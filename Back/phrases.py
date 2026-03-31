"""
phrases.py — Shared phrase vocabulary
======================================
Single source of truth for the phrase labels the LSTM is trained to recognise.
Import this in collect_sequences.py, train_lstm.py, and sequence_predictor.py.

To add a new phrase:
  1. Add an entry to PHRASES below.
  2. Re-collect sequence data for that phrase.
  3. Re-train:  python train_lstm.py

Each entry:
  id          — internal key (snake_case, no spaces)
  display     — human-readable sentence shown in the UI
  hint        — brief description of the ASL motion (UI only, not used for training)
  emoji       — decorative icon for the UI
  category    — groups phrases in the reference panel
"""

PHRASES = [
    {
        "id":       "hello_how_are_you",
        "display":  "Hello, how are you?",
        "hint":     "Wave hand, then open-palm question",
        "emoji":    "👋",
        "category": "Greeting",
    },
    {
        "id":       "thank_you",
        "display":  "Thank you.",
        "hint":     "Flat hand from chin, move forward",
        "emoji":    "🙏",
        "category": "Greeting",
    },
    {
        "id":       "i_love_you",
        "display":  "I love you.",
        "hint":     "Pinky, index & thumb extended",
        "emoji":    "🤟",
        "category": "Expression",
    },
    {
        "id":       "yes_please",
        "display":  "Yes, please.",
        "hint":     "Fist nod, then rub palms together",
        "emoji":    "✅",
        "category": "Response",
    },
    {
        "id":       "no_thank_you",
        "display":  "No, thank you.",
        "hint":     "Index & middle tap thumb, then thank you",
        "emoji":    "❌",
        "category": "Response",
    },
    {
        "id":       "please_stop",
        "display":  "Please stop.",
        "hint":     "Rub chest, then karate-chop flat hand",
        "emoji":    "✋",
        "category": "Action",
    },
    {
        "id":       "good_morning",
        "display":  "Good morning.",
        "hint":     "Hand from chin outward, then arm rises",
        "emoji":    "🌅",
        "category": "Greeting",
    },
    {
        "id":       "nice_to_meet_you",
        "display":  "Nice to meet you.",
        "hint":     "Flat hands slide together, then point",
        "emoji":    "🤝",
        "category": "Greeting",
    },
    {
        "id":       "i_am_fine",
        "display":  "I am fine.",
        "hint":     "Point to self, then thumbs up",
        "emoji":    "😊",
        "category": "Response",
    },
    {
        "id":       "help_me_please",
        "display":  "Help me, please.",
        "hint":     "Fist on open palm, lift upward",
        "emoji":    "🆘",
        "category": "Action",
    },
    {
        "id":       "you_are_welcome",
        "display":  "You are welcome.",
        "hint":     "Point out, then bow flat hand inward",
        "emoji":    "🫱",
        "category": "Response",
    },
    {
        "id":       "see_you_later",
        "display":  "See you later.",
        "hint":     "V-sign from eyes, point out, wave",
        "emoji":    "👋",
        "category": "Greeting",
    },
]

# ── Convenience helpers ───────────────────────────────────────────────────────

PHRASE_IDS      = [p["id"]      for p in PHRASES]
PHRASE_DISPLAYS = [p["display"] for p in PHRASES]
NUM_PHRASES     = len(PHRASES)

# Look-ups
ID_TO_META  = {p["id"]: p for p in PHRASES}
IDX_TO_META = {i: PHRASES[i] for i in range(NUM_PHRASES)}
ID_TO_IDX   = {p["id"]: i for i, p in enumerate(PHRASES)}