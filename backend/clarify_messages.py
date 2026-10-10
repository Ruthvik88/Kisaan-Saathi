"""
Static localized clarification messages.

Used when the transcript is too unreliable to pass to generation
(low-confidence STT path in main.py). These are STATIC strings — no LLM
call — so an unreliable transcript never reaches generation.

REPEAT_MESSAGES: spoken-style "please say it again" prompts, 3 variants
per language. The variant is picked by clarify_count so a repeated failure
does not sound like a stuck robot.

GIVE_UP_MESSAGES: polite final message when MAX_CLARIFY_TURNS is reached.
Suggests trying again later or asking the local KVK. Contains NO phone
number — do not add one unless explicitly provided.

All strings below need review by a native speaker before production use.
"""

REPEAT_MESSAGES = {
    "hi": [
        "माफ़ कीजिए, मैं आपकी बात समझ नहीं पाया। कृपया फिर से बोलिए।",
        "आपकी आवाज़ साफ़ सुनाई नहीं दी। ज़रा धीरे और साफ़ बोलकर फिर से बताइए।",
        "मुझे ठीक से सुनाई नहीं दिया। कृपया बटन दबाकर फिर से पूछिए।",
    ],
    "te": [
        "క్షమించండి, మీ మాట నాకు అర్థం కాలేదు. దయచేసి మళ్లీ చెప్పండి.",
        "మీ గొంతు సరిగా వినిపించలేదు. కొంచెం నెమ్మదిగా, స్పష్టంగా మళ్లీ అడగండి.",
        "నాకు సరిగా వినపడలేదు. దయచేసి బటన్ నొక్కి మళ్లీ అడగండి.",
    ],
    "kn": [
        "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಮಾತು ನನಗೆ ಅರ್ಥವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಹೇಳಿ.",
        "ನಿಮ್ಮ ಧ್ವನಿ ಸರಿಯಾಗಿ ಕೇಳಿಸಲಿಲ್ಲ. ಸ್ವಲ್ಪ ನಿಧಾನವಾಗಿ, ಸ್ಪಷ್ಟವಾಗಿ ಮತ್ತೆ ಕೇಳಿ.",
        "ನನಗೆ ಸರಿಯಾಗಿ ಕೇಳಿಸಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಬಟನ್ ಒತ್ತಿ ಮತ್ತೆ ಕೇಳಿ.",
    ],
    "ta": [
        "மன்னிக்கவும், நீங்கள் சொன்னது எனக்குப் புரியவில்லை. தயவுசெய்து மீண்டும் சொல்லுங்கள்.",
        "உங்கள் குரல் சரியாகக் கேட்கவில்லை. கொஞ்சம் மெதுவாக, தெளிவாக மீண்டும் கேளுங்கள்.",
        "எனக்கு சரியாகக் கேட்கவில்லை. தயவுசெய்து பொத்தானை அழுத்தி மீண்டும் கேளுங்கள்.",
    ],
}

GIVE_UP_MESSAGES = {
    "hi": (
        "माफ़ कीजिए, मैं आपका सवाल समझ नहीं पा रहा हूँ। "
        "कृपया कुछ देर बाद फिर से कोशिश कीजिए, "
        "या अपने नज़दीकी कृषि विज्ञान केंद्र से सलाह लीजिए।"
    ),
    "te": (
        "క్షమించండి, మీ ప్రశ్నను నేను అర్థం చేసుకోలేకపోతున్నాను. "
        "దయచేసి కొంతసేపటి తర్వాత మళ్లీ ప్రయత్నించండి, "
        "లేదా మీ దగ్గరి వ్యవసాయ విజ్ఞాన కేంద్రంలో సలహా తీసుకోండి."
    ),
    "kn": (
        "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ನಾನು ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲಾಗುತ್ತಿಲ್ಲ. "
        "ದಯವಿಟ್ಟು ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ, "
        "ಅಥವಾ ನಿಮ್ಮ ಹತ್ತಿರದ ಕೃಷಿ ವಿಜ್ಞಾನ ಕೇಂದ್ರದಲ್ಲಿ ಸಲಹೆ ಪಡೆಯಿರಿ."
    ),
    "ta": (
        "மன்னிக்கவும், உங்கள் கேள்வியை என்னால் புரிந்துகொள்ள முடியவில்லை. "
        "தயவுசெய்து சிறிது நேரம் கழித்து மீண்டும் முயற்சி செய்யுங்கள், "
        "அல்லது உங்கள் அருகிலுள்ள வேளாண் அறிவியல் நிலையத்தில் ஆலோசனை பெறுங்கள்."
    ),
}


def get_repeat_message(lang: str, clarify_count: int) -> str:
    """Return a 'please repeat' prompt, rotating variants by clarify_count."""
    variants = REPEAT_MESSAGES.get(lang, REPEAT_MESSAGES["hi"])
    return variants[clarify_count % len(variants)]


def get_give_up_message(lang: str) -> str:
    """Return the final give-up message for a language."""
    return GIVE_UP_MESSAGES.get(lang, GIVE_UP_MESSAGES["hi"])
