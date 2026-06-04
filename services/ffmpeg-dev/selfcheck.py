from __future__ import annotations

import json
import re
from pathlib import Path

from command_builder import (
    ALLOWED_METADATA_KEYS,
    IMAGE_SUBTITLE_ERROR,
    build_convert_args,
    build_convert_plan,
    build_runtime_convert_plan,
    build_mp4_player_metadata_command,
    build_remux_args,
    decode_process_bytes,
    ensure_output_artifact_path,
    ensure_clear_target,
    metadata_postprocess_warning,
    normalize_mp4_metadata_value,
    remux_status_for_warnings,
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


def fake_probe_size(width: int, height: int, display_aspect_ratio: str, subtitle_codec: str | None = None) -> dict:
    probe = fake_probe(subtitle_codec=subtitle_codec)
    probe["video_streams"][0].update(
        {
            "width": width,
            "height": height,
            "display_aspect_ratio": display_aspect_ratio,
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


def assert_no_burn_or_pad(args: list[str]) -> None:
    vf = value_after(args, "-vf")
    assert "subtitles=" not in vf, f"subtitle burn filter must not be used: {vf}"
    assert "pad=" not in vf, f"padding/black bars must not be default behavior: {vf}"


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
    assert_no_burn_or_pad(args)
    if checks.get("fourcc"):
        assert_contains(args, "-vtag", checks["fourcc"])
    if checks.get("format"):
        assert value_after(args, "-f") == checks["format"]
    return args


def assert_no_subtitle_map(args: list[str]) -> None:
    assert "0:3" not in args
    assert "-c:s" not in args
    assert "-c:s:0" not in args


def assert_drop_plan(profile: dict, *, output_name: str, codec: str) -> dict:
    plan = build_convert_plan(Path("input path/clip, one & two (test).mkv"), Path(output_name), profile, fake_probe(subtitle_codec=codec))
    args = plan["args"]
    assert_no_burn_or_pad(args)
    assert_no_subtitle_map(args)
    assert plan["warnings"], "drop warning missing"
    assert f"codec {codec}" in plan["warnings"][0]
    assert "was dropped because profile" in plan["warnings"][0]
    assert "does not support subtitle preservation" in plan["warnings"][0]
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
    assert ALLOWED_METADATA_KEYS == {"title", "artist", "date", "genre", "description"}
    assert "publisher" not in ALLOWED_METADATA_KEYS
    assert "language" not in ALLOWED_METADATA_KEYS

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
    status_model = {"warnings": ["Subtitle stream #3 codec subrip was dropped because profile cowon-iaudio-d2-plus does not support subtitle preservation."]}
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
    assert_video_filter(cowon, "setsar=1")
    assert_video_filter(cowon, "setdar=4:3")
    assert "pad=" not in value_after(cowon, "-vf")

    lacie_4x3 = assert_convert_shape(
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
        probe=fake_probe_size(1280, 720, "16:9", subtitle_codec=None),
    )
    lacie_4x3_vf = value_after(lacie_4x3, "-vf")
    assert "crop='min(iw,ih*1.3333333333333333)':ih:(iw-ow)/2:0" in lacie_4x3_vf
    assert "scale=720:576" in lacie_4x3_vf
    assert "setdar=4:3" in lacie_4x3_vf
    assert "setsar=1" not in lacie_4x3_vf
    assert "pad=" not in lacie_4x3_vf

    lacie_16x9_vob = assert_convert_shape(
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
        probe=fake_probe_size(1280, 720, "16:9", subtitle_codec=None),
    )
    lacie_16x9_vob_vf = value_after(lacie_16x9_vob, "-vf")
    assert "crop=" not in lacie_16x9_vob_vf
    assert "scale=720:576" in lacie_16x9_vob_vf
    assert "setdar=16:9" in lacie_16x9_vob_vf
    assert "setsar=1" not in lacie_16x9_vob_vf
    assert "pad=" not in lacie_16x9_vob_vf
    runtime_plan = build_runtime_convert_plan(
        "2022 remuxed 1 2 3.mp4",
        Path("/data/current/input/001-2022 remuxed 1 2 3.mp4"),
        Path("/data/current/output"),
        profiles["lacie-ss-16x9-vob-pal"],
        fake_probe_size(1280, 720, "16:9", subtitle_codec="mov_text"),
    )
    runtime_args = runtime_plan["args"]
    runtime_vf = value_after(runtime_args, "-vf")
    assert runtime_plan["output_path"].name == "2022 remuxed 1 2 3-lacie-ss-16x9-vob-pal.vob"
    assert "subtitles=" not in runtime_vf
    assert "pad=" not in runtime_vf
    assert "crop=" not in runtime_vf
    assert runtime_vf == "scale=720:576,setdar=16:9"
    assert "0:3" not in runtime_args
    assert "-c:s" not in runtime_args
    assert runtime_plan["warnings"] == [
        "Subtitle stream #3 codec mov_text was dropped because profile lacie-ss-16x9-vob-pal does not support subtitle preservation."
    ]
    assert "burned" not in " ".join(runtime_plan["warnings"])
    assert "subtitles=" not in runtime_plan["command"]
    assert "pad=" not in runtime_plan["command"]

    lacie_16x9_avi = assert_convert_shape(
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
        probe=fake_probe_size(1280, 720, "16:9", subtitle_codec=None),
    )
    lacie_16x9_avi_vf = value_after(lacie_16x9_avi, "-vf")
    assert "crop=" not in lacie_16x9_avi_vf
    assert "scale=1024:576" in lacie_16x9_avi_vf
    assert "setsar=1" in lacie_16x9_avi_vf
    assert "setdar=16:9" in lacie_16x9_avi_vf
    assert "pad=" not in lacie_16x9_avi_vf

    for profile_id, output_name in [
        ("cowon-iaudio-d2-plus", "movie.avi"),
        ("lacie-ss-16x9-avi", "movie.avi"),
        ("lacie-ss-4x3-vob-pal", "movie.vob"),
    ]:
        drop = assert_drop_plan(profiles[profile_id], output_name=output_name, codec="mov_text")
        assert value_after(drop["args"], "-c:v") == profiles[profile_id]["video"]["codec"]
        assert value_after(drop["args"], "-c:a") == profiles[profile_id]["audio"]["codec"]

    cowon_subrip = assert_drop_plan(profiles["cowon-iaudio-d2-plus"], output_name="movie.avi", codec="subrip")
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
    assert "does not support subtitle preservation" in pgs_plan["warnings"][0]

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
    assert normalize_mp4_metadata_value("date", "2002") == "2002:01:01 00:00:00"
    assert normalize_mp4_metadata_value("date", "2002-05-17") == "2002:05:17 00:00:00"
    assert normalize_mp4_metadata_value("date", "2002:05:17 12:34:56") == "2002:05:17 12:34:56"

    metadata_plan = build_mp4_player_metadata_command(
        Path("/tmp/ffmpeg-data/current/output/Queen of the Damned.mp4"),
        {
            "title": "Queen of the Damned",
            "artist": "Rymer & Abbott, Petroni",
            "date": "2002",
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
    assert_pair(exiftool, "-api", "LargeFileSupport=1")
    assert "-overwrite_original" in exiftool
    assert exiftool[-1] == "/tmp/ffmpeg-data/current/output/Queen of the Damned.mp4"
    assert "-QuickTime:Encoder=" in exiftool
    assert "-ItemList:Encoder=" in exiftool
    assert "-UserData:Encoder=" in exiftool
    assert "-Keys:Encoder=" in exiftool
    assert "-ItemList:Title=Queen of the Damned" in exiftool
    assert "-UserData:Title=Queen of the Damned" in exiftool
    assert "-Keys:Title=Queen of the Damned" in exiftool
    assert "-ItemList:Artist=Rymer & Abbott, Petroni" in exiftool
    assert "-UserData:Author=Rymer & Abbott, Petroni" in exiftool
    assert "-ItemList:ContentCreateDate=2002:01:01 00:00:00" in exiftool
    assert "-ItemList:Genre=RU-EN" in exiftool
    assert "-ItemList:Description=русский текст" in exiftool
    assert "-ItemList:LongDescription=русский текст" in exiftool
    assert "-UserData:Description=русский текст" in exiftool
    assert "-Keys:Description=русский текст" in exiftool
    assert not any("Comment=" in item for item in exiftool)
    assert not any("Publisher" in item for item in exiftool)
    assert not any("Producer" in item for item in exiftool)
    assert not any("LANGUAGE" in item or "Language" in item for item in exiftool)
    assert not any("taglib" in item.lower() for item in exiftool)
    assert not any("raw_args" in item or "-unsafe" in item for item in exiftool)
    assert metadata_plan["warnings"] == []
    metadata_warning = metadata_postprocess_warning("End of processing at large atom (LargeFileSupport not enabled)")
    assert "remuxed MP4 was preserved" in metadata_warning
    assert "LargeFileSupport" in metadata_warning
    assert remux_status_for_warnings([]) == "done"
    assert remux_status_for_warnings([metadata_warning]) == "done_with_warnings"
    preserved_artifact_model = {
        "status": remux_status_for_warnings([metadata_warning]),
        "artifacts": [{"name": "Queen of the Damned.mp4", "path": "/tmp/ffmpeg-data/current/output/Queen of the Damned.mp4"}],
        "warnings": [metadata_warning],
        "error": None,
    }
    assert preserved_artifact_model["status"] == "done_with_warnings"
    assert preserved_artifact_model["artifacts"][0]["name"] == "Queen of the Damned.mp4"
    assert preserved_artifact_model["error"] is None

    template = (HERE / "templates" / "index.html").read_text(encoding="utf-8")
    assert 'name="publisher"' not in template
    assert 'name="language"' not in template
    assert 'name="description"' in template

    print("selfcheck ok: profiles and command construction validated")


if __name__ == "__main__":
    main()
