OPENROUTER_KEY_PREFIX = "sk-or-"


def validate_openrouter_key_format(api_key: str) -> tuple[bool, str]:
    cleaned = api_key.strip()
    if not cleaned:
        return False, "API key kosong."
    if "://" in cleaned or cleaned.startswith("http"):
        return (
            False,
            "Nilai nampak seperti URL, bukan OpenRouter API key. "
            "Guna key dari openrouter.ai/keys (format sk-or-v1-...).",
        )
    if not cleaned.startswith(OPENROUTER_KEY_PREFIX):
        return False, f"API key mesti bermula dengan '{OPENROUTER_KEY_PREFIX}'."
    if len(cleaned) < 20:
        return False, "API key terlalu pendek."
    return True, "Format key OK."
