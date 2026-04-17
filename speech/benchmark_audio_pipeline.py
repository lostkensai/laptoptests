import argparse
import csv
import json
import socket
import subprocess
import time
from pathlib import Path

# 3 sample audios
AUDIO_FILES = [
    "speech/samples/audio1.wav",
    "speech/samples/audio2.wav",
    "speech/samples/audio3.wav",
    "speech/samples/audio4.wav",
]

RESULTS_FILE = "results_speech.csv"


def run_command(cmd: list[str]) -> subprocess.CompletedProcess:
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        print("Command failed:")
        print(" ".join(cmd))
        print("\nSTDOUT:\n", result.stdout)
        print("\nSTDERR:\n", result.stderr)
        raise subprocess.CalledProcessError(
            result.returncode,
            cmd,
            output=result.stdout,
            stderr=result.stderr,
        )

    return result

def count_words(text: str) -> int:
    return len(text.split())

def ffprobe_duration(input_file: Path) -> float:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(input_file),
    ]
    result = run_command(cmd)
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def transcribe_with_whisper(
    whisper_cli: Path,
    model_path: Path,
    audio_file: Path,
    threads: int = 8,
    language: str = "en",
) -> dict:
    cmd = [
        str(whisper_cli),
        "-m", str(model_path),
        "-f", str(audio_file),
        "-t", str(threads),
        "-l", language,
        "-nt",
    ]

    start = time.perf_counter()
    result = run_command(cmd)
    elapsed_s = time.perf_counter() - start

    transcript = result.stdout.strip()

    return {
        "transcription_time_s": elapsed_s,
        "transcript_text": transcript.replace("\r", " ").replace("\n", " ").strip(),
        "stderr_text": result.stderr.replace("\r", " ").replace("\n", " ").strip(),
    }


def write_csv(rows: list[dict], output_file: str) -> None:
    fieldnames = [
        "laptop_name",
        "audio_file",
        "audio_duration_s",
        "whisper_model",
        "whisper_threads",
        "whisper_transcription_time_s",
        "whisper_realtime_factor",
        "num_output_words",
        "words_per_second",
        "transcript_text",
    ]

    file_exists = Path(output_file).exists()

    with open(output_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark whisper.cpp transcription")
    parser.add_argument("--whisper-cli", required=True, help="Path to whisper-cli.exe")
    parser.add_argument("--whisper-model", required=True, help="Path to whisper ggml model")
    parser.add_argument("--threads", type=int, default=8, help="Threads for whisper-cli")
    args = parser.parse_args()

    whisper_cli = Path(args.whisper_cli).resolve()
    whisper_model = Path(args.whisper_model).resolve()

    rows = []

    for audio in AUDIO_FILES:
        audio_path = Path(audio).resolve()
        if not audio_path.exists():
            print(f"Skipping missing file: {audio_path}")
            continue

        print(f"\n=== Processing {audio_path.name} ===")

        audio_duration_s = ffprobe_duration(audio_path)

        transcribe_with_whisper(
            whisper_cli=whisper_cli,
            model_path=whisper_model,
            audio_file=audio_path,
            threads=args.threads,
            language="en",
        )

        whisper_result = transcribe_with_whisper(
            whisper_cli=whisper_cli,
            model_path=whisper_model,
            audio_file=audio_path,
            threads=args.threads,
            language="en",
        )

        whisper_time_s = whisper_result["transcription_time_s"]
        realtime_factor = audio_duration_s / whisper_time_s if whisper_time_s > 0 else 0.0
        num_output_words = count_words(whisper_result["transcript_text"])
        words_per_second = num_output_words / whisper_time_s if whisper_time_s > 0 else 0.0

        row = {
            "laptop_name": socket.gethostname(),
            "audio_file": audio_path.name,
            "audio_duration_s": round(audio_duration_s, 3),
            "whisper_model": whisper_model.name,
            "whisper_threads": args.threads,
            "whisper_transcription_time_s": round(whisper_time_s, 3),
            "whisper_realtime_factor": round(realtime_factor, 3),
            "num_output_words": num_output_words,
            "words_per_second": round(words_per_second, 3),
            "transcript_text": whisper_result["transcript_text"],
        }

        rows.append(row)

        print(
            f"{audio_path.name} | "
            f"duration={audio_duration_s:.2f}s | "
            f"whisper={whisper_time_s:.2f}s | "
            f"rtf={realtime_factor:.2f}x"
        )

    if rows:
        write_csv(rows, RESULTS_FILE)
        print(f"\nSaved results to {RESULTS_FILE}")
    else:
        print("\nNo rows written.")


if __name__ == "__main__":
    main()