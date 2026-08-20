#!/usr/bin/env python3
"""Palabreitor: extrae el guion hablado de un video de clase a un TXT con marcas de tiempo."""

import argparse
import ctypes
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import ctranslate2


def _setup_cuda_dlls() -> None:
    base = os.path.normpath(os.path.join(os.path.dirname(ctranslate2.__file__), ".."))
    for sub in ("nvidia/cublas/bin", "nvidia/cudnn/bin"):
        p = os.path.normpath(os.path.join(base, sub))
        if os.path.isdir(p):
            for dll in sorted(os.listdir(p)):
                if dll.lower().endswith(".dll"):
                    try:
                        ctypes.WinDLL(os.path.join(p, dll))
                    except OSError:
                        pass


if sys.platform == "win32":
    _setup_cuda_dlls()
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

from faster_whisper import WhisperModel

MODEL = "large-v3-turbo"
LANG = "es"


def fmt_ts(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def extract_audio(video: Path, wav: Path) -> None:
    print(f"Extrayendo audio de '{video.name}'...")
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(video),
            "-vn", "-ac", "1", "-ar", "16000", "-f", "wav", str(wav),
        ],
        check=True,
    )


def transcribe(wav: Path, device: str) -> list:
    print(f"Cargando modelo {MODEL} en {device.upper()}...")
    compute = "float16" if device == "cuda" else "int8"
    model = WhisperModel(MODEL, device=device, compute_type=compute)
    print("Transcribiendo...")
    segments, info = model.transcribe(
        str(wav),
        language=LANG,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )
    print(f"Idioma detectado: {info.language} ({info.language_probability * 100:.0f}%)")
    return list(segments)


def write_txt(segments: list, out: Path) -> None:
    lines = []
    for seg in segments:
        text = seg.text.strip()
        if text:
            lines.append(f"[{fmt_ts(seg.start)}] {text}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Guardado: {out}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="palabreitor",
        description="Extrae el guion hablado de un video de clase (español) a TXT con timestamps.",
    )
    parser.add_argument("-i", "--input", required=True, help="Video de entrada (mp4, mkv, etc.)")
    parser.add_argument("-o", "--output", required=True, help="Archivo de texto de salida (.txt)")
    parser.add_argument(
        "--device",
        choices=["auto", "cuda", "cpu"],
        default="auto",
        help="Dispositivo de inferencia (auto detecta GPU NVIDIA)",
    )
    args = parser.parse_args()

    video = Path(args.input)
    out = Path(args.output)
    if not video.is_file():
        sys.exit(f"Error: no existe el archivo '{video}'")

    if shutil.which("ffmpeg") is None:
        sys.exit("Error: ffmpeg no está en el PATH. Instálalo con: winget install ffmpeg")

    device = args.device
    if device == "auto":
        try:
            import ctypes
            ctypes.WinDLL("nvcuda.dll")
            device = "cuda"
        except OSError:
            device = "cpu"

    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "audio.wav"
        extract_audio(video, wav)
        segments = transcribe(wav, device)

    write_txt(segments, out)
    print(f"Segmentos: {len(segments)} | Duración total: {fmt_ts(segments[-1].end) if segments else '00:00:00'}")


if __name__ == "__main__":
    main()