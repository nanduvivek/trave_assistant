"""
core/ocr_engine.py — Receipt OCR using Gemini Vision for TravelPro.

Extracts structured expense data from uploaded receipt images.
Falls back gracefully to empty dict if API key not configured.
"""
from __future__ import annotations
import json
import re
import streamlit as st


def extract_receipt_data(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """
    Use Gemini Vision to extract structured data from a receipt image.

    Returns a dict with keys: merchant, amount, currency, date, category, description.
    Returns empty dict on failure (caller should show manual-entry fallback).
    """
    api_key = st.session_state.get("ai_api_key", "")
    if not api_key:
        return {}

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = """You are a receipt OCR system. Analyze this receipt image and extract the following fields.
Return ONLY a valid JSON object with these exact keys:
{
  "merchant": "business name",
  "amount": 0.00,
  "currency": "USD",
  "date": "YYYY-MM-DD",
  "category": "one of: Accommodation | Airfare | Meals | Ground Transport | Other",
  "description": "brief description of purchase"
}

If a field cannot be determined, use null. Return ONLY the JSON, no other text."""

        import google.generativeai as genai
        image_part = {"mime_type": mime_type, "data": image_bytes}
        response = model.generate_content([prompt, image_part])

        raw = response.text.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        data = json.loads(raw)
        # Ensure amount is a float
        if data.get("amount") is not None:
            data["amount"] = float(data["amount"])
        return data

    except Exception:
        return {}


def parse_receipt_fallback(text: str) -> dict:
    """
    Simple regex-based fallback for text receipts (PDF/TXT).
    Returns partial data where detectable.
    """
    result: dict = {"currency": "USD"}

    # Amount: look for $XX.XX or total: XX.XX
    amt_match = re.search(r"(?:total|amount|grand total)[:\s]*\$?([\d,]+\.\d{2})", text, re.IGNORECASE)
    if not amt_match:
        amt_match = re.search(r"\$\s*([\d,]+\.\d{2})", text)
    if amt_match:
        result["amount"] = float(amt_match.group(1).replace(",", ""))

    # Date: look for MM/DD/YYYY or YYYY-MM-DD
    date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2})", text)
    if date_match:
        result["date"] = date_match.group(1)

    return result
