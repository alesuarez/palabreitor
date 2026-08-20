#!/usr/bin/env python3
"""Palabreitor: extrae el guion hablado de un video de clase a un TXT con marcas de tiempo."""

import argparse
import ctypes
import itertools
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
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


def _transcribe_with_spinner(segments, message: str = "Transcribiendo") -> list:
    chars = itertools.cycle("/-\\|")
    stop = threading.Event()

    def spin() -> None:
        while not stop.is_set():
            sys.stdout.write(f"\r{message} {next(chars)}")
            sys.stdout.flush()
            time.sleep(0.1)

    t = threading.Thread(target=spin, daemon=True)
    t.start()
    try:
        result = list(segments)
        return result
    finally:
        stop.set()
        t.join()
        sys.stdout.write("\r" + " " * (len(message) + 2) + "\r")
        sys.stdout.flush()


def transcribe(wav: Path, device: str) -> list:
    print(f"Cargando modelo {MODEL} en {device.upper()}...")
    compute = "float16" if device == "cuda" else "int8"
    model = WhisperModel(MODEL, device=device, compute_type=compute)
    segments, info = model.transcribe(
        str(wav),
        language=LANG,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )
    print(f"Idioma detectado: {info.language} ({info.language_probability * 100:.0f}%)")
    print("Procesando audio (no cierres la ventana)...")
    return _transcribe_with_spinner(segments)


def write_txt(segments: list, out: Path) -> None:
    lines = []
    for seg in segments:
        text = seg.text.strip()
        if text:
            lines.append(f"[{fmt_ts(seg.start)}] {text}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Guardado: {out}")


def human_size(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024 or unit == "GB":
            return f"{num:.1f} {unit}" if unit != "B" else f"{int(num)} B"
        num /= 1024
    return f"{num:.1f} GB"


def fmt_clock(dt) -> str:
    return dt.strftime("%H:%M:%S")


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

    t_start = time.time()

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

    elapsed = time.time() - t_start
    if elapsed < 60:
        tiempo = f"{elapsed:.0f} seg"
    else:
        mins, secs = divmod(int(elapsed), 60)
        tiempo = f"{mins:02d}:{secs:02d} min"
    print()
    print("=" * 52)
    print("  RESUMEN DE PROCESAMIENTO")
    print("=" * 52)
    print(f"  Archivo de entrada : {video.name}")
    print(f"  Archivo de salida  : {out}  ({human_size(out.stat().st_size)})")
    print(f"  Hora de inicio     : {fmt_clock(datetime.fromtimestamp(t_start))}")
    print(f"  Hora de fin        : {fmt_clock(datetime.now())}")
    print(f"  Tamaño de entrada  : {human_size(video.stat().st_size)}")
    print(f"  Tiempo de proceso  : {tiempo}")
    print("=" * 52)


if __name__ == "__main__":
    main()