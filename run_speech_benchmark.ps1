Write-Host "Running benchmarks..."
python speech/benchmark_audio_pipeline.py --whisper-cli "C:\Users\ginle\OneDrive\Documents\Laptop Tests\speech\whisper.cpp\build\bin\Release\whisper-cli.exe" --whisper-model "C:\Users\ginle\OneDrive\Documents\Laptop Tests\speech\whisper.cpp\models\ggml-large-v3-turbo.bin" --threads 8

Write-Host "Done!"