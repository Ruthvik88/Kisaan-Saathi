"""
Context builder: live weather (Open-Meteo, free, no API key) + hardcoded MSP
price data from msp_data.json.

Weather fetch fails SOFT — returns ok=False with a message — since weather
being briefly unavailable shouldn't break the whole assistant. This is the
ONE place a soft fallback is appropriate, unlike STT/LLM/TTS which must
raise on failure.
"""

import json
import os
import logging

import requests

logger = logging.getLogger(__name__)

_MSP_DATA_PATH = os.path.join(os.path.dirname(__file__), "msp_data.json")


def get_weather(lat: float = 12.97, lon: float = 77.59) -> dict:
    """
    Fetch current weather from Open-Meteo.

    Returns:
        On success: {"ok": True, "data": <Open-Meteo response dict>}
        On failure: {"ok": False, "error": <message string>}
    """
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,precipitation,rain",
                "timezone": "Asia/Kolkata",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return {"ok": True, "data": resp.json()}
    except requests.RequestException as exc:
        msg = f"Weather fetch failed: {exc}"
        logger.warning(msg)
        return {"ok": False, "error": msg}


def get_msp_data() -> dict:
    """Load and return the hardcoded MSP data from msp_data.json."""
    with open(_MSP_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_context_string() -> str:
    """
    Combine weather + MSP data into a single labeled text block for
    injection into the Gemini system prompt.
    """
    # --- Weather section ---
    weather = get_weather()

    if weather["ok"]:
        current = weather["data"].get("current", {})
        temp = current.get("temperature_2m", "N/A")
        humidity = current.get("relative_humidity_2m", "N/A")
        precipitation = current.get("precipitation", "N/A")
        rain = current.get("rain", "N/A")

        weather_text = (
            "WEATHER (current, Bangalore area):\n"
            f"  Temperature: {temp}°C\n"
            f"  Humidity: {humidity}%\n"
            f"  Precipitation: {precipitation} mm\n"
            f"  Rain: {rain} mm"
        )
    else:
        weather_text = (
            "WEATHER: UNAVAILABLE\n"
            f"  Reason: {weather['error']}\n"
            "  Do NOT guess or invent weather numbers. Tell the farmer "
            "weather data could not be fetched right now."
        )

    # --- MSP section ---
    msp = get_msp_data()
    crops = msp.get("crops", [])

    msp_lines = [
        "MSP DATA (2024-25 season, reference prices — NOT live mandi rates):",
        "  Remind the farmer to verify prices at their local mandi before selling.",
    ]
    for crop in crops:
        msp_lines.append(
            f"  {crop['crop_name']} "
            f"(हिं: {crop['crop_name_hi']}, "
            f"తె: {crop['crop_name_te']}, "
            f"ಕ: {crop['crop_name_kn']}, "
            f"த: {crop['crop_name_ta']}): "
            f"₹{crop['msp_inr_per_quintal']}/quintal, "
            f"{crop['season']}"
        )

    msp_text = "\n".join(msp_lines)

    return f"{weather_text}\n\n{msp_text}"
