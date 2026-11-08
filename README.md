# Poetry Style Analyzer

Compares an OpenAI model and an open-weight model on poetry analysis
(form, meter, rhyme, tone, imagery, devices, revision suggestions).

## Setup
```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...          # Windows: set OPENAI_API_KEY=sk-...
```

### Open-weight model (pick one)
**Local with Ollama (free):**
```bash
ollama pull llama3.1:8b
# defaults already point to http://localhost:11434/v1
```
**Hosted (Groq, Together, etc.):** set
```bash
export OPEN_BASE_URL=https://api.groq.com/openai/v1
export OPEN_API_KEY=your_key
export OPEN_MODEL=llama-3.1-8b-instant
```
Optional: `export OPENAI_MODEL=gpt-4o`

## Run
```bash
streamlit run app.py                 # interactive side-by-side UI
python run_comparison.py --runs 3    # batch evaluation -> results/
```

## Evaluation outputs (results/)
- `results.csv`: every run (model, latency, form, meter, rhyme)
- `summary.csv`: parse success, avg latency, rhyme consistency, rhyme accuracy
- `raw.json`: full raw outputs, for manual 1-5 quality scoring

## To do for the report
1. Add 20-30 poems to `poems/` (one `.txt` each)
2. Annotate rhyme scheme in `annotations.csv`
3. Run the batch, then manually rate insight/accuracy/usefulness (1-5)
4. Write up findings and limitations
