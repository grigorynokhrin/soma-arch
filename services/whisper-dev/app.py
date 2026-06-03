from datetime import datetime
from pathlib import Path
import uuid
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from typing import List, Tuple

from faster_whisper import WhisperModel
from fastapi import BackgroundTasks, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

ROOT_PATH = os.getenv("WHISPER_ROOT_PATH", "/whisper-dev")
TEMPLATE_ROOT_PATH = ROOT_PATH.rstrip("/")

OUTPUT_DIR = Path(os.getenv("WHISPER_OUTPUT_DIR", "/app/outputs"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

JOBS_DIR = Path(os.getenv("WHISPER_JOBS_DIR", "/app/data/jobs"))
JOBS_DIR.mkdir(parents=True, exist_ok=True)

CONTEXTS_PATH = Path(os.getenv("WHISPER_CONTEXTS_PATH", "/app/contexts.json"))
MAX_CONTEXT_CHARS = int(os.getenv("WHISPER_MAX_CONTEXT_CHARS", "1200"))
RETENTION_MAX_JOBS = int(os.getenv("WHISPER_RETENTION_MAX_JOBS", "5"))

app = FastAPI(root_path=ROOT_PATH)
templates = Jinja2Templates(directory="templates")
templates.env.globals["root_path"] = TEMPLATE_ROOT_PATH

_model_cache: dict[tuple[str, str], tuple[WhisperModel, str]] = {}

LANG_OPTIONS = ["auto", "ru", "en"]
def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def job_dir(job_id: str) -> Path:
    return JOBS_DIR / job_id


def job_meta_path(job_id: str) -> Path:
    return job_dir(job_id) / "job.json"


def job_log_path(job_id: str) -> Path:
    return job_dir(job_id) / "job.log"


def ensure_job_dir(job_id: str) -> Path:
    path = job_dir(job_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_job(
    *,
    filename: str,
    language: str,
    model_name: str,
    context_preset: str,
    transcription_context: str,
    compute_type: str,
    chunk_min: int,
    overlap_sec: int,
    beam: int,
    vad: bool,
    keep_tmp: bool,
) -> dict:
    job_id = uuid.uuid4().hex[:12]
    ensure_job_dir(job_id)

    data = {
        "job_id": job_id,
        "filename": filename,
        "status": "queued",
        "context_preset": context_preset,
        "transcription_context": transcription_context,
        "stage": "uploaded",
        "progress_current": 0,
        "progress_total": 0,
        "started_at": now_iso(),
        "finished_at": None,
        "error": None,
        "language": language,
        "model_name": model_name,
        "compute_type": compute_type,
        "chunk_min": chunk_min,
        "overlap_sec": overlap_sec,
        "beam": beam,
        "vad": vad,
        "keep_tmp": keep_tmp,
        "used_compute": None,
        "duration_min": None,
        "chunks_count": None,
        "result_text": None,
        "txt_file": None,
        "srt_file": None,
        "source_path": None,
        "wav_path": None,
        "jsonl_path": None,
        "chunk_files": [],
    }
    save_job(data)
    append_job_log(job_id, f"job created for file={filename}")
    return data


def load_job(job_id: str) -> dict:
    path = job_meta_path(job_id)
    if not path.exists():
        raise FileNotFoundError(f"Job not found: {job_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_job(data: dict):
    path = job_meta_path(data["job_id"])
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def update_job(job_id: str, **fields) -> dict:
    data = load_job(job_id)
    data.update(fields)
    save_job(data)
    return data


def append_job_log(job_id: str, message: str):
    with open(job_log_path(job_id), "a", encoding="utf-8") as f:
        f.write(f"[{now_iso()}] {message}\n")

def load_context_presets() -> list[dict]:
    if not CONTEXTS_PATH.exists():
        return [{"id": "none", "label": "Без контекста", "text": ""}]
    try:
        data = json.loads(CONTEXTS_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list) and data:
            return data
    except Exception:
        pass
    return [{"id": "none", "label": "Без контекста", "text": ""}]


def get_context_text(context_preset: str, context_text: str) -> str:
    manual = (context_text or "").strip()
    if manual:
        return manual

    for item in load_context_presets():
        if item.get("id") == context_preset:
            return (item.get("text") or "").strip()

    return ""

def trim_context_text(text: str, max_chars: int = MAX_CONTEXT_CHARS) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[-max_chars:].strip()

def run(cmd: List[str]) -> str:
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", "ignore"))
    return r.stdout.decode("utf-8", "ignore")


def ffprobe_duration(path: str) -> float:
    out = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ]
    ).strip()
    try:
        return float(out)
    except Exception:
        return 0.0


def transcode_to_pcm16_mono_16k(src: str, dst: str):
    run(["ffmpeg", "-y", "-i", src, "-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le", dst])


def split_wav_with_overlap(src_wav: str, segment_sec: int, overlap_sec: int, workdir: str) -> List[Tuple[str, float]]:
    total_dur = ffprobe_duration(src_wav)
    if total_dur <= 0:
        return []

    if segment_sec <= 0:
        raise ValueError("segment_sec должен быть > 0")

    if overlap_sec < 0:
        raise ValueError("overlap_sec должен быть >= 0")

    if overlap_sec >= segment_sec:
        raise ValueError("overlap_sec должен быть меньше длины чанка")

    step_sec = segment_sec - overlap_sec
    chunks: List[Tuple[str, float]] = []

    start = 0.0
    idx = 1

    while start < total_dur:
        out_path = os.path.join(workdir, f"chunk_{idx:03d}.wav")
        run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(start),
                "-i",
                src_wav,
                "-t",
                str(segment_sec),
                "-acodec",
                "copy",
                out_path,
            ]
        )

        chunk_dur = ffprobe_duration(out_path)
        if chunk_dur <= 0.05:
            break

        chunks.append((out_path, start))

        if start + chunk_dur >= total_dur:
            break

        start += step_sec
        idx += 1

    return chunks


def ts_srt(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def segments_to_txt_and_srt(segments, offset: float = 0.0) -> Tuple[str, List[Tuple[float, float, str]]]:
    txt = []
    srt = []
    for seg in segments:
        txt.append(seg.text)
        srt.append((seg.start + offset, seg.end + offset, seg.text))
    return "".join(txt), srt


def merge_srt(entries: List[Tuple[float, float, str]]) -> str:
    lines = []
    for i, (s, e, txt) in enumerate(entries, 1):
        lines += [str(i), f"{ts_srt(s)} --> {ts_srt(e)}", txt.strip(), ""]
    return "\n".join(lines)


def dedupe_echo(text: str, max_repeat: int = 2) -> str:
    parts = re.split(r'(?<=[\.\!\?\…])\s+', text.strip())
    out, last, cnt = [], None, 0
    for p in parts:
        norm = re.sub(r"\s+", " ", p.strip().lower())
        if not norm:
            continue
        if norm == last:
            cnt += 1
            if cnt < max_repeat:
                out.append(p)
        else:
            last, cnt = norm, 0
            out.append(p)
    return " ".join(out).strip()





def load_model_cached(name: str, requested_compute: str) -> tuple[WhisperModel, str]:
    key = (name, requested_compute)
    if key in _model_cache:
        return _model_cache[key]

    tries = []
    last_err = None

    for ct in [requested_compute, "int8", "float32"]:
        if ct in tries:
            continue

        try:
            model = WhisperModel(
                name,
                device="auto",
                compute_type=ct,
                cpu_threads=max(2, (os.cpu_count() or 4) // 2),
                num_workers=1,
            )

            try:
                actual_device = getattr(model.model, "device", "unknown")
            except Exception:
                actual_device = "unknown"

            print(
                f"[WHISPER_MODEL] name={name} requested_compute={requested_compute} "
                f"actual_compute={ct} device={actual_device}"
            )

            _model_cache[key] = (model, ct)
            return model, ct

        except Exception as e:
            print(
                f"[WHISPER_MODEL_FAIL] name={name} requested_compute={requested_compute} "
                f"try_compute={ct} error={e}"
            )
            tries.append(ct)
            last_err = e

    raise last_err if last_err else RuntimeError("Не удалось инициализировать модель.")


def cleanup_old_jobs(max_jobs: int = RETENTION_MAX_JOBS) -> None:
    if max_jobs <= 0:
        return

    if not JOBS_DIR.exists():
        return

    job_dirs = [p for p in JOBS_DIR.iterdir() if p.is_dir()]
    if len(job_dirs) <= max_jobs:
        return

    def sort_key(path: Path):
        try:
            meta = job_meta_path(path.name)
            if meta.exists():
                data = json.loads(meta.read_text(encoding="utf-8"))
                finished_at = data.get("finished_at") or ""
                started_at = data.get("started_at") or ""
                return finished_at or started_at or datetime.fromtimestamp(path.stat().st_mtime).isoformat()
        except Exception:
            pass
        return datetime.fromtimestamp(path.stat().st_mtime).isoformat()

    job_dirs.sort(key=sort_key)
    delete_dirs = job_dirs[:-max_jobs]

    for path in delete_dirs:
        try:
            job_id = path.name
            data = load_job(job_id)
            status = data.get("status")
            if status not in {"done", "error", "deleted"}:
                continue
            shutil.rmtree(path)
            print(f"[WHISPER_RETENTION] deleted old job: {job_id}")
        except Exception as e:
            print(f"[WHISPER_RETENTION_FAIL] path={path} error={e}")


def render_page(
    request: Request,
    *,
    result_text=None,
    saved_file=None,
    language="ru",
    model_name="medium",
    compute_type="float32",
    chunk_min=5,
    overlap_sec=0,
    beam=1,
    context_preset="none",
    context_text="",
    context_presets=None,
    vad=False,
    keep_tmp=False,
    error=None,
    used_compute=None,
    duration_min=None,
    chunks_count=None,
    srt_file=None,
    txt_file=None,
):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "title": "Whisper",
            "result_text": result_text,
            "saved_file": saved_file,
            "language": language,
            "model_name": model_name,
            "compute_type": compute_type,
            "chunk_min": chunk_min,
            "overlap_sec": overlap_sec,
            "beam": beam,
            "context_preset": context_preset,
            "context_text": context_text,
            "context_presets": context_presets or load_context_presets(),
            "vad": vad,
            "keep_tmp": keep_tmp,
            "error": error,
            "used_compute": used_compute,
            "duration_min": duration_min,
            "chunks_count": chunks_count,
            "srt_file": srt_file,
            "txt_file": txt_file,
        },
    )
def run_transcription_job(job_id: str):
    job = load_job(job_id)

    safe_name = Path(job["filename"]).name
    stem = Path(safe_name).stem
    work_dir = ensure_job_dir(job_id)

    src_path = work_dir / safe_name
    wav_path = work_dir / "audio_16k.wav"
    jsonl_path = work_dir / "intermediate.jsonl"

    update_job(
        job_id,
        status="running",
        stage="uploaded",
        source_path=str(src_path),
        wav_path=str(wav_path),
        jsonl_path=str(jsonl_path),
    )
    append_job_log(job_id, "job started")

    try:
        append_job_log(job_id, "probing duration")
        dur = ffprobe_duration(str(src_path))
        update_job(job_id, duration_min=round(dur / 60, 1))

        append_job_log(job_id, "converting to wav")
        update_job(job_id, stage="converting")
        transcode_to_pcm16_mono_16k(str(src_path), str(wav_path))

        seg_sec = int(job["chunk_min"] * 60)
        overlap_sec = int(job["overlap_sec"])

        append_job_log(job_id, f"chunking: segment_sec={seg_sec}, overlap_sec={overlap_sec}")
        update_job(job_id, stage="chunking")
        chunks = split_wav_with_overlap(str(wav_path), seg_sec, overlap_sec, str(work_dir))
        if not chunks:
            raise RuntimeError("После нарезки не получено ни одного чанка.")

        update_job(
            job_id,
            chunks_count=len(chunks),
            progress_current=0,
            progress_total=len(chunks),
            chunk_files=[str(Path(ch).name) for ch, _ in chunks],
        )

        append_job_log(job_id, f"loading model: {job['model_name']} / {job['compute_type']}")
        model, used_ct = load_model_cached(job["model_name"], job["compute_type"])
        update_job(job_id, used_compute=used_ct)

        lang_param = None if job["language"] == "auto" else job["language"]
        initial_prompt = (job.get("transcription_context") or "").strip() or None

        parts_txt: List[str] = []
        parts_srt: List[Tuple[float, float, str]] = []

        update_job(job_id, stage="transcribing")

        with open(jsonl_path, "w", encoding="utf-8") as jf:
            for ci, (ch, offset) in enumerate(chunks, 1):
                append_job_log(job_id, f"transcribing chunk {ci}/{len(chunks)}: {Path(ch).name}")
                start_t = time.time()

                segments, info = model.transcribe(
                    ch,
                    language=lang_param,
                    beam_size=job["beam"],
                    initial_prompt=initial_prompt,
                    temperature=[0.0, 0.2, 0.4, 0.6],
                    compression_ratio_threshold=2.4,
                    log_prob_threshold=-1.0,
                    no_speech_threshold=0.6,
                    condition_on_previous_text=False,
                    vad_filter=job["vad"],
                    vad_parameters={"min_silence_duration_ms": 500},
                    word_timestamps=False,
                )
                segs = list(segments)

                part_txt, part_srt = segments_to_txt_and_srt(segs, offset)
                part_txt = dedupe_echo(part_txt, max_repeat=2)

                parts_txt.append(part_txt)
                parts_srt.extend(part_srt)

                chunk_txt_name = f"{stem}_chunk{ci:02d}.txt"
                chunk_txt_path = work_dir / chunk_txt_name
                chunk_txt_path.write_text(part_txt, encoding="utf-8")

                jf.write(
                    json.dumps(
                        {
                            "chunk": os.path.basename(ch),
                            "time_offset": round(offset, 3),
                            "detected_language": getattr(info, "language", None),
                            "text": part_txt,
                            "elapsed_sec": round(time.time() - start_t, 2),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

                update_job(job_id, progress_current=ci)
                append_job_log(job_id, f"chunk {ci}/{len(chunks)} done")

        append_job_log(job_id, "assembling final txt/srt")
        update_job(job_id, stage="assembling")

        file_txt_raw = "\n".join(parts_txt)
        file_txt = dedupe_echo(file_txt_raw, max_repeat=2)
        file_srt = merge_srt(parts_srt)

        txt_name = f"{job_id}-{stem}.txt"
        srt_name = f"{job_id}-{stem}.srt"

        txt_path = work_dir / txt_name
        srt_path = work_dir / srt_name

        txt_path.write_text(file_txt, encoding="utf-8")
        srt_path.write_text(file_srt, encoding="utf-8")

        update_job(
            job_id,
            status="done",
            stage="done",
            finished_at=now_iso(),
            result_text=file_txt,
            txt_file=txt_name,
            srt_file=srt_name,
        )
        append_job_log(job_id, "job done")
        cleanup_old_jobs()

    except Exception as e:
        update_job(
            job_id,
            status="error",
            stage="error",
            finished_at=now_iso(),
            error=str(e),
        )
        append_job_log(job_id, f"job error: {e}")
        cleanup_old_jobs()
        raise

@app.get("/healthz", response_class=PlainTextResponse)
async def healthz() -> str:
    return "ok"

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    presets = load_context_presets()
    default_text = get_context_text("none", "")
    return render_page(
        request,
        context_preset="none",
        context_text=default_text,
        context_presets=presets,
    )
@app.post("/submit")
async def submit(
    request: Request,
    background_tasks: BackgroundTasks,
    audio_file: UploadFile | None = File(default=None),
    language: str = Form(default="ru"),
    model_name: str = Form(default="medium"),
    compute_type: str = Form(default="float32"),
    chunk_min: int = Form(default=5),
    overlap_sec: int = Form(default=0),
    beam: int = Form(default=1),
    context_preset: str = Form(default="none"),
    context_text: str = Form(default=""),
    vad: bool = Form(default=False),
    keep_tmp: bool = Form(default=False),
):
    if not audio_file or not audio_file.filename:
        return render_page(
            request,
            language=language,
            model_name=model_name,
            compute_type=compute_type,
            chunk_min=chunk_min,
            overlap_sec=overlap_sec,
            beam=beam,
            context_preset=context_preset,
            context_text=context_text,
            context_presets=load_context_presets(),
            vad=vad,
            keep_tmp=keep_tmp,
            error="Файл не выбран.",
        )

    if overlap_sec < 0:
        return render_page(
            request,
            language=language,
            model_name=model_name,
            compute_type=compute_type,
            chunk_min=chunk_min,
            overlap_sec=overlap_sec,
            beam=beam,
            context_preset=context_preset,
            context_text=context_text,
            context_presets=load_context_presets(),
            vad=vad,
            keep_tmp=keep_tmp,
            error="Overlap не может быть отрицательным.",
        )

    seg_sec = int(chunk_min * 60)
    if overlap_sec >= seg_sec:
        return render_page(
            request,
            language=language,
            model_name=model_name,
            compute_type=compute_type,
            chunk_min=chunk_min,
            overlap_sec=overlap_sec,
            beam=beam,
            context_preset=context_preset,
            context_text=context_text,
            context_presets=load_context_presets(),
            vad=vad,
            keep_tmp=keep_tmp,
            error="Overlap должен быть меньше длины чанка.",
        )

    safe_name = Path(audio_file.filename).name

    resolved_context = trim_context_text(get_context_text(context_preset, context_text))
    
    job = create_job(
        filename=safe_name,
        language=language,
        model_name=model_name,
        compute_type=compute_type,
        chunk_min=chunk_min,
        overlap_sec=overlap_sec,
        beam=beam,
        context_preset=context_preset,
        transcription_context=resolved_context,
        vad=vad,
        keep_tmp=keep_tmp,
    )

    src_path = job_dir(job["job_id"]) / safe_name
    with open(src_path, "wb") as f:
        shutil.copyfileobj(audio_file.file, f)

    update_job(job["job_id"], source_path=str(src_path))
    append_job_log(job["job_id"], f"source uploaded: {safe_name}")

    background_tasks.add_task(run_transcription_job, job["job_id"])

    status_url = request.url_for("job_status_page", job_id=job["job_id"])
    return RedirectResponse(url=str(status_url), status_code=303)

@app.get("/jobs/{job_id}", response_class=HTMLResponse, name="job_status_page")
async def job_status_page(request: Request, job_id: str):
    try:
        job = load_job(job_id)
    except FileNotFoundError:
        return PlainTextResponse("Job not found", status_code=404)

    return templates.TemplateResponse(
        request,
        "job_status.html",
        {
            "title": "Whisper Job Status",
            "job": job,
        },
    )
@app.get("/jobs/{job_id}/status.json")
async def job_status_json(job_id: str):
    try:
        job = load_job(job_id)
    except FileNotFoundError:
        return PlainTextResponse("Job not found", status_code=404)

    return job

@app.get("/jobs/{job_id}/result", response_class=HTMLResponse, name="job_result_page")
async def job_result_page(request: Request, job_id: str):
    try:
        job = load_job(job_id)
    except FileNotFoundError:
        return PlainTextResponse("Job not found", status_code=404)

    if job.get("status") != "done":
        status_url = request.url_for("job_status_page", job_id=job_id)
        return RedirectResponse(url=str(status_url), status_code=303)

    return templates.TemplateResponse(
        request,
        "job_result.html",
        {
            "title": "Whisper Job Result",
            "job": job,
        },
    )
@app.get("/jobs/{job_id}/artifacts/{filename}", response_class=PlainTextResponse)
async def job_artifact(job_id: str, filename: str):
    try:
        job = load_job(job_id)
    except FileNotFoundError:
        return PlainTextResponse("Job not found", status_code=404)

    safe_name = Path(filename).name
    path = job_dir(job_id) / safe_name
    if not path.exists():
        return PlainTextResponse("Artifact not found", status_code=404)

    return PlainTextResponse(path.read_text(encoding="utf-8", errors="ignore"))
@app.post("/transcribe", response_class=HTMLResponse)
async def transcribe(
    request: Request,
    audio_file: UploadFile | None = File(default=None),
    language: str = Form(default="ru"),
    model_name: str = Form(default="medium"),
    compute_type: str = Form(default="float32"),
    chunk_min: int = Form(default=5),
    overlap_sec: int = Form(default=0),
    beam: int = Form(default=1),
    vad: bool = Form(default=False),
    keep_tmp: bool = Form(default=False),
):
    if not audio_file or not audio_file.filename:
        return render_page(
            request,
            language=language,
            model_name=model_name,
            compute_type=compute_type,
            chunk_min=chunk_min,
            overlap_sec=overlap_sec,
            beam=beam,
            vad=vad,
            keep_tmp=keep_tmp,
            error="Файл не выбран.",
        )

    if overlap_sec < 0:
        return render_page(
            request,
            language=language,
            model_name=model_name,
            compute_type=compute_type,
            chunk_min=chunk_min,
            overlap_sec=overlap_sec,
            beam=beam,
            vad=vad,
            keep_tmp=keep_tmp,
            error="Overlap не может быть отрицательным.",
        )

    seg_sec = int(chunk_min * 60)
    if overlap_sec >= seg_sec:
        return render_page(
            request,
            language=language,
            model_name=model_name,
            compute_type=compute_type,
            chunk_min=chunk_min,
            overlap_sec=overlap_sec,
            beam=beam,
            vad=vad,
            keep_tmp=keep_tmp,
            error="Overlap должен быть меньше длины чанка.",
        )

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_name = Path(audio_file.filename).name
    stem = Path(safe_name).stem
    tmp_root = tempfile.mkdtemp(prefix="whisper_")
    src_path = os.path.join(tmp_root, safe_name)

    with open(src_path, "wb") as f:
        shutil.copyfileobj(audio_file.file, f)

    try:
        dur = ffprobe_duration(src_path)
        wav_path = os.path.join(tmp_root, "audio_16k.wav")
        transcode_to_pcm16_mono_16k(src_path, wav_path)

        chunks = split_wav_with_overlap(wav_path, seg_sec, overlap_sec, tmp_root)
        if not chunks:
            raise RuntimeError("После нарезки не получено ни одного чанка.")

        model, used_ct = load_model_cached(model_name, compute_type)
        lang_param = None if language == "auto" else language

        jsonl_path = os.path.join(tmp_root, "intermediate.jsonl")
        parts_txt: List[str] = []
        parts_srt: List[Tuple[float, float, str]] = []

        with open(jsonl_path, "w", encoding="utf-8") as jf:
            for ci, (ch, offset) in enumerate(chunks, 1):
                start_t = time.time()

                segments, info = model.transcribe(
                    ch,
                    language=lang_param,
                    beam_size=beam,
                    temperature=[0.0, 0.2, 0.4, 0.6],
                    compression_ratio_threshold=2.4,
                    log_prob_threshold=-1.0,
                    no_speech_threshold=0.6,
                    condition_on_previous_text=False,
                    vad_filter=vad,
                    vad_parameters={"min_silence_duration_ms": 500},
                    word_timestamps=False,
                )
                segs = list(segments)

                part_txt, part_srt = segments_to_txt_and_srt(segs, offset)
                part_txt = dedupe_echo(part_txt, max_repeat=2)

                parts_txt.append(part_txt)
                parts_srt.extend(part_srt)

                jf.write(
                    json.dumps(
                        {
                            "chunk": os.path.basename(ch),
                            "time_offset": round(offset, 3),
                            "detected_language": getattr(info, "language", None),
                            "text": part_txt,
                            "elapsed_sec": round(time.time() - start_t, 2),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

                out_chunk_path = OUTPUT_DIR / f"{stem}_chunk{ci:02d}.txt"
                out_chunk_path.write_text(part_txt, encoding="utf-8")

        file_txt_raw = "\n".join(parts_txt)
        file_txt = dedupe_echo(file_txt_raw, max_repeat=2)
        file_srt = merge_srt(parts_srt)

        txt_name = f"{timestamp}-{stem}.txt"
        srt_name = f"{timestamp}-{stem}.srt"
        (OUTPUT_DIR / txt_name).write_text(file_txt, encoding="utf-8")
        (OUTPUT_DIR / srt_name).write_text(file_srt, encoding="utf-8")

        return render_page(
            request,
            result_text=file_txt,
            saved_file=safe_name,
            language=language,
            model_name=model_name,
            compute_type=compute_type,
            chunk_min=chunk_min,
            overlap_sec=overlap_sec,
            beam=beam,
            vad=vad,
            keep_tmp=keep_tmp,
            used_compute=used_ct,
            duration_min=round(dur / 60, 1),
            chunks_count=len(chunks),
            txt_file=txt_name,
            srt_file=srt_name,
        )

    except Exception as e:
        return render_page(
            request,
            saved_file=safe_name,
            language=language,
            model_name=model_name,
            compute_type=compute_type,
            chunk_min=chunk_min,
            overlap_sec=overlap_sec,
            beam=beam,
            vad=vad,
            keep_tmp=keep_tmp,
            error=f"Ошибка распознавания: {e}",
        )
    finally:
        if not keep_tmp:
            shutil.rmtree(tmp_root, ignore_errors=True)


@app.get("/outputs/{filename}", response_class=PlainTextResponse)
async def get_output(filename: str):
    path = OUTPUT_DIR / Path(filename).name
    if not path.exists():
        return PlainTextResponse("Not found", status_code=404)
    return PlainTextResponse(path.read_text(encoding="utf-8", errors="ignore"))
