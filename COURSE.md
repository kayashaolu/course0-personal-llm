# COURSE.md

## What this repo is

This is a frozen copy of `kekoexchange/personal-llm`, made for Systems Thinking Lab's Course 0. The original is a project by Kay Ashaolu, who teaches Course 0: a desktop ChatGPT-style app that runs entirely on your own machine, with no cloud API calls. `README.md` in this repo is Kay's own project writeup, plus the Windows setup and test notes added for this course. This file is the course companion: what to do with the code once you have it.

Course 0 lives at [systemthinkinglab.ai](https://systemthinkinglab.ai). Three challenges are built on this codebase: reading the code cold, then two feature builds, one in craft mode and one in direction mode. They are described there, not here. If you got here without a link to those pages, start there.

## Who this is for

Anyone working through Course 0's challenges. You will fork this repo, run it, read it, then build on it. Nothing here assumes you have used Ollama, Peewee, Eel, or React before.

## Quick start

Fork this repo on GitHub, then clone your fork:

```bash
git clone https://github.com/<your-username>/course0-personal-llm.git
cd course0-personal-llm
```

Work from your fork, not this repo directly. Your commits, your challenge branches, your `scaffold-wiki/` notes: all of it belongs to your copy.

You need [Google Chrome](https://www.google.com/chrome/) installed first, on every platform: the app opens its window in Chrome, and nothing below installs it for you.

### Mac and Linux

One command installs everything else (a Python virtual environment, the Node packages, and Ollama if it is missing), builds the frontend, and starts the app:

```bash
npm run start
```

That chains three steps you can also run one at a time: `npm run setup`, then `npm run build`, then `./.venv/bin/python backend/main.py`. The default model is `gemma3:270m`, about 290 MB, and downloads on first run. It runs on an ordinary laptop with no dedicated GPU.

### A second terminal for the worker

`npm run start` only runs the app itself. Background jobs (a model pull, once you build that feature) run in a separate process, `backend/worker.py`, that you start yourself in a second terminal:

```bash
npm run worker
```

This is deliberate, not a missing convenience script: you are meant to see two separate processes sharing one database, not have that boundary hidden behind one command. If a feature you build sets `PERSONAL_LLM_DB` to point the database somewhere other than the default, set it the same way in both terminals. The app and the worker each read that variable independently at startup; if one terminal has it set and the other doesn't, the two processes open two different SQLite files and silently stop seeing each other's writes; nothing raises an error when that happens.

### Windows

`npm run setup` runs `scripts/setup.sh`, a POSIX shell script, and it will not run on Windows. This path is unverified: it has not been tested on a real Windows machine, so treat it as a starting point, not a guarantee.

Install [Python 3.11+](https://www.python.org/downloads/), [Node 22+](https://nodejs.org/), and [Ollama](https://ollama.com/) yourself first, in addition to Chrome above; the setup script's automatic Ollama install only covers Mac and Linux. Then, from the repo root:

```
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm install
npm run build
```

Run the app:

```
.venv\Scripts\python.exe backend\main.py
```

If any of this breaks on your machine, email support@systemthinkinglab.ai rather than guessing.

### Running the tests

```bash
npm run test:no-ollama
```

This runs both suites, Python and React, and skips the tests that need a live Ollama server, so it works even without a model downloaded. It is POSIX-only, same reason as setup: it shells out to `./.venv/bin/python`. On Windows, run the two suites yourself:

```
.venv\Scripts\python.exe -m pytest -m "not ollama"
npx vitest run
```

There is no hosted CI for this repo. Every test runs on your own machine, every time.

## What not to do

**Do not open a pull request against this repo.** `kayashaolu/course0-personal-llm` is frozen: a snapshot taken once and left alone. It will not change, and a pull request against it will not be reviewed. Every change you make belongs in your own fork.

**Do not commit secrets.** The app needs none by default. The only two environment variables it reads, `PERSONAL_LLM_MODEL` and `PERSONAL_LLM_DB`, are configuration, not credentials. If a feature you build ever needs a key, put it in a `.env` file at the repo root. That file is listed in `.gitignore`, so it stays on your machine.

## scaffold-wiki/ and your submission

If you work through the challenges in scaffold's mentor mode, scaffold keeps a `scaffold-wiki/` folder: your own working notes, and a running record of what you have demonstrated you understand. `.gitignore` excludes it on purpose. Those notes are yours, not a build artifact, and they have no reason to live in your git history.

Your challenge submission is a zip of your whole working folder, not a git push. That zip includes `scaffold-wiki/` even though git never tracked it: the grader reads your notes as part of the submission, so the ignore rule and the requirement to submit them are not in conflict. Zip the folder, upload it where the course tells you to.

## Back to the course

Everything the code does not explain, the challenges, the rubric, what "craft mode" and "direction mode" mean, lives at [systemthinkinglab.ai](https://systemthinkinglab.ai).

---
