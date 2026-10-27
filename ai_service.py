import os

def generate_health_remarks(patient):
    """
    Uses the Google Gemini API to generate cautious, non-diagnostic educational remarks.
    Returns (remarks, status). If no API key is configured or the request fails,
    returns an explicit status message instead of inventing an AI result.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return (
            "AI remarks unavailable: GEMINI_API_KEY is not configured. Add your key to .env and retry.",
            "GEMINI_API_KEY is not configured"
        )
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        prompt = f"""
You are writing brief educational health information, not diagnosing a patient.
Blood-test values supplied:
- Glucose: {patient['glucose']}
- Haemoglobin: {patient['haemoglobin']}
- Cholesterol: {patient['cholesterol']}

Write 2-4 concise sentences for a general audience:
1. Identify values that may merit review, but do not assume units or fasting status.
2. Explain that interpretation depends on laboratory reference ranges, units, age, symptoms,
   medications, fasting status, and clinical history.
3. Recommend discussing results with a qualified healthcare professional.
Do not diagnose a disease, calculate a disease probability, prescribe treatment, or make emergency
claims. Do not repeat the patient's name, date of birth, or email. Clearly label this as informational.
"""
        response = client.models.generate_content(model=model, contents=prompt)
        text = (getattr(response, "text", None) or "").strip()
        if not text:
            return ("AI returned no text. Please review the results with a healthcare professional.", "empty response")
        return ("AI informational remarks: " + text, "ok")
    except Exception as exc:
        # Keep the UI usable if the API key, network, quota, model or SDK is unavailable.
        return (
            "AI remarks unavailable because the Gemini request failed. Check the API key, internet connection, "
            "model access and quota. Please review the results with a healthcare professional.",
            f"Gemini request failed ({type(exc).__name__})"
        )
