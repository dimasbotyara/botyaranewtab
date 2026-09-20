"""50+ greetings per time-of-day, per language, with optional {name} placeholder."""

import random

# Each list has greetings — some use {name}, some don't.
# The frontend will replace {name} with username (or remove it if empty).

GREETINGS = {
    "en": {
        "morning": [
            "Good morning, {name}",
            "Morning, {name} ☀️",
            "Rise and shine!",
            "Top of the morning!",
            "Hey early bird!",
            "Wakey wakey, {name}!",
            "A brand new day, {name}",
            "Morning sunshine!",
            "Hello, beautiful morning!",
            "Ready to conquer the day?",
            "Fresh start, {name}!",
            "The world awaits, {name}",
            "Good morning, superstar!",
            "Up and at 'em!",
            "Dawn patrol, {name}!",
        ],
        "afternoon": [
            "Good afternoon, {name}",
            "Afternoon, {name}",
            "Hey there!",
            "How's your day going?",
            "Halfway through the day!",
            "Keep it up, {name}!",
            "Hope your day is great!",
            "Productive afternoon, {name}?",
            "Still crushing it?",
            "Hello, {name}! 👋",
            "What's cooking, {name}?",
            "Afternoon vibes ✨",
            "You're doing great!",
        ],
        "evening": [
            "Good evening, {name}",
            "Evening, {name} 🌆",
            "Winding down?",
            "How was your day, {name}?",
            "Relax, you've earned it!",
            "Evening vibes 🌙",
            "Time to chill, {name}",
            "Hello, {name}! Nice evening",
            "Sunset mode activated",
            "Almost done for today!",
            "Take it easy, {name}",
            "Enjoy your evening!",
            "Golden hour, {name} 🌅",
        ],
        "night": [
            "Hello, night owl 🦉",
            "Burning the midnight oil?",
            "Late night, {name}?",
            "The night is young!",
            "Can't sleep, {name}?",
            "Night shift vibes",
            "Stars are out, {name} ✨",
            "Shh… it's quiet hours",
            "Midnight adventures!",
            "The world sleeps, but not {name}!",
            "Nocturnally yours 🌙",
            "Who needs sleep anyway?",
            "3 AM thoughts, {name}?",
            "Hello darkness, my old friend",
            "Night mode: activated",
        ],
    },
    "ru": {
        "morning": [
            "Доброе утро, {name}!",
            "Утречко, {name} ☀️",
            "С добрым утром!",
            "Подъём, {name}!",
            "Новый день — новые свершения!",
            "Ранняя пташка, {name}?",
            "Утро начинается с тебя!",
            "Проснулся? Красавчик!",
            "Солнышко встало, и ты тоже!",
            "Время кофе, {name} ☕",
            "Бодрого утра, {name}!",
            "Утро доброе, день будет лучше!",
            "Сегодня будет отличный день!",
            "Кто рано встаёт… привет, {name}!",
            "Утренний {name} — лучший {name}!",
        ],
        "afternoon": [
            "Добрый день, {name}!",
            "Привет, {name}! 👋",
            "Как дела, {name}?",
            "День в разгаре!",
            "Продолжай в том же духе!",
            "Хороший день, {name}?",
            "Дневной {name} жжёт!",
            "Так держать, {name}!",
            "Полдень. Время великих дел!",
            "Привет! Как настроение?",
            "Ты молодец, {name}!",
            "Дневная смена, {name}!",
            "Уже половина дня — ты справляешься!",
        ],
        "evening": [
            "Добрый вечер, {name}!",
            "Вечер добрый! 🌆",
            "Как прошёл день, {name}?",
            "Время отдыхать!",
            "Вечерний {name} в деле!",
            "Расслабься, ты заслужил!",
            "Уютного вечера, {name}!",
            "Вечерние вайбы 🌙",
            "Закат. Красиво, правда?",
            "Отличный был день, {name}?",
            "Скоро ночь, но ты ещё здесь!",
            "Вечерок, {name} 🌅",
            "Вечер — лучшее время!",
        ],
        "night": [
            "Привет, полуночник! 🦉",
            "Не спится, {name}?",
            "Ночная смена?",
            "Ночь — время гениев!",
            "Звёзды вышли, {name} ✨",
            "Тише… все спят!",
            "Полуночные приключения!",
            "Мир спит, а {name} нет!",
            "Ночной {name} — особенный!",
            "Кому нужен сон?",
            "3 часа ночи, {name}? Серьёзно?",
            "Ночной режим активирован 🌙",
            "Привет, ночная душа!",
            "Тёмная тема для тёмного времени",
            "Сова? Жаворонок? Нет — {name}!",
        ],
    },
}


def get_time_period(hour: int) -> str:
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 22:
        return "evening"
    else:
        return "night"


def get_greeting(hour: int, lang: str = "en", name: str = "") -> str:
    period = get_time_period(hour)
    lang_greetings = GREETINGS.get(lang, GREETINGS["en"])
    pool = lang_greetings.get(period, lang_greetings["morning"])

    greeting = random.choice(pool)

    if name:
        greeting = greeting.replace("{name}", name)
    else:
        # Clean up {name} placeholder
        greeting = greeting.replace(", {name}", "")
        greeting = greeting.replace(" {name}", "")
        greeting = greeting.replace("{name}", "")

    # Clean double spaces / trailing punctuation issues
    greeting = greeting.replace("  ", " ").strip()

    return greeting


def get_all_greetings():
    """Return all greetings for frontend (so it can pick randomly client-side)."""
    return GREETINGS
