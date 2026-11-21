# Agentic Money Tracker

Syncs transactions from Fio banka, categorizes them with a vector DB (ChromaDB), and is being built toward a LangGraph agent.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- A Fio banka API token

## Setup

1. Install dependencies (creates `.venv` from `uv.lock`):

   ```bash
   uv sync
   ```

2. Create a `.env` file in the project root:

   ```
   FIO_TOKEN_SHARE=your_fio_api_token
   ANTHROPIC_API_KEY=your_anthropic_key   # for the agent
   ```

   Optional overrides (defaults shown):

   ```
   MONEY_DB=data/money.db
   MONEY_VECTOR_DB=data/chroma
   ```

   Note: the code reads these from the environment, so export them (or load the `.env`) before running:

   ```bash
   set -a; source .env; set +a
   ```

## Run

Sync new transactions from the bank into the local database:

```bash
uv run python main.py
```

It prints the number of new transactions. Data is stored under `data/` (git-ignored).

## Development

```bash
uv run pytest        # tests
uv run ruff check .  # lint
uv run mypy src      # type check
```
