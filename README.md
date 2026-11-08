# Poetry Style Analyzer

Compares two open-weight language models, OpenAI's **gpt-oss-120b** and **gpt-oss-20b**, on poetry analysis: form, meter, rhyme scheme, tone, themes, imagery and literary devices. Each model gets the same prompt and returns a structured JSON analysis, and the batch script measures how reliable, fast, accurate and consistent each one is.

## Results (16 poems x 3 runs per model)

| Metric | gpt-oss-120b | gpt-oss-20b |
|---|---|---|
| Valid output | 100% | 85% |
| Avg time per poem | 2.5 s | 10.0 s |
| Rhyme accuracy | 69% | 52% |
| Rhyme consistency | 62% | 62% |

The larger model was more accurate, always returned usable output and was faster. Both gave different rhyme schemes across repeated runs on about 4 in 10 poems, so a single answer from either model should not be trusted for technical analysis.

## Dataset

16 poems in `poems/`, with hand-annotated rhyme schemes in `annotations.csv`:

- 11 public-domain poems (Shakespeare, Rossetti, Herrick, Blake, Tennyson, Wordsworth, Whitman)
- 5 original free-verse poems (`own_*.txt`) by the repo owner. These are not licensed for reuse.

## How it works

- `analyzer.py` sends a poem to any OpenAI-compatible chat endpoint, with retries and request pacing. It uses only the Python standard library.
- `run_comparison.py` runs every poem through both models and writes `results/results.csv`, `results/summary.csv` and `results/raw.json`.
- `app.py` is an optional Streamlit page for trying one poem on both models (needs `pip install streamlit`; Python 3.12 or 3.13 recommended).

## Run it

You need a free Groq API key from console.groq.com.

PowerShell:

```
$env:OPENAI_BASE_URL="https://api.groq.com/openai/v1"
$env:OPEN_BASE_URL="https://api.groq.com/openai/v1"
$env:OPENAI_MODEL="openai/gpt-oss-120b"
$env:OPEN_MODEL="openai/gpt-oss-20b"
$env:OPENAI_API_KEY="your-key"
$env:OPEN_API_KEY="your-key"
python run_comparison.py --runs 3
```

Mac/Linux: use `export NAME="value"` instead of `$env:NAME="value"`.

Never commit your API key. It is read from environment variables and is not stored in any file.

## Limitations

- Small dataset (16 poems), only 3 runs per poem.
- Both models are from the same developer, so this tests size, not different model families.
- Rhyme scoring is exact-match, so a correct scheme in a different format counts as wrong, and failed runs count as incorrect.
- Meter, tone and the quality of the suggestions were not scored.
- Six of the 16 poems are unrhymed, where answering "none" is correct.