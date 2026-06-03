from __future__ import annotations

from pathlib import Path
import json
import re

from command_builder import IMAGE_SUBTITLE_ERROR, build_convert_args, build_remux_args, decode_process_bytes, subtitle_remux_action

HERE = Path(__file__).resolve().parent
PROFILES_PATH = HERE / "profiles.json"


def load_profiles() -> dict[str, dict]:
    profiles = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
    return {item["id"]: item for item in profiles}


def fake_probe(avg_frame_rate: str = "24000/1001") -> dict:
    return {
        "video_streams": [
            {
                "index": 0,
                "codec_type": "video",
                "width": 1920,
                "height": 1080,
                "avg_frame_rate": avg_frame_rate,
                "display_aspect_ratio": "16:9",
            }
        ],
        "audio_streams": [
            {
                "index": 1,
                "codec_type": "audio",
                "language": "eng",
                "title": "English stream name must survive",
            },
            {
                "index": 2,
                "codec_type": "audio",
                "language": "rus",
                "title": "Russian stream name must survive",
            },
        ],
        "subtitle_streams": [
            {
                "index": 3,
                "codec_type": "subtitle",
                "codec_name": "subrip",
                "language": "eng",
                "title": "English subtitles must survive",
            }
        ],
    }


def value_after(args: list[str], key: str) -> str:
    try:
        return args[args.index(key) + 1]
    except (ValueError, IndexError) as exc:
        raise AssertionError(f"{key} missing from command: {args}") from exc


def assert_contains(args: list[str], *items: str) -> None:
    for item in items:
        assert item in args, f"{item!r} missing from command: {args}"


def assert_pair(args: list[str], key: str, value: str) -> None:
    pairs = list(zip(args, args[1:]))
    assert (key, value) in pairs, f"{key} {value} missing from command: {args}"


def assert_video_filter(args: list[str], fragment: str) -> None:
    vf = value_after(args, "-vf")
    assert fragment in vf, f"{fragment!r} missing from filter: {vf}"


def assert_convert_shape(profile: dict, *, output_name: str, checks: dict[str, str]) -> list[str]:
    args = build_convert_args(Path("input.mkv"), Path(output_name), profile, fake_probe())
    assert args[0] == "ffmpeg"
    assert args[-1] == output_name
    assert value_after(args, "-c:v") == checks["video_codec"]
    assert value_after(args, "-c:a") == checks["audio_codec"]
    assert value_after(args, "-ac") == "2"
    assert value_after(args, "-b:a") == checks["audio_bitrate"]
    assert value_after(args, "-aspect") == checks["aspect"]
    assert value_after(args, "-r") == checks["fps"]
    assert_video_filter(args, checks["scale"])
    if checks.get("fourcc"):
        assert_contains(args, "-vtag", checks["fourcc"])
    if checks.get("format"):
        assert value_after(args, "-f") == checks["format"]
    return args


def main() -> None:
    profiles = load_profiles()
    assert set(profiles) == {
        "cowon-iaudio-d2-plus",
        "lacie-ss-4x3-vob-pal",
        "lacie-ss-16x9-vob-pal",
        "lacie-ss-16x9-avi",
    }

    cowon = assert_convert_shape(
        profiles["cowon-iaudio-d2-plus"],
        output_name="movie.avi",
        checks={
            "video_codec": "mpeg4",
            "audio_codec": "mp3",
            "audio_bitrate": "128k",
            "aspect": "4:3",
            "fps": "23.976023976023978",
            "scale": "scale=320:240",
            "fourcc": "XVID",
        },
    )
    assert value_after(cowon, "-b:v") == "900k"
    assert value_after(cowon, "-maxrate") == "1300k"
    assert float(value_after(cowon, "-r")) <= 30.0

    assert_convert_shape(
        profiles["lacie-ss-4x3-vob-pal"],
        output_name="movie.vob",
        checks={
            "video_codec": "mpeg2video",
            "audio_codec": "ac3",
            "audio_bitrate": "192k",
            "aspect": "4:3",
            "fps": "25.0",
            "scale": "scale=720:576",
            "format": "vob",
        },
    )

    assert_convert_shape(
        profiles["lacie-ss-16x9-vob-pal"],
        output_name="movie.vob",
        checks={
            "video_codec": "mpeg2video",
            "audio_codec": "ac3",
            "audio_bitrate": "448k",
            "aspect": "16:9",
            "fps": "25.0",
            "scale": "scale=720:576",
            "format": "vob",
        },
    )

    assert_convert_shape(
        profiles["lacie-ss-16x9-avi"],
        output_name="movie.avi",
        checks={
            "video_codec": "mpeg4",
            "audio_codec": "ac3",
            "audio_bitrate": "448k",
            "aspect": "16:9",
            "fps": "25.0",
            "scale": "scale=1024:576",
            "fourcc": "XVID",
        },
    )

    remux = build_remux_args(
        input_path=Path("input.mkv"),
        output_path=Path("remuxed.mp4"),
        probe=fake_probe(),
        audio_streams=[1, 2],
        default_audio_stream=2,
        subtitle_streams=[3],
        metadata={"title": "Kept", "raw_args": "-filter_complex unsafe", "genre": "Live"},
    )
    assert_contains(remux, "-c", "copy", "-map_chapters", "0", "-map_metadata", "-1", "-movflags", "use_metadata_tags")
    assert_pair(remux, "-map_chapters", "0")
    assert_pair(remux, "-map_metadata", "-1")
    assert_pair(remux, "-movflags", "use_metadata_tags")
    assert ("-map_metadata", "0") not in list(zip(remux, remux[1:]))
    assert "-c:v" not in remux
    assert "-c:a" not in remux
    assert_pair(remux, "-c:s:0", "mov_text")
    assert_pair(remux, "-metadata:s:a:0", "language=eng")
    assert_pair(remux, "-metadata:s:a:0", "title=English stream name must survive")
    assert_pair(remux, "-metadata:s:a:0", "handler_name=English stream name must survive")
    assert_pair(remux, "-metadata:s:a:1", "language=rus")
    assert_pair(remux, "-metadata:s:a:1", "title=Russian stream name must survive")
    assert_pair(remux, "-metadata:s:a:1", "handler_name=Russian stream name must survive")
    assert_pair(remux, "-metadata:s:s:0", "language=eng")
    assert_pair(remux, "-metadata:s:s:0", "title=English subtitles must survive")
    assert_pair(remux, "-metadata:s:s:0", "handler_name=English subtitles must survive")
    assert "-filter_complex unsafe" not in " ".join(remux)
    assert "raw_args=-filter_complex unsafe" not in remux
    assert "-metadata" in remux
    assert "title=Kept" in remux
    assert "genre=Live" in remux
    assert re.search(r"-disposition:a:1\s+default", " ".join(remux))

    mov_text_probe = fake_probe()
    mov_text_probe["subtitle_streams"][0]["codec_name"] = "mov_text"
    mov_text = build_remux_args(
        input_path=Path("input.mkv"),
        output_path=Path("remuxed.mp4"),
        probe=mov_text_probe,
        audio_streams=[1],
        default_audio_stream=1,
        subtitle_streams=[3],
        metadata={"title": "Kept"},
    )
    assert "-c:s:0" not in mov_text
    assert_pair(mov_text, "-metadata:s:s:0", "language=eng")
    assert subtitle_remux_action(mov_text_probe["subtitle_streams"][0]) == "copy"

    image_probe = fake_probe()
    image_probe["subtitle_streams"][0]["codec_name"] = "hdmv_pgs_subtitle"
    try:
        build_remux_args(
            input_path=Path("input.mkv"),
            output_path=Path("remuxed.mp4"),
            probe=image_probe,
            audio_streams=[1],
            default_audio_stream=1,
            subtitle_streams=[3],
            metadata={"title": "Kept"},
        )
        raise AssertionError("image subtitle should have failed before ffmpeg")
    except RuntimeError as exc:
        assert str(exc) == IMAGE_SUBTITLE_ERROR

    assert decode_process_bytes(b"ok\xd1bad") == "ok\ufffdbad"

    print("selfcheck ok: profiles and command construction validated")


if __name__ == "__main__":
    main()
