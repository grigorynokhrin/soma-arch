from __future__ import annotations

from pathlib import Path
from typing import Any

ALLOWED_METADATA_KEYS = {"title", "artist", "date", "genre", "language", "description", "publisher"}


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

    args += ["-c", "copy", "-map_chapters", "0"]
    for key, value in metadata.items():
        if key in ALLOWED_METADATA_KEYS and value.strip():
            args += ["-metadata", f"{key}={value.strip()}"]

    for out_audio_idx, source_idx in enumerate(audio_streams):
        disposition = "default" if source_idx == default_audio_stream else "0"
        args += [f"-disposition:a:{out_audio_idx}", disposition]

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


def build_convert_args(input_path: Path, output_path: Path, profile: dict[str, Any], probe: dict[str, Any]) -> list[str]:
    video = profile["video"]
    audio = profile["audio"]
    args = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-map",
        "0:s?",
        "-map_chapters",
        "0",
        "-map_metadata",
        "0",
        "-vf",
        video_filter(profile, probe),
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
        "-c:s",
        "copy",
    ]
    if video.get("fourcc"):
        args += ["-vtag", video["fourcc"]]
    if profile["container"] == "vob":
        args += ["-f", "vob"]
    args.append(str(output_path))
    return args
