from datetime import datetime


def calculate_risk_level(student) -> tuple[str, str]:
    """
    Returns (level, reason) where level is 'critical', 'warning', 'info', or 'ok'
    """
    today = datetime.now().date()
    credits_earned = student["credits_earned"]
    credits_expected = student["credits_expected"]
    credits_remaining = 240 - credits_earned
    valid_until = student["valid_until"]
    if isinstance(valid_until, str):
        valid_until = datetime.strptime(valid_until, "%Y-%m-%d").date()
    months_left = (valid_until - today).days / 30
    months_needed = credits_remaining / 5
    buffer_months = months_left - months_needed
    completion_rate = credits_earned / credits_expected if credits_expected > 0 else 1.0

    if completion_rate < 0.5 and buffer_months < -6:
        return "critical", f"completed only {round(completion_rate*100)}% of expected credits and may not finish before study right expires"
    elif buffer_months < -12:
        return "critical", f"study right ends too soon — needs {round(months_needed)} more months but only {round(months_left)} months remaining"
    elif completion_rate < 0.5:
        return "warning", f"completed only {round(completion_rate*100)}% of expected credits — falling behind schedule"
    elif buffer_months < -6:
        return "warning", f"at current pace may not finish before study right expires"
    elif completion_rate < 0.75 or buffer_months < 0:
        return "info", f"slightly behind expected pace, worth checking in"
    else:
        return "ok", ""