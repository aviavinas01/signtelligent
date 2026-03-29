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
  hint        — which gestures to sign, in order
  emoji       — decorative icon for the UI
  category    — groups phrases in the reference panel
"""

PHRASES = [
    {
        "id":       "hello_how_are_you",
        "display":  "Hello, how are you?",
        "hint":     "hello → ok → ?",
        "emoji":    "👋",
        "category": "greeting",
    },
    {
        "id":       "thank_you",
        "display":  "Thank you.",
        "hint":     "thank_you",
        "emoji":    "🙏",
        "category": "greeting",
    },
    {
        "id":       "i_love_you",
        "display":  "I love you.",
        "hint":     "i_love_you",
        "emoji":    "🤟",
        "category": "expression",
    },
    {
        "id":       "yes_please",
        "display":  "Yes, please.",
        "hint":     "yes → peace",
        "emoji":    "✅",
        "category": "response",
    },
    {
        "id":       "no_thank_you",
        "display":  "No, thank you.",
        "hint":     "no → thank_you",
        "emoji":    "❌",
        "category": "response",
    },
    {
        "id":       "please_stop",
        "display":  "Please stop.",
        "hint":     "peace → stop",
        "emoji":    "✋",
        "category": "action",
    },
    {
        "id":       "good_morning",
        "display":  "Good morning.",
        "hint":     "thumbs_up → hello",
        "emoji":    "🌅",
        "category": "greeting",
    },
    {
        "id":       "nice_to_meet_you",
        "display":  "Nice to meet you.",
        "hint":     "ok → hello",
        "emoji":    "🤝",
        "category": "greeting",
    },
    {
        "id":       "i_am_fine",
        "display":  "I am fine.",
        "hint":     "number_1 → thumbs_up",
        "emoji":    "😊",
        "category": "response",
    },
    {
        "id":       "help_me_please",
        "display":  "Help me, please.",
        "hint":     "stop → peace → number_1",
        "emoji":    "🆘",
        "category": "action",
    },
    {
        "id":       "you_are_welcome",
        "display":  "You are welcome.",
        "hint":     "peace → ok → thumbs_up",
        "emoji":    "🫱",
        "category": "response",
    },
    {
        "id":       "see_you_later",
        "display":  "See you later.",
        "hint":     "hello → thumbs_up",
        "emoji":    "👋",
        "category": "greeting",
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