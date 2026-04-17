Write-Host "Running benchmarks..."
python llm\benchmark_llm.py gemma4:e2b
python llm\benchmark_llm.py qwen3.5:9b

Write-Host "Done!"