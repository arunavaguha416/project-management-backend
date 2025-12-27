
def get_financial_year(date):
    """
    Returns financial year string (India format)
    Example:
      Apr 2024 → 2024-2025
      Feb 2025 → 2024-2025
    """
    if date.month >= 4:
        return f"{date.year}-{date.year + 1}"
    return f"{date.year - 1}-{date.year}"
