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
    # --- ORIGINAL 12 PHRASES ---
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

    # --- NEW 88 PHRASES ---

    # QUESTIONS
    {
        "id":       "what",
        "display":  "What?",
        "hint":     "Hands open, palms up, shake slightly side to side",
        "emoji":    "🤷",
        "category": "Question",
    },
    {
        "id":       "where",
        "display":  "Where?",
        "hint":     "Index finger pointing up, shaking side to side",
        "emoji":    "📍",
        "category": "Question",
    },
    {
        "id":       "when",
        "display":  "When?",
        "hint":     "Index finger circles and taps other index finger",
        "emoji":    "⏱️",
        "category": "Question",
    },
    {
        "id":       "who",
        "display":  "Who?",
        "hint":     "Thumb on chin, index finger bends and straightens",
        "emoji":    "👤",
        "category": "Question",
    },
    {
        "id":       "why",
        "display":  "Why?",
        "hint":     "Hand touches forehead, pulls away into 'Y' shape",
        "emoji":    "🤔",
        "category": "Question",
    },
    {
        "id":       "how",
        "display":  "How?",
        "hint":     "Curved hands back to back, roll forward and open",
        "emoji":    "🛠️",
        "category": "Question",
    },
    {
        "id":       "what_time_is_it",
        "display":  "What time is it?",
        "hint":     "Tap wrist where a watch would be",
        "emoji":    "⌚",
        "category": "Question",
    },
    {
        "id":       "where_is_bathroom",
        "display":  "Where is the bathroom?",
        "hint":     "'T' handshape shaking side to side",
        "emoji":    "🚻",
        "category": "Question",
    },
    {
        "id":       "how_much",
        "display":  "How much?",
        "hint":     "Fists palm up, spring open to spread fingers",
        "emoji":    "💵",
        "category": "Question",
    },
    {
        "id":       "do_you_understand",
        "display":  "Do you understand?",
        "hint":     "Fist near head, flick index finger up",
        "emoji":    "💡",
        "category": "Question",
    },

    # CONVERSATION / POLITENESS
    {
        "id":       "sorry",
        "display":  "I am sorry.",
        "hint":     "Fist rubs in circle over heart",
        "emoji":    "😔",
        "category": "Conversation",
    },
    {
        "id":       "excuse_me",
        "display":  "Excuse me.",
        "hint":     "Fingertips brush along flat palm of other hand",
        "emoji":    "🚶",
        "category": "Conversation",
    },
    {
        "id":       "please",
        "display":  "Please.",
        "hint":     "Flat hand rubs in circle on chest",
        "emoji":    "🥺",
        "category": "Conversation",
    },
    {
        "id":       "yes",
        "display":  "Yes.",
        "hint":     "Fist knocks up and down",
        "emoji":    "👍",
        "category": "Conversation",
    },
    {
        "id":       "no",
        "display":  "No.",
        "hint":     "Index and middle fingers tap thumb",
        "emoji":    "👎",
        "category": "Conversation",
    },
    {
        "id":       "maybe",
        "display":  "Maybe.",
        "hint":     "Flat hands alternate weighing up and down",
        "emoji":    "⚖️",
        "category": "Conversation",
    },
    {
        "id":       "i_dont_understand",
        "display":  "I don't understand.",
        "hint":     "Flick index finger near head while shaking head",
        "emoji":    "❓",
        "category": "Conversation",
    },
    {
        "id":       "again_repeat",
        "display":  "Again / Repeat.",
        "hint":     "Bent hand taps into flat palm",
        "emoji":    "🔁",
        "category": "Conversation",
    },
    {
        "id":       "slow_down",
        "display":  "Slow down.",
        "hint":     "Flat hand strokes down back of other hand",
        "emoji":    "🐢",
        "category": "Conversation",
    },
    {
        "id":       "right_correct",
        "display":  "Right / Correct.",
        "hint":     "Sides of index fists tap each other",
        "emoji":    "✔️",
        "category": "Conversation",
    },
    {
        "id":       "wrong",
        "display":  "Wrong.",
        "hint":     "'Y' handshape taps chin",
        "emoji":    "✖️",
        "category": "Conversation",
    },
    {
        "id":       "what_is_your_name",
        "display":  "What is your name?",
        "hint":     "Point, then tap index/middle fingers forming cross",
        "emoji":    "📛",
        "category": "Conversation",
    },
    {
        "id":       "my_name_is",
        "display":  "My name is...",
        "hint":     "Point to self, tap index/middle fingers forming cross",
        "emoji":    "🏷️",
        "category": "Conversation",
    },
    {
        "id":       "sign_language",
        "display":  "Sign language.",
        "hint":     "Index fingers point up and pedal backwards",
        "emoji":    "👐",
        "category": "Conversation",
    },

    # NEEDS & EMERGENCY
    {
        "id":       "i_need",
        "display":  "I need...",
        "hint":     "Curved 'X' hand moves down sharply",
        "emoji":    "❗",
        "category": "Emergency",
    },
    {
        "id":       "i_am_sick",
        "display":  "I am sick.",
        "hint":     "Middle fingers tap forehead and stomach",
        "emoji":    "🤒",
        "category": "Emergency",
    },
    {
        "id":       "pain_hurt",
        "display":  "Pain / It hurts.",
        "hint":     "Index fingers point at each other and twist",
        "emoji":    "🤕",
        "category": "Emergency",
    },
    {
        "id":       "hospital",
        "display":  "Hospital.",
        "hint":     "'H' handshape draws cross on upper arm",
        "emoji":    "🏥",
        "category": "Emergency",
    },
    {
        "id":       "doctor",
        "display":  "Doctor.",
        "hint":     "Bent hand taps inside of wrist",
        "emoji":    "🩺",
        "category": "Emergency",
    },
    {
        "id":       "emergency",
        "display":  "Emergency!",
        "hint":     "'E' handshape shaken vigorously",
        "emoji":    "🚨",
        "category": "Emergency",
    },
    {
        "id":       "call_for_help",
        "display":  "Call for help.",
        "hint":     "Phone handshape to ear, then 'Help' sign",
        "emoji":    "📞",
        "category": "Emergency",
    },
    {
        "id":       "i_am_tired",
        "display":  "I am tired.",
        "hint":     "Fingertips on chest, hands roll downward",
        "emoji":    "🥱",
        "category": "Emergency",
    },
    {
        "id":       "medicine",
        "display":  "Medicine.",
        "hint":     "Middle finger rubs palm of other hand",
        "emoji":    "💊",
        "category": "Emergency",
    },
    {
        "id":       "danger_watch_out",
        "display":  "Danger / Watch out.",
        "hint":     "Thumb of 'A' hand brushes up back of flat hand",
        "emoji":    "⚠️",
        "category": "Emergency",
    },

    # FOOD & DRINK
    {
        "id":       "food_eat",
        "display":  "Food / Eat.",
        "hint":     "Flattened 'O' hand taps mouth",
        "emoji":    "🍽️",
        "category": "Food",
    },
    {
        "id":       "drink",
        "display":  "Drink.",
        "hint":     "Mimic holding a cup and drinking",
        "emoji":    "🥤",
        "category": "Food",
    },
    {
        "id":       "water",
        "display":  "Water.",
        "hint":     "'W' handshape taps chin",
        "emoji":    "💧",
        "category": "Food",
    },
    {
        "id":       "hungry",
        "display":  "I am hungry.",
        "hint":     "'C' handshape slides down chest",
        "emoji":    "🤤",
        "category": "Food",
    },
    {
        "id":       "full_eaten",
        "display":  "I am full.",
        "hint":     "Flat hand pushes under chin",
        "emoji":    "🤰",
        "category": "Food",
    },
    {
        "id":       "coffee",
        "display":  "Coffee.",
        "hint":     "Fists stacked, top fist grinds in circle",
        "emoji":    "☕",
        "category": "Food",
    },
    {
        "id":       "tea",
        "display":  "Tea.",
        "hint":     "'F' handshape stirs inside 'O' handshape",
        "emoji":    "🍵",
        "category": "Food",
    },
    {
        "id":       "more",
        "display":  "More.",
        "hint":     "Flattened 'O' hands tap fingertips together",
        "emoji":    "➕",
        "category": "Food",
    },
    {
        "id":       "finished_done",
        "display":  "Finished / Done.",
        "hint":     "Open hands, palms facing in, flip to face out",
        "emoji":    "👐",
        "category": "Food",
    },
    {
        "id":       "delicious",
        "display":  "Delicious.",
        "hint":     "Middle finger and thumb snap off chin",
        "emoji":    "😋",
        "category": "Food",
    },
    {
        "id":       "milk",
        "display":  "Milk.",
        "hint":     "Squeeze fist like milking a cow",
        "emoji":    "🥛",
        "category": "Food",
    },
    {
        "id":       "apple",
        "display":  "Apple.",
        "hint":     "Knuckle of index finger twists on cheek",
        "emoji":    "🍎",
        "category": "Food",
    },

    # EMOTIONS & FEELINGS
    {
        "id":       "happy",
        "display":  "Happy.",
        "hint":     "Flat hands brush upward on chest",
        "emoji":    "😁",
        "category": "Emotion",
    },
    {
        "id":       "sad",
        "display":  "Sad.",
        "hint":     "Open hands pull down in front of face",
        "emoji":    "😢",
        "category": "Emotion",
    },
    {
        "id":       "angry",
        "display":  "Angry.",
        "hint":     "Claw hands pull up and out from chest",
        "emoji":    "😠",
        "category": "Emotion",
    },
    {
        "id":       "surprised",
        "display":  "Surprised.",
        "hint":     "Pinch fingers at eyes, pop open wide",
        "emoji":    "😲",
        "category": "Emotion",
    },
    {
        "id":       "scared",
        "display":  "Scared.",
        "hint":     "Fists move to center of chest and open",
        "emoji":    "😨",
        "category": "Emotion",
    },
    {
        "id":       "excited",
        "display":  "Excited.",
        "hint":     "Middle fingers alternating brushing up on chest",
        "emoji":    "🤩",
        "category": "Emotion",
    },
    {
        "id":       "bored",
        "display":  "Bored.",
        "hint":     "Index finger twists at side of nose",
        "emoji":    "😒",
        "category": "Emotion",
    },
    {
        "id":       "nervous",
        "display":  "Nervous.",
        "hint":     "Hands shake slightly at sides",
        "emoji":    "😬",
        "category": "Emotion",
    },
    {
        "id":       "proud",
        "display":  "Proud.",
        "hint":     "'A' handshape thumb slides up chest",
        "emoji":    "😌",
        "category": "Emotion",
    },
    {
        "id":       "confused",
        "display":  "Confused.",
        "hint":     "Point to head, then two claw hands circle each other",
        "emoji":    "😵",
        "category": "Emotion",
    },

    # TIME & DAYS
    {
        "id":       "today",
        "display":  "Today.",
        "hint":     "Both 'Y' hands bounce twice",
        "emoji":    "📅",
        "category": "Time",
    },
    {
        "id":       "tomorrow",
        "display":  "Tomorrow.",
        "hint":     "'A' handshape thumb strokes forward on jaw",
        "emoji":    "➡️",
        "category": "Time",
    },
    {
        "id":       "yesterday",
        "display":  "Yesterday.",
        "hint":     "'A' handshape thumb moves from chin to ear",
        "emoji":    "⬅️",
        "category": "Time",
    },
    {
        "id":       "now",
        "display":  "Now.",
        "hint":     "Both 'Y' hands drop down once",
        "emoji":    "👇",
        "category": "Time",
    },
    {
        "id":       "later",
        "display":  "Later.",
        "hint":     "'L' handshape pivots forward",
        "emoji":    "🔜",
        "category": "Time",
    },
    {
        "id":       "day",
        "display":  "Day.",
        "hint":     "Straight arm pivots down resting on other hand",
        "emoji":    "☀️",
        "category": "Time",
    },
    {
        "id":       "night",
        "display":  "Night.",
        "hint":     "Bent hand taps over flat hand/arm",
        "emoji":    "🌙",
        "category": "Time",
    },
    {
        "id":       "afternoon",
        "display":  "Afternoon.",
        "hint":     "Flat arm points forward, bouncing slightly",
        "emoji":    "🌇",
        "category": "Time",
    },
    {
        "id":       "evening",
        "display":  "Evening.",
        "hint":     "Bent hands overlap in front of chest",
        "emoji":    "🌆",
        "category": "Time",
    },
    {
        "id":       "week",
        "display":  "Week.",
        "hint":     "Index finger slides across flat palm",
        "emoji":    "📆",
        "category": "Time",
    },
    {
        "id":       "month",
        "display":  "Month.",
        "hint":     "Index finger slides down back of other index finger",
        "emoji":    "🗓️",
        "category": "Time",
    },
    {
        "id":       "year",
        "display":  "Year.",
        "hint":     "Fists circle each other and stack",
        "emoji":    "🎊",
        "category": "Time",
    },
    {
        "id":       "time",
        "display":  "Time.",
        "hint":     "Tap back of wrist",
        "emoji":    "🕰️",
        "category": "Time",
    },

    # PEOPLE & FAMILY
    {
        "id":       "family",
        "display":  "Family.",
        "hint":     "'F' hands touch thumbs, circle out to touch pinkies",
        "emoji":    "👨‍👩‍👧‍👦",
        "category": "People",
    },
    {
        "id":       "mother",
        "display":  "Mother.",
        "hint":     "Thumb of '5' hand taps chin",
        "emoji":    "👩",
        "category": "People",
    },
    {
        "id":       "father",
        "display":  "Father.",
        "hint":     "Thumb of '5' hand taps forehead",
        "emoji":    "👨",
        "category": "People",
    },
    {
        "id":       "friend",
        "display":  "Friend.",
        "hint":     "Index fingers hook together, then reverse",
        "emoji":    "🤝",
        "category": "People",
    },
    {
        "id":       "man",
        "display":  "Man.",
        "hint":     "Thumb from forehead to chest",
        "emoji":    "🚹",
        "category": "People",
    },
    {
        "id":       "woman",
        "display":  "Woman.",
        "hint":     "Thumb from chin to chest",
        "emoji":    "🚺",
        "category": "People",
    },
    {
        "id":       "child_baby",
        "display":  "Child / Baby.",
        "hint":     "Mimic cradling and rocking a baby",
        "emoji":    "👶",
        "category": "People",
    },
    {
        "id":       "teacher",
        "display":  "Teacher.",
        "hint":     "'O' hands pull from head, then person marker down",
        "emoji":    "🧑‍🏫",
        "category": "People",
    },
    {
        "id":       "student",
        "display":  "Student.",
        "hint":     "Pick up from palm, to head, then person marker down",
        "emoji":    "🧑‍🎓",
        "category": "People",
    },
    {
        "id":       "deaf",
        "display":  "Deaf.",
        "hint":     "Index finger from ear to mouth",
        "emoji":    "🧏",
        "category": "People",
    },
    {
        "id":       "hearing",
        "display":  "Hearing.",
        "hint":     "Index finger rolls forward in front of mouth",
        "emoji":    "👂",
        "category": "People",
    },

    # COMMON VERBS / ACTIONS
    {
        "id":       "go",
        "display":  "Go.",
        "hint":     "Index fingers point and push forward",
        "emoji":    "🚶‍♂️",
        "category": "Action",
    },
    {
        "id":       "come",
        "display":  "Come.",
        "hint":     "Index fingers point and pull inward",
        "emoji":    "🏃",
        "category": "Action",
    },
    {
        "id":       "work",
        "display":  "Work.",
        "hint":     "Fists tap each other at wrists",
        "emoji":    "💼",
        "category": "Action",
    },
    {
        "id":       "learn",
        "display":  "Learn.",
        "hint":     "Grab from palm and pull to forehead",
        "emoji":    "📚",
        "category": "Action",
    },
    {
        "id":       "sleep",
        "display":  "Sleep.",
        "hint":     "Hand draws down over face, closing fingers",
        "emoji":    "😴",
        "category": "Action",
    },
    {
        "id":       "wake_up",
        "display":  "Wake up.",
        "hint":     "Pinch fingers at eyes, pop open",
        "emoji":    "😳",
        "category": "Action",
    },
    {
        "id":       "read",
        "display":  "Read.",
        "hint":     "Two fingers scan down flat palm",
        "emoji":    "📖",
        "category": "Action",
    },
    {
        "id":       "write",
        "display":  "Write.",
        "hint":     "Mimic holding pen and writing on palm",
        "emoji":    "✍️",
        "category": "Action",
    },
    {
        "id":       "drive",
        "display":  "Drive.",
        "hint":     "Mimic holding and turning a steering wheel",
        "emoji":    "🚗",
        "category": "Action",
    },
    {
        "id":       "home",
        "display":  "Home.",
        "hint":     "Fingertips tap chin then cheek",
        "emoji":    "🏠",
        "category": "Action",
    }
]

# ── Convenience helpers ───────────────────────────────────────────────────────

PHRASE_IDS      = [p["id"]      for p in PHRASES]
PHRASE_DISPLAYS = [p["display"] for p in PHRASES]
NUM_PHRASES     = len(PHRASES)

# Look-ups
ID_TO_META  = {p["id"]: p for p in PHRASES}
IDX_TO_META = {i: PHRASES[i] for i in range(NUM_PHRASES)}
ID_TO_IDX   = {p["id"]: i for i, p in enumerate(PHRASES)}