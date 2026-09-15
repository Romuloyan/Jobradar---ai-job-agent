from sources.arbeitnow import procurar_vagas_arbeitnow
from sources.remotive import procurar_vagas_remotive


def normalise_score(job: dict) -> int:
    try:
        return int(job.get("score_pre_filtro", 0))
    except ValueError:
        return 0


def classify_location(job: dict) -> str:
    """
    Accept only clearly remote or hybrid international jobs.
    On-site international jobs are excluded.
    """

    source = job.get("fonte", "").lower()
    title = job.get("titulo", "").lower()
    location = job.get("local", "").lower()
    remote_api = job.get("remote", False)

    # Do not use the full description to accept remote work.
    # Some job boards include generic text containing the word "remote".
    location_text = f"{title} {location}"

    remote_signals = [
        "worldwide",
        "anywhere",
        "global",
        "fully remote",
        "100% remote",
        "remote worldwide",
        "remote europe",
        "europe remote",
        "remote eu",
        "eu remote",
        "emea remote",
        "remote emea",
        "portugal remote",
        "remote from portugal",
        "deutschland remote",
        "remote uk",
        "remote united kingdom",
        "remote",
    ]

    hybrid_signals = [
        "hybrid",
        "híbrido",
        "hybride",
        "hybrid remote",
        "remote hybrid",
    ]

    if source == "remotive":
        if any(signal in location_text for signal in remote_signals):
            return "REMOTE COMPATIBLE"

    if remote_api is True:
        return "REMOTE COMPATIBLE"

    for signal in remote_signals:
        if signal in location_text:
            return "REMOTE COMPATIBLE"

    for signal in hybrid_signals:
        if signal in location_text:
            return "HYBRID COMPATIBLE"

    return "EXCLUDE"


def remove_duplicates(jobs: list[dict]) -> list[dict]:
    result = []
    seen_links = set()

    for job in jobs:
        link = job.get("link", "")

        if not link or link in seen_links:
            continue

        result.append(job)
        seen_links.add(link)

    return result


def final_international_score(job: dict) -> int:
    score = normalise_score(job)
    location_compatibility = job.get("compatibilidade_local", "")

    if location_compatibility == "REMOTE COMPATIBLE":
        score += 20
    elif location_compatibility == "HYBRID COMPATIBLE":
        score += 5

    return score


def filter_by_location(jobs: list[dict]) -> list[dict]:
    filtered_jobs = []

    for job in jobs:
        compatibility = classify_location(job)

        if compatibility == "EXCLUDE":
            continue

        job["compatibilidade_local"] = compatibility
        job["score_final"] = final_international_score(job)
        filtered_jobs.append(job)

    return filtered_jobs


def procurar_vagas_internacionais() -> list[dict]:
    all_jobs = []

    print("Searching Remotive...")
    all_jobs.extend(procurar_vagas_remotive(limite_por_termo=5))

    print("Searching Arbeitnow...")
    all_jobs.extend(procurar_vagas_arbeitnow(paginas=3, limite_total=30))

    all_jobs = remove_duplicates(all_jobs)
    all_jobs = filter_by_location(all_jobs)
    all_jobs.sort(key=lambda job: job.get("score_final", 0), reverse=True)

    return all_jobs


if __name__ == "__main__":
    vacancies = procurar_vagas_internacionais()
    print(f"International remote/hybrid jobs found: {len(vacancies)}")

    for vacancy in vacancies[:25]:
        print("-" * 80)
        print(f"Technical score: {vacancy.get('score_pre_filtro')}")
        print(f"Final score: {vacancy.get('score_final')}")
        print(f"Location compatibility: {vacancy.get('compatibilidade_local')}")
        print(f"Source: {vacancy.get('fonte')}")
        print(f"Title: {vacancy.get('titulo')}")
        print(f"Company: {vacancy.get('empresa')}")
        print(f"Location: {vacancy.get('local')}")
        print(f"Link: {vacancy.get('link')}")
