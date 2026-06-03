from __future__ import annotations

from pathlib import Path
import json
import re

from command_builder import build_convert_args, build_remux_args

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
        "audio_streams": [{"index": 1, "codec_type": "audio"}, {"index": 2, "codec_type": "audio"}],
        "subtitle_streams": [{"index": 3, "codec_type": "subtitle"}],
    }


def value_after(args: list[str], key: str) -> str:
    try:
        return args[args.index(key) + 1]
    except (ValueError, IndexError) as exc:
        raise AssertionError(f"{key} missing from command: {args}") from exc


def assert_contains(args: list[str], *items: str) -> None:
    for item in items:
        assert item in args, f"{item!r} missing from command: {args}"


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
    assert_contains(remux, "-c", "copy", "-map_chapters", "0")
    assert "-c:v" not in remux
    assert "-c:a" not in remux
    assert "-filter_complex unsafe" not in " ".join(remux)
    assert "raw_args=-filter_complex unsafe" not in remux
    assert "-metadata" in remux
    assert "title=Kept" in remux
    assert "genre=Live" in remux
    assert re.search(r"-disposition:a:1\s+default", " ".join(remux))

    print("selfcheck ok: profiles and command construction validated")


if __name__ == "__main__":
    main()
