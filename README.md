# Personal LLM - a desktop ChatGPT clone that runs 100% local off of the cloud

## Author
[Kay Ashaolu](https://www.linkedin.com/in/kayashaolu/)

## Description
Personal LLM is a desktop chat app that runs a language model entirely on your own machine, with no cloud API calls. The backend is Python, and the frontend is React, served into a Chrome window through Python-Eel. Conversations are stored in SQLite through the Peewee ORM, and Ollama runs the model. This is the codebase Systems Thinking Lab's Course 0 uses for its three challenges: reading code you did not write, then building two features by directing an AI agent.

## Learn with this repo
This repo is the practice ground for Course 0, a self-paced course that teaches the plan-first workflow for directing an AI agent on real code. Course 0 is $99: [systemthinkinglab.ai/course-0.html](https://systemthinkinglab.ai/course-0.html)

The seven building blocks Systems Thinking Lab teaches, the knowledge behind every architecture call, are free to learn on their own, no course required: [systemthinkinglab.ai/learn/](https://systemthinkinglab.ai/learn/)

Courses I-IV teach those same seven blocks on real systems like Instagram, Stripe, and Netflix, as one guided path.

## Technologies Used
- HTML
- CSS
- JavaScript
- Python
- Ollama
- LLM
- ORM [Peewee](https://docs.peewee-orm.com/en/latest/)
- RDBMS [Sqlite3](https://sqlite.org/)
- [Python-Eel](https://github.com/python-eel/Eel)

## Demo
[![Personal-LLM Demo Video](http://img.youtube.com/vi/BwRgVGhxm70/0.jpg)](http://www.youtube.com/watch?v=BwRgVGhxm70 "Personal-LLM Demo Video")

## Technical System Design
[![Personal-LLM System Design Video](http://img.youtube.com/vi/MgdypIh9wrA/0.jpg)](http://www.youtube.com/watch?v=MgdypIh9wrA "Personal-LLM System Design Video")

## Setup Instructions
1. Please download and install the following dependencies
  * [Python 3](https://www.python.org/downloads/) (3.11 or newer)
  * [Node.js](https://nodejs.org/) (22 or newer)
  * [Google Chrome](https://www.google.com/chrome/)
  * [Ollama](https://ollama.com/) — optional to pre-install: `npm run start` installs it if it's missing (Linux via the official script, macOS via Homebrew) and starts it if it isn't running.
    * Ollama is a LLM model backend that lets you download and access LLMs locally and use it in your applications.
2. Clone this repository
3. Run `npm run start` to run the project (`npm run setup` and `npm run build` are the individual steps)

## Windows Setup (UNVERIFIED)
Everything above has only been run on Linux and macOS. `scripts/setup.sh` is a POSIX shell script and will not run on Windows. The steps below are the equivalent commands for a Windows machine; they have not been tested on one, so treat them as a starting point, not a verified path.

1. Install [Python 3](https://www.python.org/downloads/) (3.11 or newer), [Node.js](https://nodejs.org/) (22 or newer), and [Google Chrome](https://www.google.com/chrome/).
2. Install [Ollama](https://ollama.com/) with its Windows installer, or `winget install Ollama.Ollama`.
3. Clone this repository, then from the repo root, in PowerShell or Command Prompt:
   ```
   py -m venv .venv
   .venv\Scripts\python.exe -m pip install -r requirements.txt
   .venv\Scripts\python.exe -m pip install -r requirements-dev.txt
   npm install
   npm run build
   ```
4. Run the app: `.venv\Scripts\python.exe backend\main.py`
5. The npm test commands (`npm run test`, `npm run test:backend`, `npm run test:no-ollama`) are POSIX-only: they call `./.venv/bin/python`, which does not exist on Windows. Run the two suites directly instead:
   ```
   .venv\Scripts\python.exe -m pytest -m "not ollama"
   npx vitest run
   ```

## Configuration
Optional environment variables:
- `PERSONAL_LLM_MODEL` — Ollama model to pull and chat with (default `gemma3:270m`)
- `PERSONAL_LLM_DB` — path to the SQLite file (default `storage/app/data.db` under the repo root; the folder is created if missing)
    * The default model is [Gemma 3 270M](https://ollama.com/library/gemma3) from Google, about 290 MB; the first run downloads it. Set `PERSONAL_LLM_MODEL` to use a different Ollama model.

## Background jobs
Long-running background work (a model pull, once that feature exists) runs in a separate process, `backend/worker.py`, started with its own command in a second terminal:

```bash
npm run worker
```

That is a second terminal on purpose: the app (`npm run start`) does not start the worker for you, so the two processes stay visible as two separate things sharing one database. If you set `PERSONAL_LLM_DB` to a non-default path, set it the same way in both terminals. Each process reads that variable independently at startup, so a mismatch between the two silently points them at two different SQLite files, with no error from either side.

## Running tests
Run `npm run setup` first (once per clone; it installs pytest into `.venv` and vitest into `node_modules`). Backend and frontend tests are separate commands:

```bash
npm run test:backend    # Python: pytest over backend/tests/
npm run test:frontend   # React:  vitest over frontend/tests/
npm test                # both, one after the other; fails if either failed
npm run test:no-ollama  # both, skipping the tests that need a running Ollama server
```

Each prints how many tests passed and failed, plus the error for every failure. There is no hosted CI for this repo; every one of these commands, including `npm run test:no-ollama`, runs entirely on your own machine.

The backend suite includes a few tests marked `ollama` that talk to the real Ollama server on `localhost:11434` and send one short prompt to the configured model (`PERSONAL_LLM_MODEL`, default `gemma3:270m`). They fail with a message telling you what to do if Ollama isn't running or the model isn't downloaded. Everything else runs with the LLM stubbed out and needs no Ollama, browser, or network. To skip the Ollama tests: `./.venv/bin/python -m pytest -m "not ollama"` (`npm run test:no-ollama` does this for both suites at once).
