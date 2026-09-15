import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
PROJECT_DIR = Path(__file__).parent
PROFILE_FILE = PROJECT_DIR / "candidate_profile.md"


if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY. Create a .env file based on .env.example.")


client = genai.Client(api_key=API_KEY)


def read_text_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}. Copy candidate_profile.example.md to candidate_profile.md first."
        )

    return path.read_text(encoding="utf-8")


def load_candidate_profile() -> str:
    return read_text_file(PROFILE_FILE)


def create_job_analysis_prompt(candidate_profile: str, job_text: str) -> str:
    return f"""
You are a critical job vacancy evaluator for Electrical and Computer Engineering roles.

Your task is to analyse a job vacancy against the real candidate profile.

Mandatory rules:
- Write the answer in European Portuguese.
- Be direct and realistic.
- Do not invent skills.
- Do not exaggerate technical experience.
- Distinguish clearly between what the vacancy states and what is your inference.
- Avoid promotional language.
- Do not use words such as "perfeito", "ideal", "excelente", "perfeitamente", "totalmente" or "claramente" unless fully justified by the vacancy.
- Prefer cautious technical wording.
- Use "compatível" instead of "corresponde diretamente" unless the vacancy asks for exactly the same background or skill.
- Do not automatically reject vacancies that do not explicitly say "junior".
- Value previous professional experience where relevant.
- Distinguish general professional experience from formal engineering experience.
- Consider international remote roles when compatible.
- If information is missing from the vacancy, state that clearly.
- If the vacancy is weak for the candidate, say so.
- The compatibility score must always be shown as "85/100".
- In the market analysis section, write "Estimativa qualitativa sem consulta externa:" when no external market data was used.
- Do not present salaries, demand or progression as facts unless the vacancy provides that information or a source is available.

Return the answer exactly in this structure.

First, a technical block with these fields:

CLASSIFICACAO: CANDIDATAR AGORA / CANDIDATAR COM CUIDADO / GUARDAR PARA REVER / FORMAÇÃO ANTES DE CANDIDATAR / IGNORAR
COMPATIBILIDADE: number from 0 to 100
AREA: main vacancy area
NIVEL: Júnior / entrada / intermédio / sénior / pouco claro
CV_RECOMENDADO: geral / instalações-obra / automação-ia / manutenção-suporte / internacional-remoto

Then write the full analysis in Markdown:

# Análise da vaga

## Classificação final
...

## Compatibilidade
.../100

## Área principal da vaga
...

## Nível real da vaga
...

## Porque pode encaixar
- ...

## Riscos
- ...

## Requisitos que faltam
- ...

## Experiência anterior aproveitável
...

## Mercado e potencial
...

## CV recomendado
...

## Ação recomendada
...

## Resumo em 3 linhas
...

CANDIDATE PROFILE:
{candidate_profile}

JOB VACANCY:
{job_text}
"""


def analyse_job(job_text: str) -> str:
    if not job_text.strip():
        raise ValueError("The job vacancy text is empty.")

    candidate_profile = load_candidate_profile()
    prompt = create_job_analysis_prompt(
        candidate_profile=candidate_profile,
        job_text=job_text,
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    return response.text


# Portuguese alias kept for local compatibility with earlier versions.
def analisar_vaga(texto_vaga: str) -> str:
    return analyse_job(texto_vaga)
