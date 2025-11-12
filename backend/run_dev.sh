source .venv/bin/activate

export PYTHONPATH="${PYTHONPATH}:$(pwd)"

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level info
