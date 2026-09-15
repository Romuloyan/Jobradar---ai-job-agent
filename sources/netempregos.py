import re
import time
from html import unescape
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.net-empregos.com"


SEARCH_TERMS = [
    "engenheiro eletrotécnico",
    "engenheiro electrotécnico",
    "engenharia eletrotécnica",
    "engenharia electrotécnica",
    "automação industrial",
    "técnico eletrotécnica",
    "instalações elétricas",
    "fiscalização eletrotécnica",
    "manutenção industrial eletrotécnica",
    "mobilidade elétrica",
    "quadros elétricos",
    "projetista eletrotécnico",
]


FIXED_PAGES = [
    "https://www.net-empregos.com/engenheiro-eletrotecnico/",
    "https://www.net-empregos.com/engenharia-eletrotecnico/",
    "https://www.net-empregos.com/emprego-engenharia-eletrotecnica.asp",
]


GOOD_TERMS = [
    "eletrotécnico",
    "electrotécnico",
    "eletrotecnico",
    "electrotecnico",
    "engenheiro eletrotécnico",
    "engenheiro electrotécnico",
    "engenharia eletrotécnica",
    "engenharia electrotécnica",
    "automação",
    "automação industrial",
    "controlo",
    "controle",
    "plc",
    "scada",
    "manutenção industrial",
    "instalações elétricas",
    "instalações eléctricas",
    "quadros elétricos",
    "quadros eléctricos",
    "mobilidade elétrica",
    "mobilidade eléctrica",
    "energia",
    "fotovoltaico",
    "solar",
    "renováveis",
    "fiscalização",
    "obra",
    "direção de obra",
    "direcção de obra",
    "orçamentista",
    "projetista",
    "projectista",
    "instrumentação",
    "comissionamento",
    "comissioning",
    "técnico superior",
    "júnior",
    "junior",
    "estágio",
    "iefp",
]


BAD_TERMS = [
    "comercial puro",
    "call center",
    "marketing",
    "sales",
    "vendedor",
    "loja",
    "retalho",
    "programador senior",
    "developer senior",
    "full stack",
    "frontend",
    "backend",
    "php",
    "react",
    "java developer",
    "data scientist",
    "contabilidade",
    "financeiro",
    "recursos humanos",
]


GOOD_AREAS = [
    "lisboa",
    "oeiras",
    "amadora",
    "loures",
    "odivelas",
    "sintra",
    "cascais",
    "alverca",
    "vila franca de xira",
    "almada",
    "seixal",
    "barreiro",
    "setúbal",
    "setubal",
    "santarém",
    "santarem",
    "remoto",
    "híbrido",
    "hibrido",
    "teletrabalho",
]


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    return session


def clean_html(html_text: str) -> str:
    if not html_text:
        return ""

    soup = BeautifulSoup(html_text, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text("\n")
    text = unescape(text)

    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]

    return "\n".join(lines)


def normalise_text(text: str) -> str:
    return text.lower().strip()


def is_login_or_blocked_page(response: requests.Response) -> bool:
    final_url = response.url.lower()
    text = response.text.lower()

    if "loginc.asp" in final_url:
        return True

    if "login de candidato" in text:
        return True

    if "email ou login" in text and "password" in text:
        return True

    return False


def get_html(session: requests.Session, url: str) -> str:
    response = session.get(url, timeout=8)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"

    if is_login_or_blocked_page(response):
        raise RuntimeError(f"Net-Empregos returned a login or blocked page: {response.url}")

    return response.text


def build_search_url(term: str, page: int) -> str:
    params = {"chaves": term, "page": page}
    return f"{BASE_URL}/pesquisa-empregos.asp?{urlencode(params)}"


def build_listing_urls(pages_per_term: int = 2) -> list[str]:
    urls = []

    for base_url in FIXED_PAGES:
        for page in range(1, pages_per_term + 1):
            separator = "&" if "?" in base_url else "?"
            urls.append(f"{base_url}{separator}page={page}")

    for term in SEARCH_TERMS:
        for page in range(1, pages_per_term + 1):
            urls.append(build_search_url(term, page))

    return urls


def extract_job_links(html: str, origin_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()

        if not href:
            continue

        url = urljoin(origin_url, href)

        if re.search(r"net-empregos\.com/\d{6,}/", url):
            links.append(url)
            continue

        reference_match = re.search(r"REF=(\d{6,})", url, flags=re.IGNORECASE)
        if reference_match:
            reference = reference_match.group(1)
            links.append(f"{BASE_URL}/{reference}/")

    result = []
    seen = set()

    for link in links:
        if link in seen:
            continue

        result.append(link)
        seen.add(link)

    return result


def extract_title(soup: BeautifulSoup, clean_text: str, url: str) -> str:
    for selector in ["h1", "h2", "title"]:
        tag = soup.find(selector)

        if tag:
            title = tag.get_text(" ", strip=True)

            if title:
                return title.replace("Net-Empregos", "").strip(" -|")

    parts = url.rstrip("/").split("/")

    if len(parts) >= 2:
        slug = parts[-1].replace("-", " ").strip()

        if slug:
            return slug.title()

    lines = clean_text.splitlines()

    if lines:
        return lines[0][:120]

    return "Untitled"


def extract_reference(url: str, text: str) -> str:
    url_match = re.search(r"net-empregos\.com/(\d{6,})/", url)

    if url_match:
        return url_match.group(1)

    text_match = re.search(r"Ref[:\s]+(\d{6,})", text, flags=re.IGNORECASE)

    if text_match:
        return text_match.group(1)

    return ""


def extract_location(text: str) -> str:
    lines = text.splitlines()

    for line in lines[:40]:
        line_lower = line.lower()

        for area in GOOD_AREAS:
            if area in line_lower:
                return line.strip()

    return ""


def extract_company(text: str) -> str:
    lines = text.splitlines()

    for index, line in enumerate(lines[:80]):
        if "engenharia" in line.lower() or "ref:" in line.lower():
            candidates = lines[index + 1:index + 5]

            for candidate in candidates:
                if len(candidate) > 3 and "detalhe da oferta" not in candidate.lower():
                    return candidate[:120]

    return ""


def calculate_pre_filter_score(job: dict) -> int:
    title = normalise_text(job.get("titulo", ""))
    description = normalise_text(job.get("descricao", ""))
    location = normalise_text(job.get("local", ""))

    full_text = f"{title} {location} {description}"
    score = 0

    for term in GOOD_TERMS:
        if term in title:
            score += 6
        elif term in location:
            score += 3
        elif term in description:
            score += 1

    for area in GOOD_AREAS:
        if area in full_text:
            score += 3

    for term in BAD_TERMS:
        if term in title:
            score -= 8
        elif term in description:
            score -= 3

    if "sénior" in title or "senior" in title:
        score -= 5

    if "diretor" in title or "director" in title:
        score -= 5

    if "chefe" in title:
        score -= 4

    if "júnior" in title or "junior" in title:
        score += 6

    if "estágio" in title or "iefp" in full_text:
        score += 4

    return score


def job_passes_pre_filter(job: dict) -> bool:
    score = calculate_pre_filter_score(job)
    job["score_pre_filtro"] = score

    title = normalise_text(job.get("titulo", ""))
    description = normalise_text(job.get("descricao", ""))
    full_text = f"{title} {description}"

    has_area_signal = any(
        term in full_text
        for term in [
            "eletrotécnico",
            "electrotécnico",
            "eletrotecnico",
            "electrotecnico",
            "automação",
            "plc",
            "scada",
            "instalações elétricas",
            "quadros elétricos",
            "mobilidade elétrica",
            "energia",
            "fotovoltaico",
            "manutenção industrial",
            "instrumentação",
        ]
    )

    return has_area_signal and score >= 4


def get_job_detail(session: requests.Session, url: str) -> dict | None:
    try:
        html = get_html(session, url)
    except Exception as error:
        print(f"Error opening job detail: {url} | {error}")
        return None

    soup = BeautifulSoup(html, "html.parser")
    clean_text = clean_html(html)

    title = extract_title(soup, clean_text, url)
    reference = extract_reference(url, clean_text)
    location = extract_location(clean_text)
    company = extract_company(clean_text)

    job = {
        "fonte": "Net-Empregos",
        "id_fonte": reference,
        "titulo": title,
        "empresa": company,
        "local": location,
        "link": url,
        "categoria": "Portugal / Net-Empregos",
        "tipo": "",
        "salario": "",
        "data_publicacao": "",
        "descricao": clean_text,
        "termo_pesquisa": "Net-Empregos",
        "compatibilidade_local": "PORTUGAL",
    }

    if job_passes_pre_filter(job):
        return job

    return None


def procurar_vagas_netempregos(
    paginas_por_termo: int = 2,
    limite_total: int = 50,
    pausa_segundos: float = 0.8,
) -> list[dict]:
    session = create_session()
    listing_urls = build_listing_urls(pages_per_term=paginas_por_termo)

    job_links = []
    seen_links = set()

    for index, url in enumerate(listing_urls, start=1):
        print(f"Reading listing {index}/{len(listing_urls)}: {url}")

        try:
            html = get_html(session, url)
            links = extract_job_links(html, url)

            for link in links:
                if link in seen_links:
                    continue

                job_links.append(link)
                seen_links.add(link)

            time.sleep(pausa_segundos)

        except Exception as error:
            print(f"Listing error: {url} | {error}")

    results = []
    seen_references = set()

    for index, link in enumerate(job_links, start=1):
        if len(results) >= limite_total:
            break

        print(f"Reading detail {index}/{len(job_links)}: {link}")
        job = get_job_detail(session, link)

        if not job:
            time.sleep(pausa_segundos)
            continue

        reference = job.get("id_fonte") or job.get("link")

        if reference in seen_references:
            continue

        results.append(job)
        seen_references.add(reference)
        time.sleep(pausa_segundos)

    results.sort(key=lambda job: job.get("score_pre_filtro", 0), reverse=True)
    return results


if __name__ == "__main__":
    vacancies = procurar_vagas_netempregos(
        paginas_por_termo=1,
        limite_total=10,
        pausa_segundos=0.2,
    )

    print(f"Net-Empregos jobs after pre-filter: {len(vacancies)}")

    for vacancy in vacancies[:30]:
        print("-" * 80)
        print(f"Score: {vacancy.get('score_pre_filtro')}")
        print(f"Title: {vacancy.get('titulo')}")
        print(f"Company: {vacancy.get('empresa')}")
        print(f"Location: {vacancy.get('local')}")
        print(f"Reference: {vacancy.get('id_fonte')}")
        print(f"Link: {vacancy.get('link')}")
