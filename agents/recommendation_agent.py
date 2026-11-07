def generate_recommendations(match_results, top_n=3):
    """Explain ranked results without changing their order."""
    recommendations = []

    for job in match_results[:max(0, int(top_n))]:
        matched = job.get("matched_skills", [])
        missing = job.get("missing_skills", [])
        score = job["final_score"]
        skill_score = job.get("skill_score")

        # Descriptive thresholds, not validated hiring decisions.
        if score >= 75:
            fit_label = "Strong Match"
        elif score >= 50:
            fit_label = "Moderate Match"
        else:
            fit_label = "Limited Match"

        if skill_score is None:
            reason = (
                "No skills from the current vocabulary were detected "
                "in this job. The score uses text similarity only."
            )
            tip = "Review the job requirements manually."
        else:
            if matched:
                reason = (
                    "Your profile contains these detected job skills: "
                    + ", ".join(matched[:8])
                    + "."
                )
            else:
                reason = (
                    "No overlap was detected between your profile "
                    "skills and the recognised job skills."
                )

            if missing:
                tip = (
                    "These job skills were not detected in your profile: "
                    + ", ".join(missing[:8])
                    + ". Add supporting experience if you have it, "
                    "or consider learning them."
                )
            else:
                tip = (
                    "All recognised job skills appear in your profile. "
                    "Review experience, qualifications, and other "
                    "requirements separately."
                )

        preference_matches = job.get("preference_matches", [])
        preference_reason = (
            "Matching preferences: " + ", ".join(preference_matches) + "."
            if preference_matches
            else "No preference bonus applied."
        )

        recommendations.append({
            **job,
            "fit_label": fit_label,
            "reason": reason,
            "tip": tip,
            "preference_reason": preference_reason,
        })

    return recommendations