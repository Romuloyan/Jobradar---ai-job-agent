import re
from html import unescape

import requests


URL_ARBEITNOW = "https://www.arbeitnow.com/api/job-board-api"


STRONG_TITLE_TERMS = [
    "electrical engineer",
    "electronics engineer",
    "automation engineer",
    "control systems engineer",
    "field service engineer",
    "technical support engineer",
    "application engineer",
    "commissioning engineer",
    "maintenance engineer",
    "facilities engineer",
    "data center technician",
    "data centre technician",
    "data center engineer",
    "data centre engineer",
    "hardware engineer",
    "infrastructure engineer",
    "it infrastructure engineer",
    "embedded engineer",
    "iot engineer",
    "simulation",
]


USEFUL_TERMS = [
    "electrical",
    "electronics",
    "automation",
    "control systems",
    "power systems",
    "energy",
    "hardware",
    "iot",
    "embedded",
    "commissioning",
    "maintenance",
    "facilities",
    "data center",
    "data centre",
    "diagnostics",
    "troubleshooting",
    "technical support",
    "infrastructure",
    "simulation",
]


BAD_TITLE_TERMS = [
    "account executive",
    "sales",
    "marketing",
    "copywriter",
    "writer",
    "finance",
    "financial controller",
    "accounting",
    "controlling",
    "buchhaltung",
    "retail",
    "commerce",
    "cto",
    "chief",
    "head of",
    "director",
    "manager",
    "architect",
    "senior",
    "lead",
    "principal",
    "react",
    "golang",
    "php",
    "ruby",
    "frontend",
    "backend",
    "full-stack",
    "full stack",
    "devops",
    "data scientist",
    "ml engineer",
    "machine learning",
]


BAD_DESCRIPTION_TERMS = [
    "sales quota",
    "pipeline generation",
    "account executive",
    "marketing campaign",
    "copywriting",
    "financial reporting",
    "bookkeeping",
]


def clean_html(html_text: str) -> str:
    if not html_text:
        return ""

    text = re.sub(r"<br\s*/?>", "\n", html_text)
    text = re.sub(r"</p>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)

    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]

    return "\n".join(lines)


def calculate_pre_filter_score(job: dict) -> int:
    title = job.get("titulo", "").lower()
    description = job.get("descricao", "").lower()
    tags = " ".join(job.get("tags", [])).lower()
    location = job.get("local", "").lower()

    full_text = f"{title} {description} {tags}"
    score = 0

    for term in BAD_TITLE_TERMS:
        if term in title:
            score -= 8

    for term in BAD_DESCRIPTION_TERMS:
        if term in description:
            score -= 4

    for term in STRONG_TITLE_TERMS:
        if term in title:
            score += 10

    for term in USEFUL_TERMS:
        if term in title:
            score += 5
        elif term in tags:
            score += 3
        elif term in description:
            score += 1

    if any(signal in location for signal in ["remote", "europe", "emea", "portugal", "germany", "spain", "france", "netherlands"]):
        score += 2

    if "software" in title and not any(
        term in full_text
        for term in ["hardware", "embedded", "iot", "automation", "electrical", "electronics", "control systems", "simulation"]
    ):
        score -= 8

    if "financial controller" in title or "controlling" in title or "accounting" in title:
        score -= 10

    if "werkstudent" in title or "working student" in title or "praxissemester" in title:
        score -= 6

    return score


def job_passes_pre_filter(job: dict) -> bool:
    score = calculate_pre_filter_score(job)
    job["score_pre_filtro"] = score

    title = job.get("titulo", "").lower()
    description = job.get("descricao", "").lower()
    full_text = f"{title} {description}"

    has_strong_signal = any(term in title for term in STRONG_TITLE_TERMS)
    has_real_technical_signal = any(
        term in full_text
        for term in [
            "electrical",
            "electronics",
            "automation",
            "control systems",
            "hardware",
            "embedded",
            "iot",
            "data center",
            "data centre",
            "facilities",
            "commissioning",
            "maintenance",
            "technical support",
            "infrastructure",
            "simulation",
        ]
    )

    if has_strong_signal and score >= 4:
        return True

    if has_real_technical_signal and score >= 6:
        return True

    return False


def procurar_vagas_arbeitnow(paginas: int = 3, limite_total: int = 30) -> list[dict]:
    results = []
    seen_links = set()

    for page in range(1, paginas + 1):
        try:
            response = requests.get(
                URL_ARBEITNOW,
                params={"page": page},
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()

            for job in data.get("data", []):
                link = job.get("url", "")

                if not link or link in seen_links:
                    continue

                tags = job.get("tags", [])

                normalised_job = {
                    "fonte": "Arbeitnow",
                    "id_fonte": str(job.get("slug", "")),
                    "titulo": job.get("title", ""),
                    "empresa": job.get("company_name", ""),
                    "local": job.get("location", ""),
                    "link": link,
                    "categoria": ", ".join(tags) if isinstance(tags, list) else str(tags),
                    "tipo": "",
                    "salario": "",
                    "data_publicacao": str(job.get("created_at", "")),
                    "descricao": clean_html(job.get("description", "")),
                    "termo_pesquisa": "local pre-filter",
                    "remote": job.get("remote", False),
                    "tags": tags if isinstance(tags, list) else [],
                }

                if job_passes_pre_filter(normalised_job):
                    results.append(normalised_job)
                    seen_links.add(link)

                if len(results) >= limite_total:
                    return sort_jobs(results)

        except Exception as error:
            print(f"Error searching Arbeitnow page {page}: {error}")

    return sort_jobs(results)


def sort_jobs(jobs: list[dict]) -> list[dict]:
    return sorted(jobs, key=lambda job: job.get("score_pre_filtro", 0), reverse=True)


if __name__ == "__main__":
    vacancies = procurar_vagas_arbeitnow(paginas=3, limite_total=30)
    print(f"Arbeitnow jobs after pre-filter: {len(vacancies)}")

    for vacancy in vacancies[:20]:
        print("-" * 80)
        print(f"Score: {vacancy.get('score_pre_filtro')}")
        print(f"Title: {vacancy.get('titulo')}")
        print(f"Company: {vacancy.get('empresa')}")
        print(f"Location: {vacancy.get('local')}")
        print(f"Remote API: {vacancy.get('remote')}")
        print(f"Link: {vacancy.get('link')}")
