import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Callable

import streamlit as st

from agent import analyse_job
from sources.international import procurar_vagas_internacionais
from sources.portugal import procurar_vagas_portugal


st.set_page_config(
    page_title="JobRadar AI Job Agent",
    page_icon="⚡",
    layout="wide",
)


HISTORY_FILE = Path("analysed_jobs.csv")
MAX_AUTOMATIC_ANALYSES = 50


CSV_FIELDS = [
    "date",
    "title",
    "company",
    "location",
    "link",
    "classification",
    "compatibility",
    "area",
    "level",
    "recommended_cv",
    "description",
    "analysis",
]


def ensure_compatible_csv() -> None:
    if not HISTORY_FILE.exists():
        return

    with open(HISTORY_FILE, mode="r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        header = next(reader, None)

    if header != CSV_FIELDS:
        backup_date = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = Path(f"analysed_jobs_backup_{backup_date}.csv")
        HISTORY_FILE.rename(backup_file)


def extract_field(text: str, field_name: str) -> str:
    pattern = rf"^{field_name}:\s*(.+)$"
    result = re.search(pattern, text, flags=re.MULTILINE)

    if result:
        return result.group(1).strip()

    return ""


def extract_compatibility(text: str) -> int:
    value = extract_field(text, "COMPATIBILIDADE")
    result = re.search(r"\d+", value)

    if result:
        return int(result.group(0))

    return 0


def remove_technical_block(text: str) -> str:
    index = text.find("# Análise da vaga")

    if index != -1:
        return text[index:].strip()

    return text.strip()


def save_job(
    title: str,
    company: str,
    location: str,
    link: str,
    description: str,
    analysis: str,
) -> None:
    ensure_compatible_csv()

    file_exists = HISTORY_FILE.exists()

    classification = extract_field(analysis, "CLASSIFICACAO")
    compatibility = extract_compatibility(analysis)
    area = extract_field(analysis, "AREA")
    level = extract_field(analysis, "NIVEL")
    recommended_cv = extract_field(analysis, "CV_RECOMENDADO")

    with open(HISTORY_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": title,
            "company": company,
            "location": location,
            "link": link,
            "classification": classification,
            "compatibility": compatibility,
            "area": area,
            "level": level,
            "recommended_cv": recommended_cv,
            "description": description,
            "analysis": analysis,
        })


def read_history() -> list[dict]:
    ensure_compatible_csv()

    if not HISTORY_FILE.exists():
        return []

    with open(HISTORY_FILE, mode="r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)


def load_saved_links() -> set[str]:
    history = read_history()
    links = set()

    for job in history:
        link = job.get("link", "").strip()

        if link:
            links.add(link)

    return links


def classification_symbol(classification: str) -> str:
    classification = classification.upper()

    if "CANDIDATAR AGORA" in classification:
        return "🟢"

    if "CANDIDATAR COM CUIDADO" in classification:
        return "🟡"

    if "GUARDAR" in classification:
        return "🔵"

    if "FORMAÇÃO" in classification:
        return "🟠"

    if "IGNORAR" in classification:
        return "🔴"

    return "⚪"


def build_job_text(
    title: str,
    company: str,
    location: str,
    link: str,
    description: str,
) -> str:
    return f"""
TITLE:
{title}

COMPANY:
{company}

LOCATION / WORK MODEL:
{location}

LINK:
{link}

DESCRIPTION:
{description}
"""


def prepare_automatic_job_description(job: dict) -> str:
    return f"""
SOURCE:
{job.get("fonte", "")}

CATEGORY:
{job.get("categoria", "")}

TYPE:
{job.get("tipo", "")}

SALARY:
{job.get("salario", "")}

PUBLICATION DATE:
{job.get("data_publicacao", "")}

LOCATION COMPATIBILITY:
{job.get("compatibilidade_local", "")}

PRE-FILTER SCORE:
{job.get("score_pre_filtro", "")}

FINAL SCORE:
{job.get("score_final", "")}

SEARCH TERM:
{job.get("termo_pesquisa", "")}

DESCRIPTION:
{job.get("descricao", "")}
"""


def analyse_and_save_job(
    title: str,
    company: str,
    location: str,
    link: str,
    description: str,
) -> str:
    job_text = build_job_text(
        title=title,
        company=company,
        location=location,
        link=link,
        description=description,
    )

    result = analyse_job(job_text)

    save_job(
        title=title,
        company=company,
        location=location,
        link=link,
        description=description,
        analysis=result,
    )

    return result


def show_result(result: str) -> None:
    classification = extract_field(result, "CLASSIFICACAO")
    compatibility = extract_compatibility(result)
    area = extract_field(result, "AREA")
    level = extract_field(result, "NIVEL")
    recommended_cv = extract_field(result, "CV_RECOMENDADO")

    st.success("Job analysed and saved.")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.metric("Compatibility", f"{compatibility}/100")

    with col_b:
        st.metric("Classification", classification)

    with col_c:
        st.metric("Level", level)

    st.write(f"**Area:** {area}")
    st.write(f"**Recommended CV:** {recommended_cv}")

    st.divider()
    st.markdown(remove_technical_block(result))


def process_automatic_search(
    search_name: str,
    search_function: Callable[[], list[dict]],
    analysis_limit: int,
) -> None:
    with st.spinner(f"Searching jobs: {search_name}..."):
        try:
            found_jobs = search_function()
        except Exception as error:
            st.error(f"Error searching jobs in: {search_name}")
            st.code(str(error))
            return

    if not found_jobs:
        st.warning("No jobs passed the pre-filter.")
        return

    st.success(f"{len(found_jobs)} jobs passed the pre-filter.")

    jobs_to_analyse = found_jobs[:int(analysis_limit)]
    saved_links = load_saved_links()
    automatic_results = []

    total = len(jobs_to_analyse)
    progress = st.progress(0)

    for index, job in enumerate(jobs_to_analyse, start=1):
        title = job.get("titulo", "Untitled")
        company = job.get("empresa", "Unknown company")
        location = job.get("local", "")
        link = job.get("link", "").strip()
        description = prepare_automatic_job_description(job)

        progress.progress(index / total)

        if link and link in saved_links:
            automatic_results.append({
                "status": "SKIPPED — already in history",
                "title": title,
                "company": company,
                "location": location,
                "link": link,
                "compatibility": "",
                "classification": "",
                "area": "",
                "level": "",
                "recommended_cv": "",
            })
            continue

        with st.spinner(f"Analysing {index}/{total}: {title}"):
            try:
                result = analyse_and_save_job(
                    title=title,
                    company=company,
                    location=location,
                    link=link,
                    description=description,
                )

                if link:
                    saved_links.add(link)

                automatic_results.append({
                    "status": "ANALYSED",
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": link,
                    "compatibility": extract_compatibility(result),
                    "classification": extract_field(result, "CLASSIFICACAO"),
                    "area": extract_field(result, "AREA"),
                    "level": extract_field(result, "NIVEL"),
                    "recommended_cv": extract_field(result, "CV_RECOMENDADO"),
                })

            except Exception as error:
                automatic_results.append({
                    "status": f"ERROR — {error}",
                    "title": title,
                    "company": company,
                    "location": location,
                    "link": link,
                    "compatibility": "",
                    "classification": "",
                    "area": "",
                    "level": "",
                    "recommended_cv": "",
                })

    st.success("Automatic search and analysis finished.")
    st.write("### Automatic analysis results")

    sorted_results = sorted(
        automatic_results,
        key=lambda item: int(item.get("compatibility") or 0),
        reverse=True,
    )

    for item in sorted_results:
        compatibility = item.get("compatibility", "")
        classification = item.get("classification", "")
        title = item.get("title", "")
        company = item.get("company", "")
        status = item.get("status", "")
        area = item.get("area", "")
        level = item.get("level", "")
        recommended_cv = item.get("recommended_cv", "")
        location = item.get("location", "")
        link = item.get("link", "")

        if compatibility != "":
            expander_title = f"{compatibility}/100 — {classification} — {title} — {company}"
        else:
            expander_title = f"—/100 — {status} — {title} — {company}"

        with st.expander(expander_title):
            st.write(f"**Status:** {status}")
            st.write(f"**Company:** {company}")
            st.write(f"**Location:** {location}")
            st.write(f"**Compatibility:** {compatibility}/100" if compatibility != "" else "**Compatibility:** —")
            st.write(f"**Classification:** {classification if classification else '—'}")
            st.write(f"**Area:** {area if area else '—'}")
            st.write(f"**Level:** {level if level else '—'}")
            st.write(f"**Recommended CV:** {recommended_cv if recommended_cv else '—'}")

            if link:
                st.write(f"**Link:** {link}")


# Interface

st.title("⚡ JobRadar AI Job Agent")

st.write(
    "Searches, filters and analyses job vacancies in Electrical Engineering, "
    "automation, infrastructure, technical support, construction support, maintenance and related areas."
)


st.divider()
st.subheader("🔎 Automatic job search")

st.write(
    "Choose the source. JobRadar searches vacancies, applies Python pre-filters, "
    "sends the filtered jobs to Gemini and saves the result in the history file."
)

analysis_limit = st.number_input(
    "Maximum number of jobs to analyse automatically",
    min_value=1,
    max_value=100,
    value=MAX_AUTOMATIC_ANALYSES,
    step=1,
)

col_portugal, col_international = st.columns(2)

with col_portugal:
    search_portugal = st.button(
        "🇵🇹 Search and analyse Portugal / Net-Empregos",
        type="primary",
        use_container_width=True,
    )

with col_international:
    search_international = st.button(
        "🌍 Search and analyse international/remote jobs",
        type="secondary",
        use_container_width=True,
    )

if search_portugal:
    process_automatic_search(
        search_name="Portugal / Net-Empregos",
        search_function=procurar_vagas_portugal,
        analysis_limit=int(analysis_limit),
    )

if search_international:
    process_automatic_search(
        search_name="International / Remote",
        search_function=procurar_vagas_internacionais,
        analysis_limit=int(analysis_limit),
    )


st.divider()
st.subheader("✍️ Manual job analysis")

col_input, col_output = st.columns([1, 1])

with col_input:
    st.write("Paste a manually found job vacancy here.")

    title = st.text_input("Job title", placeholder="Example: Electrical Engineer")
    company = st.text_input("Company", placeholder="Example: Company name")
    location = st.text_input("Location / work model", placeholder="Example: Lisbon / Hybrid / Remote")
    link = st.text_input("Job link", placeholder="https://...")
    description = st.text_area("Full job description", height=380, placeholder="Paste the full job description here...")

    analyse_manual = st.button("Analyse and save manual job", type="secondary")

with col_output:
    st.subheader("Manual analysis result")

    if analyse_manual:
        if not description.strip():
            st.warning("Paste the job description first.")
        else:
            with st.spinner("Analysing with Gemini..."):
                try:
                    result = analyse_and_save_job(
                        title=title,
                        company=company,
                        location=location,
                        link=link,
                        description=description,
                    )
                    show_result(result)

                except Exception as error:
                    st.error("An error occurred while analysing the job.")
                    st.code(str(error))
    else:
        st.info("Fill in the job fields and click analyse.")


st.divider()
st.subheader("📁 Analysed jobs history")

history = read_history()

if not history:
    st.info("There are no saved job analyses yet.")
else:
    st.write(f"History file: `{HISTORY_FILE}`")

    sorted_history = sorted(
        history,
        key=lambda job: int(job.get("compatibility") or 0),
        reverse=True,
    )

    for job in sorted_history[:100]:
        title = job.get("title", "Untitled")
        company = job.get("company", "Unknown company")
        date = job.get("date", "")
        location = job.get("location", "")
        link = job.get("link", "")
        classification = job.get("classification", "")
        compatibility = job.get("compatibility", "0")
        area = job.get("area", "")
        level = job.get("level", "")
        recommended_cv = job.get("recommended_cv", "")

        symbol = classification_symbol(classification)
        expander_title = f"{symbol} {compatibility}/100 — {classification} — {title} — {company}"

        with st.expander(expander_title):
            st.write(f"**Date:** {date}")
            st.write(f"**Location/work model:** {location}")
            st.write(f"**Area:** {area}")
            st.write(f"**Level:** {level}")
            st.write(f"**Recommended CV:** {recommended_cv}")

            if link:
                st.write(f"**Link:** {link}")

            st.write("**Full analysis:**")
            st.markdown(remove_technical_block(job.get("analysis", "")))
