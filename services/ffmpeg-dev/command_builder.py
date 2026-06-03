from __future__ import annotations

from pathlib import Path
import re
from typing import Any

ALLOWED_METADATA_KEYS = {"title", "artist", "date", "genre", "description"}
BASIC_MP4_METADATA_KEYS = {"title", "artist", "date", "genre", "description"}
MP4_ENCODER_DELETE_TAGS = ["QuickTime:Encoder", "ItemList:Encoder", "UserData:Encoder", "Keys:Encoder"]
EXIFTOOL_LARGE_FILE_ARGS = ["-api", "LargeFileSupport=1"]
MP4_PLAYER_METADATA_TAGS = {
    "title": ["ItemList:Title", "UserData:Title", "Keys:Title", "Keys:DisplayName"],
    "artist": ["ItemList:Artist", "UserData:Artist", "Keys:Artist", "UserData:Author", "Keys:Author"],
    "date": ["ItemList:ContentCreateDate"],
    "genre": ["ItemList:Genre", "UserData:Genre", "Keys:Genre"],
    "description": [
        "ItemList:Description",
        "ItemList:LongDescription",
        "UserData:Description",
        "Keys:Description",
    ],
}
MP4_SUBTITLE_COPY_CODECS = {"mov_text"}
MP4_SUBTITLE_TO_MOV_TEXT_CODECS = {"subrip", "srt", "ass", "ssa", "webvtt"}
TEXT_SUBTITLE_CODECS = MP4_SUBTITLE_TO_MOV_TEXT_CODECS | MP4_SUBTITLE_COPY_CODECS
IMAGE_SUBTITLE_CODECS = {"dvd_subtitle", "hdmv_pgs_subtitle", "pgs", "dvdsub", "vobsub"}
IMAGE_SUBTITLE_ERROR = "Image subtitles cannot be converted to MP4 text subtitles without OCR; deselect this subtitle stream."


def decode_process_bytes(data: bytes | str | None) -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    return data.decode("utf-8", errors="replace")


def safe_filename_component(filename: str, default: str = "input") -> str:
    name = Path(filename or "").name.strip()
    name = re.sub(r"[/\\\x00-\x1f\x7f]+", " ", name)
    while ".." in name:
        name = name.replace("..", ".")
    name = re.sub(r"\s+", " ", name).strip()
    return name or default


def safe_output_filename(value: str, default: str, extension: str) -> str:
    ext = "." + extension.lstrip(".")
    name = safe_filename_component(value or default, default)
    stem = Path(name).stem if Path(name).suffix else name
    stem = stem.strip()
    if not stem or stem in {".", ".."}:
        stem = default
    return f"{stem}{ext}"


def ensure_clear_target(data_dir: Path, current_dir: Path) -> None:
    data = data_dir.resolve()
    current = current_dir.resolve()
    if current == data or data not in current.parents:
        raise RuntimeError("Refusing to clear a path outside the FFmpeg data directory")


def ensure_output_artifact_path(output_root: Path, artifact_path: Path) -> None:
    root = output_root.resolve()
    artifact = artifact_path.resolve()
    if root not in artifact.parents or artifact.suffix.lower() != ".mp4":
        raise RuntimeError("Refusing to post-process a path outside the FFmpeg output directory")


def clean_metadata(metadata: dict[str, str]) -> dict[str, str]:
    cleaned = {}
    for key, value in metadata.items():
        if key in ALLOWED_METADATA_KEYS and value and value.strip():
            cleaned[key] = value.strip()
    return cleaned


def normalize_mp4_metadata_value(key: str, value: str) -> str:
    value = value.strip()
    if key == "date":
        if re.fullmatch(r"\d{4}", value):
            return f"{value}:01:01 00:00:00"
        match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", value)
        if match:
            return f"{match.group(1)}:{match.group(2)}:{match.group(3)} 00:00:00"
    return value


def metadata_postprocess_warning(error: str) -> str:
    error = (error or "").strip()
    if error:
        return f"MP4 metadata post-processing failed; remuxed MP4 was preserved without complete metadata: {error}"
    return "MP4 metadata post-processing failed; remuxed MP4 was preserved without complete metadata."


def remux_status_for_warnings(warnings: list[str]) -> str:
    return "done_with_warnings" if warnings else "done"


def build_mp4_player_metadata_command(output_path: Path, metadata: dict[str, str], output_root: Path | None = None) -> dict[str, Any]:
    if output_root is not None:
        ensure_output_artifact_path(output_root, output_path)

    cleaned = clean_metadata(metadata)
    args = ["exiftool", *EXIFTOOL_LARGE_FILE_ARGS, "-overwrite_original"]
    for tag in MP4_ENCODER_DELETE_TAGS:
        args.append(f"-{tag}=")
    warnings: list[str] = []

    for key, value in cleaned.items():
        tags = MP4_PLAYER_METADATA_TAGS.get(key, [])
        if not tags:
            warnings.append(f"Metadata field {key} has no safe player-compatible ExifTool aliases in v1.")
            continue
        normalized_value = normalize_mp4_metadata_value(key, value)
        for tag in tags:
            args.append(f"-{tag}={normalized_value}")

    args.append(str(output_path))
    return {"args": args, "warnings": warnings}


def rational_to_float(value: str | None) -> float | None:
    if not value or value == "0/0":
        return None
    if "/" in value:
        a, b = value.split("/", 1)
        try:
            denom = float(b)
            return float(a) / denom if denom else None
        except ValueError:
            return None
    try:
        return float(value)
    except ValueError:
        return None


def first_video_stream(probe: dict[str, Any]) -> int:
    videos = probe.get("video_streams") or []
    if not videos:
        raise RuntimeError("No video stream found")
    return int(videos[0]["index"])


def stream_by_index(probe: dict[str, Any], group: str, index: int) -> dict[str, Any]:
    for stream in probe.get(group) or []:
        if int(stream.get("index", -1)) == index:
            return stream
    return {}


def add_selected_stream_metadata(args: list[str], stream_spec: str, stream: dict[str, Any]) -> None:
    language = (stream.get("language") or "").strip()
    title = (stream.get("title") or "").strip()

    if language:
        args += [f"-metadata:s:{stream_spec}", f"language={language}"]
    if title:
        args += [f"-metadata:s:{stream_spec}", f"title={title}"]
        args += [f"-metadata:s:{stream_spec}", f"handler_name={title}"]


def subtitle_codec(stream: dict[str, Any]) -> str:
    return str(stream.get("codec_name") or "").strip().lower()


def subtitle_mp4_codec(stream: dict[str, Any]) -> str:
    codec = subtitle_codec(stream)
    if codec in MP4_SUBTITLE_COPY_CODECS:
        return "copy"
    if codec in MP4_SUBTITLE_TO_MOV_TEXT_CODECS:
        return "mov_text"
    if codec in IMAGE_SUBTITLE_CODECS:
        raise RuntimeError(IMAGE_SUBTITLE_ERROR)
    raise RuntimeError(f"Subtitle codec {codec or 'unknown'} is not supported for MP4 remux; deselect this subtitle stream.")


def subtitle_remux_action(stream: dict[str, Any]) -> str:
    try:
        codec = subtitle_mp4_codec(stream)
    except RuntimeError as e:
        return str(e)
    if codec == "copy":
        return "copy"
    return f"convert to {codec}"


def quote_filter_path(path: Path) -> str:
    value = str(path)
    value = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{value}'"


def selected_subtitle_for_burn(probe: dict[str, Any]) -> tuple[int, dict[str, Any]] | None:
    subtitles = probe.get("subtitle_streams") or []
    if not subtitles:
        return None
    for order, stream in enumerate(subtitles):
        disposition = stream.get("disposition") or {}
        if disposition.get("default"):
            return order, stream
    return 0, subtitles[0]


def subtitle_warning(stream: dict[str, Any], profile_id: str, action: str) -> str:
    index = stream.get("index")
    codec = subtitle_codec(stream) or "unknown"
    if action == "burn":
        return f"Subtitle stream #{index} codec {codec} was burned into video for profile {profile_id}."
    return f"Subtitle stream #{index} codec {codec} was dropped; bitmap/OCR subtitle conversion is not supported."


def convert_subtitle_plan(
    *,
    input_path: Path,
    profile: dict[str, Any],
    probe: dict[str, Any],
) -> dict[str, Any]:
    profile_id = str(profile["id"])
    container = str(profile["container"])
    selected = selected_subtitle_for_burn(probe)
    if selected is None:
        return {"maps": [], "video_filter_suffix": "", "warnings": []}

    subtitle_order, stream = selected
    codec = subtitle_codec(stream)
    if container == "avi" and codec == "xsub":
        return {"maps": ["-map", f"0:{stream['index']}"], "video_filter_suffix": "", "warnings": []}
    if container == "vob" and codec == "dvd_subtitle":
        return {"maps": ["-map", f"0:{stream['index']}"], "video_filter_suffix": "", "warnings": []}
    if codec in TEXT_SUBTITLE_CODECS:
        suffix = f",subtitles=filename={quote_filter_path(input_path)}:si={subtitle_order}"
        return {"maps": [], "video_filter_suffix": suffix, "warnings": [subtitle_warning(stream, profile_id, "burn")]}
    return {"maps": [], "video_filter_suffix": "", "warnings": [subtitle_warning(stream, profile_id, "drop")]}


def build_remux_args(
    *,
    input_path: Path,
    output_path: Path,
    probe: dict[str, Any],
    audio_streams: list[int],
    default_audio_stream: int | None,
    subtitle_streams: list[int],
    metadata: dict[str, str],
) -> list[str]:
    if default_audio_stream is not None and default_audio_stream not in audio_streams:
        raise RuntimeError("Default audio stream must be one of the kept audio streams")

    args = ["ffmpeg", "-y", "-i", str(input_path), "-map", f"0:{first_video_stream(probe)}"]
    for idx in audio_streams:
        args += ["-map", f"0:{idx}"]
    for idx in subtitle_streams:
        args += ["-map", f"0:{idx}"]

    args += ["-c", "copy", "-map_chapters", "0", "-map_metadata", "-1"]
    for key, value in clean_metadata(metadata).items():
        if key in BASIC_MP4_METADATA_KEYS:
            args += ["-metadata", f"{key}={value}"]

    for out_audio_idx, source_idx in enumerate(audio_streams):
        add_selected_stream_metadata(args, f"a:{out_audio_idx}", stream_by_index(probe, "audio_streams", source_idx))
        disposition = "default" if source_idx == default_audio_stream else "0"
        args += [f"-disposition:a:{out_audio_idx}", disposition]

    for out_subtitle_idx, source_idx in enumerate(subtitle_streams):
        stream = stream_by_index(probe, "subtitle_streams", source_idx)
        codec = subtitle_mp4_codec(stream)
        if codec != "copy":
            args += [f"-c:s:{out_subtitle_idx}", codec]
        add_selected_stream_metadata(args, f"s:{out_subtitle_idx}", stream)

    args.append(str(output_path))
    return args


def source_video_info(probe: dict[str, Any]) -> dict[str, Any]:
    stream = (probe.get("video_streams") or [{}])[0]
    width = int(stream.get("width") or 0)
    height = int(stream.get("height") or 0)
    fps = rational_to_float(stream.get("avg_frame_rate")) or 25.0
    dar = stream.get("display_aspect_ratio")
    if dar and ":" in dar:
        a, b = dar.split(":", 1)
        try:
            aspect = float(a) / float(b)
        except ValueError:
            aspect = width / height if height else 16 / 9
    else:
        aspect = width / height if height else 16 / 9
    return {"width": width, "height": height, "fps": fps, "aspect": aspect}


def aspect_value(value: str) -> float:
    a, b = value.split(":", 1)
    return float(a) / float(b)


def video_filter(profile: dict[str, Any], probe: dict[str, Any]) -> str:
    video = profile["video"]
    target_w = int(video["width"])
    target_h = int(video["height"])
    target_aspect = aspect_value(video["display_aspect"])
    source = source_video_info(probe)
    crop_wide = source["aspect"] > target_aspect

    if video["crop_policy"] == "crop_sides_to_aspect" or crop_wide:
        crop = f"crop='min(iw,ih*{target_aspect})':ih:(iw-ow)/2:0"
        return f"{crop},scale={target_w}:{target_h},setsar=1"

    scale = f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease"
    pad = f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2"
    return f"{scale},{pad},setsar=1"


def output_fps(profile: dict[str, Any], probe: dict[str, Any]) -> float:
    video = profile["video"]
    if video["fps_mode"] == "cfr_fixed":
        return float(video["fps"])
    source_fps = source_video_info(probe)["fps"]
    return min(source_fps, float(video.get("max_fps") or source_fps))


def build_convert_plan(input_path: Path, output_path: Path, profile: dict[str, Any], probe: dict[str, Any]) -> dict[str, Any]:
    video = profile["video"]
    audio = profile["audio"]
    subtitle_plan = convert_subtitle_plan(input_path=input_path, profile=profile, probe=probe)
    vf = video_filter(profile, probe) + subtitle_plan["video_filter_suffix"]
    args = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-map_chapters",
        "0",
        "-map_metadata",
        "0",
        "-vf",
        vf,
        "-r",
        str(output_fps(profile, probe)),
        "-c:v",
        video["codec"],
        "-b:v",
        f"{video['avg_bitrate_kbps']}k",
        "-maxrate",
        f"{video['max_bitrate_kbps']}k",
        "-bufsize",
        f"{video['max_bitrate_kbps'] * 2}k",
        "-aspect",
        video["display_aspect"],
        "-c:a",
        audio["codec"],
        "-ac",
        str(audio["channels"]),
        "-b:a",
        f"{audio['bitrate_kbps']}k",
    ]
    args[8:8] = subtitle_plan["maps"]
    if subtitle_plan["maps"]:
        args += ["-c:s", "copy"]
    if video.get("fourcc"):
        args += ["-vtag", video["fourcc"]]
    if profile["container"] == "vob":
        args += ["-f", "vob"]
    args.append(str(output_path))
    return {"args": args, "warnings": subtitle_plan["warnings"]}


def build_convert_args(input_path: Path, output_path: Path, profile: dict[str, Any], probe: dict[str, Any]) -> list[str]:
    return build_convert_plan(input_path, output_path, profile, probe)["args"]
