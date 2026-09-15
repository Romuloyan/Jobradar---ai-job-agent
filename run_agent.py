from agent import analyse_job


sample_job = """
Electrical Engineering Assistant - Lisbon

Engineering company looking for support in electrical installations projects,
site follow-up, measurements, budgeting and technical documentation.

Requirements:
- Degree in Electrical Engineering or similar area.
- AutoCAD knowledge valued.
- Organisation skills.
- Good communication.
- Willingness to learn.
- Availability for on-site work in Lisbon.

Previous professional experience, client-facing skills and responsibility are valued.
"""


if __name__ == "__main__":
    result = analyse_job(sample_job)

    print("\n" + "=" * 40)
    print(" JOB ANALYSIS RESULT")
    print("=" * 40 + "\n")
    print(result)
