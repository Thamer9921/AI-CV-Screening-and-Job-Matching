from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from agents.cv_agent import clean_text, extract_skills
from agents.job_agent import get_job_text
from database.vector_agent import build_job_index, search_jobs


def tfidf_scores(cv_text, jobs):
    """Use one shared vocabulary for all jobs in this analysis."""
    documents = [clean_text(cv_text)]
    documents.extend(clean_text(get_job_text(job)) for job in jobs)

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        stop_words="english",
    )

    try:
        matrix = vectorizer.fit_transform(documents)
    except ValueError as exc:
        if "empty vocabulary" in str(exc).lower():
            return [0.0] * len(jobs)
        raise

    return cosine_similarity(matrix[0:1], matrix[1:]).ravel().tolist()


def skill_match_score(cv_skills, job_text):
    required = set(extract_skills(job_text))
    available = set(cv_skills)

    # Avoid counting a generic term again beside its specific skill.
    for specific, generic in (
        ("oop", "programming"),
        ("rest api", "api"),
        ("network security", "networking"),
    ):
        if specific in required:
            required.discard(generic)

    matched = sorted(required & available)
    missing = sorted(required - available)

    score = 100.0 * len(matched) / len(required) if required else None
    return score, matched, missing


def preference_score(job, preferences=None):
    preferences = preferences or {}
    points = 0
    reasons = []

    fields = (
        ("preferred_location", "location", 10, "Location"),
        ("job_type", "job_type", 8, "Job type"),
        ("field_of_interest", "field", 12, "Field"),
    )

    for preference_key, job_key, weight, label in fields:
        wanted = str(preferences.get(preference_key) or "").strip().casefold()
        actual = str(job.get(job_key) or "").strip().casefold()

        if wanted in ("", "any"):
            continue

        matches = wanted == actual
        if preference_key == "preferred_location" and wanted == "remote":
            matches = (
                str(job.get("work_mode") or "").casefold() == "remote"
                or actual == "remote"
            )

        if matches:
            points += weight
            reasons.append(label)

    return points, reasons


def analyze_all_jobs(cv_data, jobs, preferences=None):
    if not jobs:
        return []

    cv_text = str(cv_data.get("text") or "").strip()
    if not cv_text:
        raise ValueError("The CV contains no readable text.")

    index, _ = build_job_index(jobs)
    candidates = search_jobs(cv_text, jobs, index)
    lexical_scores = tfidf_scores(cv_text, candidates)
    results = []

    for job, lexical in zip(candidates, lexical_scores):
        skill_score, matched, missing = skill_match_score(
            cv_data.get("skills", []),
            get_job_text(job),
        )

        semantic = max(0.0, min(1.0, job["semantic_similarity"])) * 100
        lexical = max(0.0, min(1.0, float(lexical))) * 100

        # Heuristic weights; these require evaluation on labelled examples.
        if skill_score is None:
            match_score = 0.75 * semantic + 0.25 * lexical
            basis = "Text similarity only: no known job skills detected."
        else:
            match_score = (
                0.25 * semantic
                + 0.15 * lexical
                + 0.60 * skill_score
            )
            basis = "60% skills + 25% semantic + 15% lexical similarity."

        preference_points, preference_matches = preference_score(
            job, preferences
        )

        # Preferences affect ranking but not the displayed match score.
        ranking_score = match_score + preference_points

        results.append({
            **job,
            "semantic_score": round(semantic, 2),
            "similarity_score": round(lexical, 2),
            "skill_score": (
                round(skill_score, 2) if skill_score is not None else None
            ),
            "final_score": round(match_score, 2),
            "preference_points": preference_points,
            "preference_matches": preference_matches,
            "ranking_score": round(ranking_score, 2),
            "matched_skills": matched,
            "missing_skills": missing,
            "score_basis": basis,
        })

    return sorted(
        results,
        key=lambda result: (
            -result["ranking_score"],
            -result["final_score"],
            result["id"],
        ),
    )