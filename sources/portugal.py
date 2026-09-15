from sources.netempregos import procurar_vagas_netempregos


def normalise_score(job: dict) -> int:
    try:
        return int(job.get("score_pre_filtro", 0))
    except ValueError:
        return 0


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


def procurar_vagas_portugal() -> list[dict]:
    all_jobs = []

    print("Searching Net-Empregos...")

    netempregos_jobs = procurar_vagas_netempregos(
        paginas_por_termo=2,
        limite_total=50,
        pausa_segundos=0.5,
    )

    all_jobs.extend(netempregos_jobs)
    all_jobs = remove_duplicates(all_jobs)
    all_jobs.sort(key=normalise_score, reverse=True)

    return all_jobs


if __name__ == "__main__":
    vacancies = procurar_vagas_portugal()
    print(f"Portugal jobs found: {len(vacancies)}")

    for vacancy in vacancies[:50]:
        print("-" * 80)
        print(f"Score: {vacancy.get('score_pre_filtro')}")
        print(f"Source: {vacancy.get('fonte')}")
        print(f"Title: {vacancy.get('titulo')}")
        print(f"Company: {vacancy.get('empresa')}")
        print(f"Location: {vacancy.get('local')}")
        print(f"Reference: {vacancy.get('id_fonte')}")
        print(f"Link: {vacancy.get('link')}")
