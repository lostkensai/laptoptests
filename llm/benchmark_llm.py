import requests
import csv
import socket
import argparse
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"

OPTIONS = {
    "temperature": 0
}

PROMPTS = {
    "short": "llm/short.txt",
    "long": "llm/long.txt",
}

RESULTS_FILE = "results_llm.csv"


def load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def run_test(model: str, prompt: str, keep_alive: str = "30m") -> dict:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": keep_alive,
        "options": OPTIONS,
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=600)
    response.raise_for_status()
    data = response.json()

    total_s = data.get("total_duration", 0) / 1e9
    prompt_eval_count = data.get("prompt_eval_count", 0)
    prompt_eval_s = data.get("prompt_eval_duration", 0) / 1e9
    eval_count = data.get("eval_count", 0)
    eval_s = data.get("eval_duration", 0) / 1e9

    prompt_tps = prompt_eval_count / prompt_eval_s if prompt_eval_s > 0 else 0.0
    gen_tps = eval_count / eval_s if eval_s > 0 else 0.0

    # Some models may not put useful text in "response".
    response_text = (data.get("response", "") or "").replace("\r", " ").replace("\n", " ").strip()

    return {
        "total_s": total_s,
        "prompt_eval_s": prompt_eval_s,
        "gen_eval_s": eval_s,
        "prompt_tps": prompt_tps,
        "gen_tps": gen_tps,
        "gen_tokens": eval_count,
        "response_text": response_text,
    }


def benchmark_scenario(name: str, prompt: str, model: str) -> dict:
    print(f"\n=== Scenario: {name} ===")

    # Warm up model first so the actual measurement is a warm run
    run_test(model, "warmup")

    result = run_test(model, prompt)

    row = {
        "laptop_name": socket.gethostname(),
        "scenario": name,
        "total_time_s": result["total_s"],
        "processing_time_s": result["prompt_eval_s"],
        "generation_time_s": result["gen_eval_s"],
        "processing_tps": result["prompt_tps"],
        "generation_tps": result["gen_tps"],
        "gen_tokens": result["gen_tokens"],
        "response_text": result["response_text"],
    }

    print(
        f"{name} | "
        f"total={row['total_time_s']:.2f}s | "
        f"processing={row['processing_time_s']:.2f}s | "
        f"generation={row['generation_time_s']:.2f}s | "
        f"proc_tps={row['processing_tps']:.2f} | "
        f"gen_tps={row['generation_tps']:.2f}"
    )

    return row


def write_csv(rows: list[dict], output_file: str) -> None:
    fieldnames = [
        "laptop_name",
        "scenario",
        "total_time_s",
        "processing_time_s",
        "generation_time_s",
        "processing_tps",
        "generation_tps",
        "gen_tokens",
        "response_text",
    ]

    file_exists = Path(output_file).exists()

    with open(output_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM Benchmark Script")
    parser.add_argument(
        "model",
        help="Ollama model name (e.g. qwen2.5:7b)"
    )

    args = parser.parse_args()
    selected_model = args.model

    all_rows = []

    for scenario_name, prompt_file in PROMPTS.items():
        prompt = load_prompt(prompt_file)
        scenario_row = benchmark_scenario(scenario_name, prompt, selected_model)
        all_rows.append(scenario_row)

    write_csv(all_rows, RESULTS_FILE)
    print(f"\nSaved results to {RESULTS_FILE}")


if __name__ == "__main__":
    main()