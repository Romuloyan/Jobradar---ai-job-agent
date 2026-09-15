import re
from html import unescape

import requests


URL_REMOTIVE = "https://remotive.com/api/remote-jobs"


SEARCH_TERMS = [
    "electrical engineer",
    "automation engineer",
    "energy engineer",
    "field engineer",
    "technical support engineer",
    "application engineer",
    "commissioning engineer",
    "data center engineer",
    "facilities engineer",
    "iot engineer",
    "hardware engineer",
    "maintenance engineer",
]


GOOD_TITLE_TERMS = [
    "electrical",
    "automation",
    "energy",
    "power",
    "field engineer",
    "field service",
    "technical support engineer",
    "support engineer",
    "application engineer",
    "commissioning",
    "data center",
    "data centre",
    "facilities",
    "iot",
    "hardware",
    "maintenance",
    "service desk engineer",
    "systems engineer",
]


GOOD_DESCRIPTION_TERMS = [
    "electrical",
    "electronics",
    "automation",
    "control systems",
    "power systems",
    "energy",
    "sensors",
    "actuators",
    "hardware",
    "iot",
    "maintenance",
    "technical support",
    "commissioning",
    "field service",
    "data center",
    "data centre",
    "facilities",
    "troubleshooting",
    "diagnostics",
]


BAD_TITLE_TERMS = [
    "marketing",
    "copywriter",
    "writer",
    "sales",
    "account executive",
    "head of",
    "react",
    "golang",
    "devops",
    "full-stack",
    "full stack",
    "frontend",
    "backend",
    "data engineer",
    "software developer",
    "software engineer",
    "architect",
]


BAD_CATEGORIES = [
    "marketing",
    "writing",
    "sales",
    "software development",
    "devops",
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


def location_looks_compatible(location: str) -> bool:
    if not location:
        return True

    location_lower = location.lower()

    good_signals = [
        "worldwide",
        "anywhere",
        "global",
        "remote",
        "europe",
        "emea",
        "eu",
        "european",
        "portugal",
        "spain",
        "uk",
        "united kingdom",
        "germany",
        "france",
        "netherlands",
        "ireland",
    ]

    bad_signals = [
        "us only",
        "usa only",
        "united states only",
        "u.s. only",
        "canada only",
        "north america only",
        "latam only",
        "americas only",
        "australia only",
        "new zealand only",
    ]

    for signal in bad_signals:
        if signal in location_lower:
            return False

    for signal in good_signals:
        if signal in location_lower:
            return True

    return True


def calculate_pre_filter_score(job: dict) -> int:
    title = job.get("titulo", "").lower()
    description = job.get("descricao", "").lower()
    category = job.get("categoria", "").lower()
    location = job.get("local", "").lower()

    score = 0

    for term in GOOD_TITLE_TERMS:
        if term in title:
            score += 4

    for term in GOOD_DESCRIPTION_TERMS:
        if term in description:
            score += 1

    if any(signal in location for signal in ["worldwide", "europe", "emea", "portugal", "remote"]):
        score += 2

    for bad_category in BAD_CATEGORIES:
        if bad_category in category:
            score -= 4

    for term in BAD_TITLE_TERMS:
        if term in title:
            score -= 6

    for seniority in ["senior", "lead", "principal"]:
        if seniority in title:
            score -= 4

    return score


def job_passes_pre_filter(job: dict) -> bool:
    score = calculate_pre_filter_score(job)
    job["score_pre_filtro"] = score

    title = job.get("titulo", "").lower()
    title_has_technical_signal = any(term in title for term in GOOD_TITLE_TERMS)

    if score >= 3:
        return True

    if title_has_technical_signal and score >= 1:
        return True

    return False


def search_remotive_by_term(term: str, limit: int = 10) -> list[dict]:
    response = requests.get(
        URL_REMOTIVE,
        params={"search": term, "limit": limit},
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()
    jobs = data.get("jobs", [])

    results = []

    for job in jobs:
        location = job.get("candidate_required_location", "Remote")

        if not location_looks_compatible(location):
            continue

        normalised_job = {
            "fonte": "Remotive",
            "id_fonte": str(job.get("id", "")),
            "titulo": job.get("title", ""),
            "empresa": job.get("company_name", ""),
            "local": location,
            "link": job.get("url", ""),
            "categoria": job.get("category", ""),
            "tipo": job.get("job_type", ""),
            "salario": job.get("salary", ""),
            "data_publicacao": job.get("publication_date", ""),
            "descricao": clean_html(job.get("description", "")),
            "termo_pesquisa": term,
            "remote": None,
        }

        if job_passes_pre_filter(normalised_job):
            results.append(normalised_job)

    return results


def procurar_vagas_remotive(limite_por_termo: int = 5) -> list[dict]:
    all_jobs = []
    seen_links = set()

    for term in SEARCH_TERMS:
        try:
            jobs = search_remotive_by_term(term=term, limit=limite_por_termo)

            for job in jobs:
                link = job.get("link", "")

                if not link or link in seen_links:
                    continue

                all_jobs.append(job)
                seen_links.add(link)

        except Exception as error:
            print(f"Error searching Remotive for '{term}': {error}")

    all_jobs.sort(key=lambda job: job.get("score_pre_filtro", 0), reverse=True)
    return all_jobs


if __name__ == "__main__":
    vacancies = procurar_vagas_remotive(limite_por_termo=5)
    print(f"Remotive jobs after pre-filter: {len(vacancies)}")

    for vacancy in vacancies[:20]:
        print("-" * 80)
        print(f"Score: {vacancy.get('score_pre_filtro')}")
        print(f"Title: {vacancy.get('titulo')}")
        print(f"Company: {vacancy.get('empresa')}")
        print(f"Location: {vacancy.get('local')}")
        print(f"Link: {vacancy.get('link')}")
