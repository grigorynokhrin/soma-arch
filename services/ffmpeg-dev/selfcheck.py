from __future__ import annotations

from pathlib import Path
import json
import re

from command_builder import (
    IMAGE_SUBTITLE_ERROR,
    build_convert_args,
    build_convert_plan,
    build_mp4_player_metadata_command,
    build_remux_args,
    decode_process_bytes,
    ensure_output_artifact_path,
    ensure_clear_target,
    safe_filename_component,
    safe_output_filename,
    subtitle_remux_action,
)

HERE = Path(__file__).resolve().parent
PROFILES_PATH = HERE / "profiles.json"


def load_profiles() -> dict[str, dict]:
    profiles = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
    return {item["id"]: item for item in profiles}


def fake_probe(avg_frame_rate: str = "24000/1001", subtitle_codec: str | None = "subrip") -> dict:
    probe = {
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
        "subtitle_streams": [],
    }
    if subtitle_codec:
        probe["subtitle_streams"].append(
            {
                "index": 3,
                "codec_type": "subtitle",
                "codec_name": subtitle_codec,
                "language": "eng",
                "title": "English subtitles must survive",
                "disposition": {"default": 1},
            }
        )
    return probe


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


def assert_convert_shape(profile: dict, *, output_name: str, checks: dict[str, str], probe: dict | None = None) -> list[str]:
    args = build_convert_args(Path("input.mkv"), Path(output_name), profile, probe or fake_probe(subtitle_codec=None))
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


def assert_no_subtitle_map(args: list[str]) -> None:
    assert "0:3" not in args
    assert "-c:s" not in args
    assert "-c:s:0" not in args


def assert_burn_plan(profile: dict, *, output_name: str, codec: str) -> dict:
    plan = build_convert_plan(Path("input path/clip, one & two (test).mkv"), Path(output_name), profile, fake_probe(subtitle_codec=codec))
    args = plan["args"]
    vf = value_after(args, "-vf")
    assert "subtitles=filename='input path/clip, one & two (test).mkv':si=0" in vf
    assert_no_subtitle_map(args)
    assert plan["warnings"], "burn-in warning missing"
    assert f"codec {codec}" in plan["warnings"][0]
    assert "burned into video" in plan["warnings"][0]
    return plan


def assert_safe_filename(value: str, extension: str = "mp4") -> str:
    name = safe_output_filename(value, "output", extension)
    assert "/" not in name
    assert "\\" not in name
    assert "\x00" not in name
    assert ".." not in name
    assert name.endswith(f".{extension}")
    assert name.strip() == name
    return name


def main() -> None:
    profiles = load_profiles()
    assert set(profiles) == {
        "cowon-iaudio-d2-plus",
        "lacie-ss-4x3-vob-pal",
        "lacie-ss-16x9-vob-pal",
        "lacie-ss-16x9-avi",
    }

    human_name = "2002 Queen of the Damned (RU-EN) Rymer & Abbott, Petroni.mp4"
    assert safe_output_filename(human_name, "remuxed", "mp4") == human_name
    assert_safe_filename("../evil.mp4")
    assert_safe_filename("a/b.mp4")
    assert_safe_filename("a\\b.mp4")
    assert safe_output_filename("", "output", "mp4") == "output.mp4"
    assert safe_output_filename("\x01\x02", "output", "mp4") == "output.mp4"
    assert safe_output_filename("movie.mkv", "output", "mp4") == "movie.mp4"
    assert safe_filename_component("  Пример, тест & ok (v1).mkv  ") == "Пример, тест & ok (v1).mkv"

    ensure_clear_target(Path("/tmp/ffmpeg-data"), Path("/tmp/ffmpeg-data/current"))
    ensure_output_artifact_path(Path("/tmp/ffmpeg-data/current/output"), Path("/tmp/ffmpeg-data/current/output/movie.mp4"))
    try:
        ensure_clear_target(Path("/tmp/ffmpeg-data"), Path("/tmp/elsewhere/current"))
        raise AssertionError("clear target outside data dir should fail")
    except RuntimeError:
        pass
    try:
        ensure_output_artifact_path(Path("/tmp/ffmpeg-data/current/output"), Path("/tmp/ffmpeg-data/current/input/movie.mp4"))
        raise AssertionError("metadata post-process path outside output dir should fail")
    except RuntimeError:
        pass

    artifact = {"name": "ffmpeg-batch-subtitle-source-cowon-iaudio-d2-plus.avi"}
    assert artifact["name"] == "ffmpeg-batch-subtitle-source-cowon-iaudio-d2-plus.avi"
    status_model = {"warnings": ["Subtitle stream #3 codec subrip was burned into video."]}
    assert status_model["warnings"][0].startswith("Subtitle stream")

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

    for profile_id, output_name in [
        ("cowon-iaudio-d2-plus", "movie.avi"),
        ("lacie-ss-16x9-avi", "movie.avi"),
        ("lacie-ss-4x3-vob-pal", "movie.vob"),
    ]:
        burn = assert_burn_plan(profiles[profile_id], output_name=output_name, codec="mov_text")
        assert value_after(burn["args"], "-c:v") == profiles[profile_id]["video"]["codec"]
        assert value_after(burn["args"], "-c:a") == profiles[profile_id]["audio"]["codec"]

    cowon_subrip = assert_burn_plan(profiles["cowon-iaudio-d2-plus"], output_name="movie.avi", codec="subrip")
    assert "0:3" not in cowon_subrip["args"]

    xsub_plan = build_convert_plan(Path("input.mkv"), Path("movie.avi"), profiles["cowon-iaudio-d2-plus"], fake_probe(subtitle_codec="xsub"))
    assert_pair(xsub_plan["args"], "-map", "0:3")
    assert_pair(xsub_plan["args"], "-c:s", "copy")
    assert not xsub_plan["warnings"]

    dvdsub_plan = build_convert_plan(Path("input.mkv"), Path("movie.vob"), profiles["lacie-ss-4x3-vob-pal"], fake_probe(subtitle_codec="dvd_subtitle"))
    assert_pair(dvdsub_plan["args"], "-map", "0:3")
    assert_pair(dvdsub_plan["args"], "-c:s", "copy")
    assert not dvdsub_plan["warnings"]

    pgs_plan = build_convert_plan(Path("input.mkv"), Path("movie.avi"), profiles["cowon-iaudio-d2-plus"], fake_probe(subtitle_codec="hdmv_pgs_subtitle"))
    assert_no_subtitle_map(pgs_plan["args"])
    assert pgs_plan["warnings"]
    assert "was dropped" in pgs_plan["warnings"][0]
    assert "hdmv_pgs_subtitle" in pgs_plan["warnings"][0]

    remux = build_remux_args(
        input_path=Path("input.mkv"),
        output_path=Path("remuxed.mp4"),
        probe=fake_probe(),
        audio_streams=[1, 2],
        default_audio_stream=2,
        subtitle_streams=[3],
        metadata={"title": "Kept", "raw_args": "-filter_complex unsafe", "genre": "Live"},
    )
    assert_contains(remux, "-c", "copy", "-map_chapters", "0", "-map_metadata", "-1")
    assert_pair(remux, "-map_chapters", "0")
    assert_pair(remux, "-map_metadata", "-1")
    assert "-movflags" not in remux
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

    metadata_plan = build_mp4_player_metadata_command(
        Path("/tmp/ffmpeg-data/current/output/Queen of the Damned.mp4"),
        {
            "title": "Queen of the Damned",
            "artist": "Rymer & Abbott, Petroni",
            "genre": "RU-EN",
            "description": "русский текст",
            "publisher": "Publisher & Co.",
            "language": "rus",
            "raw_args": "-unsafe",
        },
        Path("/tmp/ffmpeg-data/current/output"),
    )
    exiftool = metadata_plan["args"]
    assert exiftool[0] == "exiftool"
    assert "-overwrite_original" in exiftool
    assert exiftool[-1] == "/tmp/ffmpeg-data/current/output/Queen of the Damned.mp4"
    assert "-ItemList:Title=Queen of the Damned" in exiftool
    assert "-UserData:Title=Queen of the Damned" in exiftool
    assert "-Keys:Title=Queen of the Damned" in exiftool
    assert "-ItemList:Artist=Rymer & Abbott, Petroni" in exiftool
    assert "-UserData:Author=Rymer & Abbott, Petroni" in exiftool
    assert "-ItemList:Genre=RU-EN" in exiftool
    assert "-ItemList:Description=русский текст" in exiftool
    assert "-ItemList:LongDescription=русский текст" in exiftool
    assert "-UserData:Description=русский текст" in exiftool
    assert "-Keys:Description=русский текст" in exiftool
    assert not any("Comment=" in item for item in exiftool)
    assert "-UserData:Publisher=Publisher & Co." in exiftool
    assert "-Keys:Publisher=Publisher & Co." in exiftool
    assert not any("raw_args" in item or "-unsafe" in item for item in exiftool)
    assert metadata_plan["warnings"]
    assert "Global language" in metadata_plan["warnings"][0]

    print("selfcheck ok: profiles and command construction validated")


if __name__ == "__main__":
    main()
