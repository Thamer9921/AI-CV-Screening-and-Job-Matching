from copy import deepcopy

from data.sample_jobs import SAMPLE_JOBS


def validate_job(job):
    """Validate the fields needed by the matching pipeline."""
    required_fields = (
        "id",
        "title",
        "company",
        "location",
        "job_type",
        "work_mode",
        "field",
        "description",
        "url",
        "source",
        "is_demo",
    )

    missing = [field for field in required_fields if field not in job]
    if missing:
        raise ValueError(f"Missing job fields: {', '.join(missing)}")

    for field in required_fields:
        if field == "is_demo":
            continue

        if not isinstance(job[field], str):
            raise ValueError(f"Job field '{field}' must be text.")

    for field in ("id", "title", "description"):
        if not job[field].strip():
            raise ValueError(f"Job field '{field}' cannot be empty.")

    if not isinstance(job["is_demo"], bool):
        raise ValueError("Job field 'is_demo' must be True or False.")


def load_jobs():
    """Return independent copies of the demo jobs."""
    jobs = deepcopy(SAMPLE_JOBS)
    seen_ids = set()

    for job in jobs:
        validate_job(job)

        if job["id"] in seen_ids:
            raise ValueError(f"Duplicate job ID: {job['id']}")

        seen_ids.add(job["id"])

    return jobs


def get_job_text(job):
    """Build the text used for job similarity and skill extraction."""
    title = job.get("title", "").strip()
    description = job.get("description", "").strip()
    return f"{title}\n{description}".strip()