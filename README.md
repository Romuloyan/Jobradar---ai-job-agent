# JobRadar AI Job Agent

AI-powered job search and vacancy evaluation agent built with Python, Streamlit and the Gemini API.

This project was created as a practical AI agent for job-search automation. It collects job vacancies from online sources, applies rule-based pre-filtering, sends relevant vacancies to a Large Language Model, compares them against a candidate profile, and stores the structured evaluation history.

## What it does

- Searches job vacancies from multiple sources.
- Applies Python pre-filters before using the LLM.
- Evaluates each job vacancy against a candidate profile.
- Classifies vacancies by compatibility, area, seniority level and recommended CV profile.
- Saves analysed vacancies to a CSV history file.
- Provides a Streamlit interface for automatic and manual job analysis.
- Separates Portuguese job-market sources from international/remote sources.

## Current sources

- Net-Empregos, for Portuguese job vacancies.
- Remotive, for international remote jobs.
- Arbeitnow, for European and remote jobs.

## Main technologies

- Python
- Streamlit
- Gemini API
- requests
- BeautifulSoup
- CSV-based persistence
- Rule-based filtering
- LLM-based job matching

## Project structure

```text
.
├── app.py
├── agent.py
├── candidate_profile.example.md
├── requirements.txt
├── .env.example
├── .gitignore
└── sources/
    ├── __init__.py
    ├── arbeitnow.py
    ├── international.py
    ├── netempregos.py
    ├── portugal.py
    └── remotive.py
```

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file based on `.env.example`:

```text
GEMINI_API_KEY=your_api_key_here
```

Create your private candidate profile:

```bash
copy candidate_profile.example.md candidate_profile.md
```

Edit `candidate_profile.md` with the real candidate information. This file is intentionally ignored by Git because it may contain personal data.

## Run

```bash
streamlit run app.py
```

## Notes

This is a working MVP, not a finished recruitment platform. The goal is to demonstrate a practical AI-agent workflow:

```text
job sources → rule-based filtering → LLM evaluation → structured history → ranking
```

The project avoids storing API keys and personal profile data in the repository.

## Portfolio description

Developed a Python-based AI job search agent using Streamlit, Gemini API, automated vacancy collection, rule-based pre-filtering and LLM-based candidate-job matching.
