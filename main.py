#!/usr/bin/env python3
"""
IELTS Word Correction Practice
-------------------------------
A terminal quiz that shows you a MISSPELLED or WRONG version of a word
and asks you to type the CORRECT word. Great for fixing recurring
spelling mistakes (like "prepering" -> "preparing", "imporve" -> "improve").

Features:
  - Built-in word bank of commonly misspelled IELTS/English words
  - Add your own words (they get saved so they stay next time)
  - Random quiz order, score tracking, review of mistakes at the end
  - Definitions shown after each answer to build vocabulary too
  - Listening (TTS) mode: the script SPEAKS a word, you type what you heard

Requires for listening mode (pick one):
  Best quality (Kyutai neural TTS, still small/CPU-friendly):
    pip install pocket-tts sounddevice --break-system-packages
  Simpler fallback (lower quality, no download needed):
    pip install pyttsx3 --break-system-packages
(Text-based quiz modes work fine without either.)
"""

import json
import random
import os
import sys

# --- TTS backends -----------------------------------------------------
# Primary: pocket-tts (Kyutai) - small neural model, good voice quality.
try:
    from pocket_tts import TTSModel
    import sounddevice as sd
    POCKET_TTS_AVAILABLE = True
except ImportError:
    POCKET_TTS_AVAILABLE = False

# Fallback: pyttsx3 - offline, robotic, but zero-setup on most systems.
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

TTS_AVAILABLE = POCKET_TTS_AVAILABLE or PYTTSX3_AVAILABLE

_pocket_model = None
_pocket_voice_state = None
_pyttsx3_engine = None

# Change this to any pre-made pocket-tts voice name, or a path/URL to a
# reference wav (see pocket-tts docs), e.g. "hf://kyutai/tts-voices/..."
POCKET_TTS_VOICE = "eve"


def _get_pocket_tts():
    global _pocket_model, _pocket_voice_state
    if _pocket_model is None:
        print("Loading pocket-tts model (first run only, may take a moment)...")
        _pocket_model = TTSModel.load_model()
        _pocket_voice_state = _pocket_model.get_state_for_audio_prompt(POCKET_TTS_VOICE)
    return _pocket_model, _pocket_voice_state


def _get_pyttsx3_engine():
    global _pyttsx3_engine
    if _pyttsx3_engine is None:
        _pyttsx3_engine = pyttsx3.init()
        _pyttsx3_engine.setProperty("rate", 150)
    return _pyttsx3_engine


def speak(text):
    if POCKET_TTS_AVAILABLE:
        model, voice_state = _get_pocket_tts()
        audio = model.generate_audio(voice_state, text)
        sd.play(audio.numpy(), model.sample_rate)
        sd.wait()
        return
    if PYTTSX3_AVAILABLE:
        engine = _get_pyttsx3_engine()
        engine.say(text)
        engine.runAndWait()
        return
    print("(No TTS backend installed — see the install instructions at the top of this file.)")

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "word_bank.json")

# Starter word bank: correct word, a common wrong/misspelled form, and a short meaning.
DEFAULT_WORDS = [
    # {"correct": "preparing", "wrong": "prepering", "meaning": "getting ready for something"},
    # {"correct": "improve", "wrong": "imporve", "meaning": "to make or get better"},
    # {"correct": "possible", "wrong": "posibble", "meaning": "able to happen or be done"},
    # {"correct": "sometimes", "wrong": "some time", "meaning": "occasionally (one word, not two, in this sense)"},
    # {"correct": "necessary", "wrong": "neccessary", "meaning": "required, essential"},
    # {"correct": "definitely", "wrong": "definately", "meaning": "without doubt, certainly"},
    # {"correct": "environment", "wrong": "enviroment", "meaning": "the natural world; surroundings"},
    # {"correct": "government", "wrong": "goverment", "meaning": "the group that governs a country"},
    # {"correct": "opportunity", "wrong": "oppurtunity", "meaning": "a chance to do something"},
    # {"correct": "achieve", "wrong": "acheive", "meaning": "to successfully complete or reach a goal"},
    # {"correct": "believe", "wrong": "beleive", "meaning": "to accept something as true"},
    # {"correct": "separate", "wrong": "seperate", "meaning": "to divide or set apart"},
    # {"correct": "occurred", "wrong": "occured", "meaning": "happened (past tense of occur)"},
    # {"correct": "recommend", "wrong": "recomend", "meaning": "to suggest something as good or suitable"},
    # {"correct": "receive", "wrong": "recieve", "meaning": "to get or be given something"},
    # {"correct": "beginning", "wrong": "begining", "meaning": "the start of something"},
    # {"correct": "argument", "wrong": "arguement", "meaning": "a reason put forward to support an idea"},
    # {"correct": "advantage", "wrong": "advantege", "meaning": "a benefit or favorable factor"},
    # {"correct": "consequence", "wrong": "concequence", "meaning": "a result or effect of an action"},
]


def load_words():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            print("Couldn't read saved word bank, starting fresh.")
    return DEFAULT_WORDS.copy()


def save_words(words):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(words, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"(Warning: couldn't save word bank: {e})")


def add_word(words):
    print("\n--- Add a new word ---")
    correct = input("Correct spelling: ").strip()
    if not correct:
        print("Cancelled.")
        return
    wrong = input("Common wrong version (how you tend to write it): ").strip()
    meaning = input("Meaning (optional): ").strip()
    words.append({"correct": correct, "wrong": wrong, "meaning": meaning, "mistake":0})
    save_words(words)
    print(f"Added '{correct}'.\n")


def run_quiz(words, num_questions):
    if not words:
        print("No words available. Add some first!")
        return

    quiz_set = words.copy()
    random.shuffle(quiz_set)
    quiz_set = quiz_set[:num_questions]

    score = 0
    mistakes = []

    print(f"\nStarting quiz — {len(quiz_set)} words. Type the CORRECT spelling.\n")

    for i, item in enumerate(quiz_set, start=1):
        shown = item.get("wrong") or item["correct"]
        answer = input(f"[{i}/{len(quiz_set)}] Fix this word: '{shown}'  ->  ").strip()

        correct_word = item["correct"]
        if answer.lower() == correct_word.lower():
            print("Correct!")
            score += 1
        else:
            print(f"Not quite. Correct answer: '{correct_word}'")
            mistake_count=item["mistake"]
            mistake_count += 1
            print(mistake_count)
            words.append({"mistake":mistake_count})
            mistakes.append(item)

        if item.get("meaning"):
            print(f"   Meaning: {item['meaning']}")
        print()

    print("=" * 40)
    print(f"Score: {score}/{len(quiz_set)}")
    print("=" * 40)

    if mistakes:
        print("\nWords to review:")
        for m in mistakes:
            meaning = f" — {m['meaning']}" if m.get("meaning") else ""
            print(f"  - {m['correct']}{meaning}")
    else:
        print("\nPerfect round! 🎉")


def run_dictation_quiz(words, num_questions):
    if not words:
        print("No words available. Add some first!")
        return
    if not TTS_AVAILABLE:
        print("\nListening mode needs a TTS backend. Install one with:")
        print("  pip install pocket-tts sounddevice --break-system-packages   (better quality)")
        print("  or: pip install pyttsx3 --break-system-packages              (simpler)")
        return

    quiz_set = words.copy()
    random.shuffle(quiz_set)
    quiz_set = quiz_set[:num_questions]

    score = 0
    mistakes = []

    print(f"\nListening quiz — {len(quiz_set)} words. Listen, then type what you hear.")
    print("(Type 'r' to hear the word again.)\n")

    for i, item in enumerate(quiz_set, start=1):
        correct_word = item["correct"]
        print(f"[{i}/{len(quiz_set)}] Listen...")
        speak(correct_word)

        answer = input("Type the word you heard: ").strip()
        while answer.lower() == "r":
            speak(correct_word)
            answer = input("Type the word you heard: ").strip()

        if answer.lower() == correct_word.lower():
            print("Correct!")
            score += 1
        else:
            print(f"Not quite. Correct spelling: '{correct_word}'")
            mistake_count=item["mistake"]
            mistake_count += 1
            print(mistake_count)
            item["mistake"] = item.get("mistake", 0) + 1
            #save_words()
            mistakes.append(item)

        if item.get("meaning"):
            print(f"   Meaning: {item['meaning']}")
        print()

    print("=" * 40)
    print(f"Score: {score}/{len(quiz_set)}")
    print("=" * 40)

    if mistakes:
        print("\nWords to review:")
        for m in mistakes:
            meaning = f" — {m['meaning']}" if m.get("meaning") else ""
            print(f"  - {m['correct']}{meaning}")
    else:
        print("\nPerfect round! 🎉")


def main_menu():
    words = load_words()
    while True:
        print("\n=== IELTS Word Correction Practice ===")
        print(f"Words in your bank: {len(words)}")
        print("1) Start quiz (spelling correction)")
        print("2) Start listening quiz (TTS speaks, you type)" + ("" if TTS_AVAILABLE else "  [needs pyttsx3]"))
        print("3) Add a new word")
        print("4) View all words")
        print("5) Quit")
        choice = input("Choose an option (1-5): ").strip()

        if choice == "1":
            try:
                n = input(f"How many questions? (max {len(words)}, Enter for all): ").strip()
                num_questions = int(n) if n else len(words)
                num_questions = max(1, min(num_questions, len(words)))
            except ValueError:
                num_questions = len(words)
            run_quiz(words, num_questions)
        elif choice == "2":
            try:
                n = input(f"How many questions? (max {len(words)}, Enter for all): ").strip()
                num_questions = int(n) if n else len(words)
                num_questions = max(1, min(num_questions, len(words)))
            except ValueError:
                num_questions = len(words)
            run_dictation_quiz(words, num_questions)
        elif choice == "3":
            add_word(words)
        elif choice == "4":
            print("\n--- Word Bank ---")
            for w in words:
                meaning = f" — {w['meaning']}" if w.get("meaning") else ""
                print(f"  {w['correct']}{meaning}")
        elif choice == "5":
            print("Good luck with your IELTS prep!")
            sys.exit(0)
        else:
            print("Invalid option, try again.")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nBye! Keep practicing.")
        sys.exit(0)