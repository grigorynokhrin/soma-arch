from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import os
import shutil
import subprocess
import threading
from typing import Any
import uuid

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from command_builder import (
    ALLOWED_METADATA_KEYS,
    build_runtime_convert_plan,
    build_mp4_player_metadata_command,
    build_remux_args,
    decode_process_bytes,
    ensure_clear_target,
    metadata_postprocess_warning,
    remux_status_for_warnings,
    safe_filename_component,
    safe_output_filename,
    subtitle_remux_action,
)

ROOT_PATH = os.getenv("FFMPEG_ROOT_PATH", "/ffmpeg")
SERVICE_NAME = os.getenv("FFMPEG_SERVICE_NAME", "ffmpeg")
SERVICE_TITLE = os.getenv("FFMPEG_SERVICE_TITLE", "FFmpeg")
TEMPLATE_ROOT_PATH = ROOT_PATH.rstrip("/")
DATA_DIR = Path(os.getenv("FFMPEG_DATA_DIR", "/data"))
CURRENT_DIR = DATA_DIR / "current"
INPUT_DIR = CURRENT_DIR / "input"
TMP_DIR = CURRENT_DIR / "tmp"
OUTPUT_DIR = CURRENT_DIR / "output"
PROFILES_PATH = Path(os.getenv("FFMPEG_PROFILES_PATH", "/app/profiles.json"))

ALLOWED_PROFILE_IDS: set[str] = set()
ACTIVE_JOB_LOCK = threading.Lock()

app = FastAPI(root_path=ROOT_PATH)
templates = Jinja2Templates(directory="templates")
templates.env.globals["root_path"] = TEMPLATE_ROOT_PATH


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_profiles() -> list[dict[str, Any]]:
    profiles = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
    if not isinstance(profiles, list):
        raise RuntimeError("profiles.json must contain a list")
    return profiles


PROFILES = load_profiles()
PROFILES_BY_ID = {item["id"]: item for item in PROFILES}
ALLOWED_PROFILE_IDS = set(PROFILES_BY_ID)


def ensure_data_dirs() -> None:
    for path in [DATA_DIR, CURRENT_DIR, INPUT_DIR, TMP_DIR, OUTPUT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def clear_current_job() -> None:
    ensure_clear_target(DATA_DIR, CURRENT_DIR)
    if CURRENT_DIR.exists():
        shutil.rmtree(CURRENT_DIR)
    ensure_data_dirs()


def safe_name(filename: str) -> str:
    return safe_filename_component(filename, "input")


def safe_stem(value: str, default: str = "output") -> str:
    return Path(safe_name(value or default)).stem.strip() or default


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def job_path() -> Path:
    return CURRENT_DIR / "job.json"


def status_path() -> Path:
    return CURRENT_DIR / "status.json"


def probe_path() -> Path:
    return CURRENT_DIR / "probe.json"


def log_path() -> Path:
    return CURRENT_DIR / "job.log"


def append_log(message: str) -> None:
    ensure_data_dirs()
    with open(log_path(), "a", encoding="utf-8") as f:
        f.write(f"[{now_iso()}] {message}\n")


def save_job(job: dict[str, Any]) -> None:
    job["updated_at"] = now_iso()
    write_json(job_path(), job)
    write_json(status_path(), public_status(job))


def public_status(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1",
        "service": SERVICE_NAME,
        "job_id": job.get("job_id"),
        "mode": job.get("mode"),
        "status": job.get("status"),
        "stage": job.get("stage"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
        "started_at": job.get("started_at"),
        "finished_at": job.get("finished_at"),
        "error": job.get("error"),
        "artifacts": job.get("artifacts", []),
        "input_files": job.get("input_files", []),
        "profile_id": job.get("profile_id"),
        "warnings": job.get("warnings", []),
        "ffmpeg_commands": job.get("ffmpeg_commands", []),
    }


def current_job() -> dict[str, Any]:
    return read_json(job_path())


def stderr_excerpt(text: str, limit: int = 2400) -> str:
    text = (text or "").strip()
    return text[-limit:] if len(text) > limit else text


def run_args(args: list[str]) -> subprocess.CompletedProcess[str]:
    append_log("run: " + " ".join(args))
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return subprocess.CompletedProcess(
        args=result.args,
        returncode=result.returncode,
        stdout=decode_process_bytes(result.stdout),
        stderr=decode_process_bytes(result.stderr),
    )


def run_checked(args: list[str]) -> subprocess.CompletedProcess[str]:
    result = run_args(args)
    if result.returncode != 0:
        raise RuntimeError(stderr_excerpt(result.stderr))
    return result


def ffprobe_json(path: Path) -> dict[str, Any]:
    result = run_checked(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            "-show_chapters",
            str(path),
        ]
    )
    return json.loads(result.stdout or "{}")


def stream_language(stream: dict[str, Any]) -> str | None:
    tags = stream.get("tags") or {}
    return tags.get("language")


def stream_title(stream: dict[str, Any]) -> str | None:
    tags = stream.get("tags") or {}
    return tags.get("title") or tags.get("handler_name") or tags.get("name")


def normalized_stream(stream: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": stream.get("index"),
        "codec_type": stream.get("codec_type"),
        "codec_name": stream.get("codec_name"),
        "language": stream_language(stream),
        "title": stream_title(stream),
        "duration": stream.get("duration"),
        "bitrate": stream.get("bit_rate"),
        "channels": stream.get("channels"),
        "width": stream.get("width"),
        "height": stream.get("height"),
        "avg_frame_rate": stream.get("avg_frame_rate"),
        "display_aspect_ratio": stream.get("display_aspect_ratio"),
        "disposition": stream.get("disposition") or {},
    }


def normalize_probe(raw: dict[str, Any]) -> dict[str, Any]:
    streams = raw.get("streams") or []
    normalized = []
    for stream in streams:
        item = normalized_stream(stream)
        if item["codec_type"] == "subtitle":
            item["remux_action"] = subtitle_remux_action(item)
        normalized.append(item)
    return {
        "format": raw.get("format") or {},
        "streams": normalized,
        "video_streams": [item for item in normalized if item["codec_type"] == "video"],
        "audio_streams": [item for item in normalized if item["codec_type"] == "audio"],
        "subtitle_streams": [item for item in normalized if item["codec_type"] == "subtitle"],
        "chapters": raw.get("chapters") or [],
    }


def selected_ints(values: list[str] | None) -> list[int]:
    out = []
    for value in values or []:
        try:
            out.append(int(value))
        except ValueError:
            continue
    return out


def render_index(request: Request, error: str | None = None) -> HTMLResponse:
    job = current_job()
    show_probe = job.get("mode") == "remux" and job.get("status") == "probed"
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "title": SERVICE_TITLE,
            "profiles": PROFILES,
            "job": job,
            "probe": read_json(probe_path()) if show_probe else {},
            "show_probe": show_probe,
            "error": error,
            "metadata_keys": sorted(ALLOWED_METADATA_KEYS),
        },
    )


@app.get("/healthz", response_class=PlainTextResponse)
async def healthz() -> str:
    return "ok"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    ensure_data_dirs()
    return render_index(request)


@app.post("/job/clear")
async def clear_job():
    with ACTIVE_JOB_LOCK:
        clear_current_job()
    return RedirectResponse(url=f"{TEMPLATE_ROOT_PATH}/", status_code=303)


@app.post("/remux/probe", response_class=HTMLResponse)
async def remux_probe(request: Request, video_file: UploadFile = File(...)):
    with ACTIVE_JOB_LOCK:
        clear_current_job()
        original = safe_name(video_file.filename)
        input_path = INPUT_DIR / original
        with open(input_path, "wb") as f:
            shutil.copyfileobj(video_file.file, f)

        job = {
            "job_id": uuid.uuid4().hex[:12],
            "mode": "remux",
            "status": "running",
            "stage": "probing",
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "started_at": now_iso(),
            "finished_at": None,
            "error": None,
            "input_files": [{"name": original, "path": str(input_path)}],
            "artifacts": [],
            "warnings": [],
        }
        save_job(job)

        try:
            append_log(f"uploaded for probe: {original}")
            probe = normalize_probe(ffprobe_json(input_path))
            write_json(probe_path(), probe)
            job.update({"status": "probed", "stage": "probed", "probe_path": str(probe_path())})
            save_job(job)
        except Exception as e:
            job.update({"status": "failed", "stage": "failed", "finished_at": now_iso(), "error": str(e)})
            save_job(job)

    return render_index(request)


@app.post("/remux/run")
async def remux_run(
    output_name: str = Form(default="remuxed"),
    audio_streams: list[str] | None = Form(default=None),
    default_audio_stream: str | None = Form(default=None),
    subtitle_streams: list[str] | None = Form(default=None),
    title: str = Form(default=""),
    artist: str = Form(default=""),
    date: str = Form(default=""),
    genre: str = Form(default=""),
    description: str = Form(default=""),
):
    with ACTIVE_JOB_LOCK:
        job = current_job()
        if not job or job.get("mode") != "remux":
            return RedirectResponse(url=f"{TEMPLATE_ROOT_PATH}/", status_code=303)
        probe = read_json(probe_path())
        input_files = job.get("input_files") or []
        if not input_files:
            job.update({"status": "failed", "stage": "failed", "finished_at": now_iso(), "error": "No probed input file"})
            save_job(job)
            return RedirectResponse(url=f"{TEMPLATE_ROOT_PATH}/job/result", status_code=303)

        input_path = Path(input_files[0]["path"])
        output_path = OUTPUT_DIR / safe_output_filename(output_name, "remuxed", "mp4")
        default_audio = int(default_audio_stream) if default_audio_stream not in (None, "") else None
        metadata = {
            "title": title,
            "artist": artist,
            "date": date,
            "genre": genre,
            "description": description,
        }

        job.update({"status": "running", "stage": "remuxing", "started_at": job.get("started_at") or now_iso(), "error": None})
        save_job(job)

        try:
            args = build_remux_args(
                input_path=input_path,
                output_path=output_path,
                probe=probe,
                audio_streams=selected_ints(audio_streams),
                default_audio_stream=default_audio,
                subtitle_streams=selected_ints(subtitle_streams),
                metadata=metadata,
            )
            run_checked(args)
            artifact = {"name": output_path.name, "path": str(output_path), "kind": "mp4", "size_bytes": output_path.stat().st_size}
            metadata_plan = build_mp4_player_metadata_command(output_path, metadata, OUTPUT_DIR)
            warnings = list(job.get("warnings") or [])
            for warning in metadata_plan["warnings"]:
                warnings.append(warning)
                append_log("warning: " + warning)
            if len(metadata_plan["args"]) > 3:
                job.update({"stage": "writing_metadata", "warnings": warnings})
                save_job(job)
                try:
                    run_checked(metadata_plan["args"])
                except Exception as e:
                    warning = metadata_postprocess_warning(str(e))
                    warnings.append(warning)
                    append_log("warning: " + warning)
            status = remux_status_for_warnings(warnings)
            job.update({"status": status, "stage": status, "finished_at": now_iso(), "artifacts": [artifact], "warnings": warnings, "error": None})
        except Exception as e:
            job.update({"status": "failed", "stage": "failed", "finished_at": now_iso(), "error": str(e)})
        save_job(job)
    return RedirectResponse(url=f"{TEMPLATE_ROOT_PATH}/job/result", status_code=303)


@app.post("/convert/run")
async def convert_run(profile_id: str = Form(...), video_files: list[UploadFile] = File(...)):
    if profile_id not in ALLOWED_PROFILE_IDS:
        raise RuntimeError("Unknown profile")

    with ACTIVE_JOB_LOCK:
        clear_current_job()
        profile = PROFILES_BY_ID[profile_id]
        job = {
            "job_id": uuid.uuid4().hex[:12],
            "mode": "convert",
            "status": "running",
            "stage": "converting",
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "started_at": now_iso(),
            "finished_at": None,
            "error": None,
            "profile_id": profile_id,
            "input_files": [],
            "artifacts": [],
            "warnings": [],
            "ffmpeg_commands": [],
        }
        save_job(job)

        try:
            uploads = [item for item in video_files if item and item.filename]
            if not uploads:
                raise RuntimeError("No input files selected")
            artifacts = []
            input_items = []
            warnings = []
            ffmpeg_commands = []
            for idx, upload in enumerate(uploads, 1):
                original = safe_name(upload.filename)
                input_path = INPUT_DIR / f"{idx:03d}-{original}"
                with open(input_path, "wb") as f:
                    shutil.copyfileobj(upload.file, f)
                append_log(f"uploaded convert input {idx}/{len(uploads)}: {original}")

                probe = normalize_probe(ffprobe_json(input_path))
                plan = build_runtime_convert_plan(original, input_path, OUTPUT_DIR, profile, probe)
                output_path = plan["output_path"]
                command_record = {"input": original, "profile_id": profile_id, "args": plan["args"], "command": plan["command"]}
                ffmpeg_commands.append(command_record)
                append_log(f"convert command {idx}/{len(uploads)}: {plan['command']}")
                job.update({"ffmpeg_commands": ffmpeg_commands, "stage": f"running {idx}/{len(uploads)}"})
                save_job(job)

                for warning in plan["warnings"]:
                    warnings.append(f"{original}: {warning}")
                    append_log("warning: " + warnings[-1])
                run_checked(plan["args"])

                input_items.append({"index": idx, "name": original, "path": str(input_path), "status": "done"})
                artifacts.append(
                    {
                        "name": output_path.name,
                        "path": str(output_path),
                        "kind": profile["extension"],
                        "size_bytes": output_path.stat().st_size,
                    }
                )
                job.update({"input_files": input_items, "artifacts": artifacts, "warnings": warnings, "ffmpeg_commands": ffmpeg_commands, "stage": f"converted {idx}/{len(uploads)}"})
                save_job(job)

            job.update({"status": "done", "stage": "done", "finished_at": now_iso(), "error": None})
        except Exception as e:
            job.update({"status": "failed", "stage": "failed", "finished_at": now_iso(), "error": str(e)})
        save_job(job)
    return RedirectResponse(url=f"{TEMPLATE_ROOT_PATH}/job/result", status_code=303)


@app.get("/job/status.json")
async def job_status_json():
    return public_status(current_job())


@app.get("/job/result", response_class=HTMLResponse)
async def job_result(request: Request):
    return templates.TemplateResponse(request, "job_result.html", {"title": "FFmpeg result", "job": current_job()})


@app.get("/download/{artifact_name}")
async def download(artifact_name: str):
    name = safe_name(artifact_name)
    job = current_job()
    allowed_names = {item.get("name") for item in job.get("artifacts", [])}
    path = (OUTPUT_DIR / name).resolve()
    output_root = OUTPUT_DIR.resolve()
    if name not in allowed_names or output_root not in path.parents or not path.exists() or not path.is_file():
        return PlainTextResponse("Not found", status_code=404)
    return FileResponse(path, filename=name)
