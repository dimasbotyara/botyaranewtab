<div align="center">

# 🌙 botyaranewtab

**Твоя новая вкладка. Твои правила.**

Красивая, полностью настраиваемая страница новой вкладки для браузера.
Локально. Без облаков. Без телеметрии. Без аккаунтов. Только ты и твои данные.

[🇬🇧 English](README.md) · 🇷🇺 **Русский**

![Python CI](https://github.com/dimasbotyara/botyaranewtab/actions/workflows/python-app.yml/badge.svg)
![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
![Type](https://img.shields.io/badge/type-Local--First-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-purple.svg)
![Flask](https://img.shields.io/badge/flask-3.1-000000?logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/sqlite-3-003B57?logo=sqlite&logoColor=white)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey)

</div>

---

<p align="center">
  <img src="docs/screenshots/hero.webp" alt="botyaranewtab — полностью настроенный" width="100%">
</p>

---

## 📖 Содержание

- [✨ Что это?](#-что-это)
- [🎯 Возможности](#-возможности)
- [📸 Скриншоты](#-скриншоты)
- [🚀 Быстрый старт](#-быстрый-старт)
- [🌐 Установка как новой вкладки](#-установка-как-новой-вкладки)
- [⚙️ Конфигурация](#️-конфигурация)
- [🔄 Автозапуск](#-автозапуск)
- [🎨 Кастомизация](#-кастомизация)
- [⌨️ Горячие клавиши](#️-горячие-клавиши)
- [🔌 API](#-api)
- [📁 Структура проекта](#-структура-проекта)
- [🛠️ Стек технологий](#️-стек-технологий)
- [🤝 Участие в разработке](#-участие-в-разработке)
- [🥚 Пасхалка](#-пасхалка)
- [📜 Лицензия](#-лицензия)
- [👤 Автор](#-автор)

---

## ✨ Что это?

**botyaranewtab** — это самостоятельный, полностью настраиваемый заменитель новой вкладки браузера. Работает на твоей машине, хранит всё в локальной базе SQLite и **никогда не отправляет ни одного байта** в облако.

В отличие от других расширений для новых вкладок, которые запирают тебя в своём дизайне, своих серверах и своей аналитике — **botyaranewtab даёт тебе исходники и ключи**. Меняй CSS, добавляй виджеты, загружай свои шрифты, меняй фон хоть каждый день. Это твоя страница. Твои правила.

**Для кого это:**
- 🧠 Для тех, кто хочет, чтобы новая вкладка была **полезной**, а не рекламной панелью
- 🔒 Для тех, кто заботится о приватности и не хочет, чтобы его данные о сёрфинге лежали в чьём-то облаке
- 🎨 Для тех, кто любит ковыряться и хочет контролировать каждый пиксель
- 💻 Для тех, кто предпочитает чистый JS, а не папку `node_modules` на 200 МБ

---

## 🎯 Возможности

### 🎨 Внешний вид
- **15+ встроенных тем** — Catppuccin (Mocha, Macchiato, Frappé, Latte), Nord, Dracula, Tokyo Night, Gruvbox, Solarized, One Dark, Rosé Pine, Ayu, Midnight и другие
- **Палитра акцентных цветов** — из темы или любой свой hex
- **Свои шрифты** — устанавливай `.woff2`, `.woff`, `.ttf`, `.otf` прямо из настроек
- **Размеры шрифтов** — глобальный, часы, приветствие, шорткаты — отдельно
- **Скругление, прозрачность, размытие** — все слайдеры, какие захочешь
- **Авто-тема** — светлая днём, тёмная ночью
- **Свой CSS** — вставляй что угодно

### 🖼️ Фоны
- **4 источника** — цвет темы, картинка, градиент, сплошной цвет
- **8 режимов масштабирования** — cover, contain, stretch, tile, center, fit-width, fit-height, fill-blur
- **Сетка позиций 3×3** — точное размещение
- **Эффекты** — blur, затемнение, яркость, насыщенность, сепия, ч/б, виньетка
- **Движение** — Ken Burns (плавный зум), параллакс (за мышью), авто-ротация с настраиваемым интервалом
- **Адаптивный цвет** — вытаскивает доминирующий цвет из обоев и применяет как акцент

### 🔍 Умный поиск
- **Bang-команды** — `!g` Google, `!yt` YouTube, `!w` Википедия, `!gh` GitHub, `!r` Reddit, `!maps`, `!img`, `!translate` и другие
- **Калькулятор прямо в строке** — набери `2+2` или `sqrt(16)` и увидишь ответ
- **Конвертер единиц** — `10 км в мили`, `100 ф в ц`, `5 гб в мб`
- **Превью цвета** — введи `#cba6f7` и увидишь квадратик
- **Автодополнение** — подсказки из твоей же истории поиска
- **Определение URL** — напиши `github.com` и оно просто откроется
- **История поиска** — хранится локально, чистится в один клик

### 🔗 Быстрые ссылки
- **Папки** — группируй ссылки, получай мини-превью содержимого
- **Свои иконки** — загружай свои или бери favicon автоматически
- **Свои цвета** — фон плитки для каждой ссылки
- **Счётчик кликов** — видно, чем ты реально пользуешься
- **Импорт закладок** — HTML/JSON из браузера
- **Экспорт в JSON** — потому что твои ссылки — это твои ссылки

### 🌤️ Виджеты
- **Часы** — 24ч или 12ч (AM/PM), опционально секунды
- **Приветствие** — 50+ вариантов по времени дня, на двух языках, с твоим именем
- **Погода** — работает через [Open-Meteo](https://open-meteo.com/) (API-ключ **не нужен**!)
- **Мировые часы** — время в разных часовых поясах
- **Счётчики дней** — сколько осталось до дня рождения, отпуска, сессии D&D
- **Заметки / Блокнот** — автосохранение по мере ввода
- **Календарь** — чистый вид на месяц
- **Прогресс дня и месяца** — видно, сколько уже прошло

### ⚡ Мощные фишки
- **Режим фокуса** — скрывает всё, кроме часов и поиска
- **Дзен-режим** — только обои и маленькие часы
- **Синхронизация в реальном времени** — меняешь настройки в одной вкладке, они применяются во всех остальных (SSE)
- **PWA** — устанавливается как приложение, работает офлайн
- **Хоткеи** — `/` для поиска, `Ctrl+,` для настроек, `Ctrl+K` для палитры команд и другие
- **Мультиязычность** — русский и английский из коробки
- **Бэкапы** — скачать/восстановить всю базу в один клик
- **Экспорт/импорт настроек** — JSON для переносимости

---

## 📸 Скриншоты

### 🏠 Главный экран

<p align="center">
  <img src="docs/screenshots/hero.webp" alt="Главный экран — полностью настроенный" width="100%">
</p>

### 🎛️ Настройки — глубокая кастомизация

<p align="center">
  <img src="docs/screenshots/appearance1.webp" alt="Настройки внешнего вида — часть 1" width="32%">
  <img src="docs/screenshots/appearance2.webp" alt="Настройки внешнего вида — часть 2" width="32%">
  <img src="docs/screenshots/appearance3.webp" alt="Настройки внешнего вида — часть 3" width="32%">
</p>

### 🧩 Виджеты

<p align="center">
  <img src="docs/screenshots/widgets.webp" alt="Настройки виджетов" width="70%">
</p>

### 🔍 Калькулятор и умный поиск

<p align="center">
  <img src="docs/screenshots/calcsimple.webp" alt="Калькулятор — простой пример" width="49%">
  <img src="docs/screenshots/calchard.webp" alt="Калькулятор — сложный пример" width="49%">
</p>

### 🎨 Как выглядит из коробки

<p align="center">
  <img src="docs/screenshots/default.webp" alt="Дефолтный вид после первого запуска" width="70%">
</p>

---

## 🚀 Быстрый старт

### Что нужно

- **Python 3.10+** (используется синтаксис `X | None`)
- Современный браузер (Chrome, Firefox, Edge, Brave, Vivaldi или любой Chromium-based)
- ~50 МБ на диске (плюс обои, которые загрузишь)

### Установка

```bash
# 1. Клонируй репозиторий
git clone https://github.com/dimasbotyara/botyaranewtab.git
cd botyaranewtab

# 2. Создай виртуальное окружение
python -m venv .venv

# 3. Активируй его
source .venv/bin/activate         # Linux / macOS
# .venv\Scripts\activate          # Windows

# 4. Установи зависимости
pip install -r requirements.txt

# 5. Запусти
python run.py
```

Увидишь красивый баннер в терминале:

```
╭───────────────────────────────────────────╮
│  botyaranewtab — your new tab, your rules │
╰───────────────────────────────────────────╯

  Initializing database…
  Database ready!

  Server starting at: http://127.0.0.1:12121

  Set this URL as your new tab page:
  Extension → Custom New Tab URL → http://127.0.0.1:12121
```

Открой **http://127.0.0.1:12121** в браузере. Готово. 🎉

---

## 🌐 Установка как новой вкладки

botyaranewtab работает как локальный веб-сервер, поэтому нужен расширение браузера, которое перенаправит новую вкладку на него.

### Chrome / Edge / Brave / Vivaldi

1. Установи расширение [Custom New Tab URL](https://chromewebstore.google.com/detail/mmjbdbjnoablegbkcklggeknkfcjkjia)
2. Открой его настройки
3. Укажи URL: `http://127.0.0.1:12121`
4. Открой новую вкладку — готово

### Firefox

1. Установи [New Tab Override](https://addons.mozilla.org/en-US/firefox/addon/new-tab-override/)
2. В настройках выбери «Custom URL»
3. Укажи: `http://127.0.0.1:12121`

### Safari

Safari не позволяет задать свою новую вкладку без нативного расширения. Можно открывать `http://127.0.0.1:12121` вручную или добавить в закладки.

---

## ⚙️ Конфигурация

Всё настраивается через панель настроек в самом приложении (`Ctrl+,` или иконка шестерёнки). Руками ничего редактировать не надо.

### Где что лежит

| Путь | Что |
|---|---|
| `botyaranewtab.db` | База SQLite — все настройки, ссылки, заметки |
| `static/backgrounds/` | Загруженные обои |
| `static/icons/` | Кэшированные favicon'ы + свои иконки |
| `static/fonts/Custom/` | Установленные шрифты |
| `backups/` | Бэкапы базы |
| `config.py` | Порт, хост, пути |

### Смена порта

Если `12121` занят на твоей машине — открой `config.py`:

```python
HOST = "127.0.0.1"
PORT = 12121   # ← поменяй здесь
```

Не забудь обновить URL в расширении браузера и в разделе «О проекте» внутри приложения.

### Переменные окружения (опционально)

Можно переопределить хост и порт без правки `config.py`:

```bash
BOTYARA_PORT=5555 python run.py
```

---

## 🔄 Автозапуск

Хочешь, чтобы botyaranewtab всегда крутился в фоне? Вот как это сделать.

### Linux (systemd)

Создай `~/.config/systemd/user/botyaranewtab.service`:

```ini
[Unit]
Description=botyaranewtab
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/botyaranewtab
ExecStart=/path/to/botyaranewtab/.venv/bin/python /path/to/botyaranewtab/run.py
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
```

Включи:

```bash
systemctl --user daemon-reload
systemctl --user enable --now botyaranewtab
```

Проверка статуса:

```bash
systemctl --user status botyaranewtab
```

### macOS (launchd)

Создай `~/Library/LaunchAgents/com.botyaranewtab.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.botyaranewtab</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/botyaranewtab/.venv/bin/python</string>
        <string>/path/to/botyaranewtab/run.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Загрузи:

```bash
launchctl load ~/Library/LaunchAgents/com.botyaranewtab.plist
```

### Windows

1. Создай ярлык на `run.py` с использованием python из venv:
   ```
   Target: C:\path\to\botyaranewtab\.venv\Scripts\pythonw.exe C:\path\to\botyaranewtab\run.py
   ```

2. Нажми `Win+R`, введи `shell:startup`, Enter
3. Перемести ярлык в открывшуюся папку

Готово — botyaranewtab будет запускаться вместе с Windows.

---

## 🎨 Кастомизация

### Темы

Выбери из встроенной коллекции или **создай свою** — открой `static/js/themes.js`:

```javascript
const Themes = {
    list: {
        'my-theme': {
            name: 'My Theme',
            type: 'dark',
            colors: {
                '--bg-base': '#0a0a0a',
                '--bg-surface': '#1a1a1a',
                '--text-primary': '#ffffff',
                '--accent': '#ff00ff',
                // ...
            }
        }
    }
};
```

Перезагрузи страницу — твоя тема появится в панели «Внешний вид».

### Свой CSS

Внешний вид → поле **Свой CSS**. Всё, что туда напишешь, вставится как `<style>`. Примеры:

```css
/* Неоновые часы */
.clock-time {
    color: #ff00ff;
    text-shadow: 0 0 20px #ff00ff;
}

/* Спрятать дату */
.clock-date {
    display: none;
}

/* Пошире строка поиска */
.search-wrapper {
    max-width: 900px;
    padding: 12px 20px;
}
```

### Bang-команды

Открой `search_engine.py` → словарь `BANG_COMMANDS`:

```python
BANG_COMMANDS = {
    "!g": "https://www.google.com/search?q={}",
    "!yt": "https://www.youtube.com/results?search_query={}",
    # Добавь свои:
    "!so": "https://stackoverflow.com/search?q={}",
    "!np": "https://www.npmjs.com/search?q={}",
}
```

Перезапусти сервер — заработают.

### Шрифты

1. Возьми `.woff2` файл с [fontsource](https://fontsource.org/) или откуда угодно
2. Внешний вид → Шрифт → **Установить шрифт** → выбери файл
3. Он сразу появится в выпадающем списке

---

## ⌨️ Горячие клавиши

| Клавиши | Действие |
|---|---|
| `/` | Фокус на поиск |
| `Esc` | Очистить поиск / закрыть модалку |
| `Ctrl` + `,` | Открыть настройки |
| `Ctrl` + `K` | Палитра команд (фокус на поиск с `!`) |
| `Ctrl` + `1..9` | Открыть N-ю ссылку |
| `Ctrl` + `Shift` + `F` | Режим фокуса |
| `Ctrl` + `Shift` + `Z` | Дзен-режим |

Плюс: **правый клик по фону** открывает настройки, если включено.

---

## 🔌 API

Все эндпоинты под `/api/`. Фронтенд их использует, ты тоже можешь.

### Настройки

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/settings` | Получить все настройки |
| `POST` | `/api/settings` | Обновить одну или несколько |
| `POST` | `/api/settings/reset` | Сбросить к дефолтным |
| `GET` | `/api/settings/export` | Скачать настройки как JSON |
| `POST` | `/api/settings/import` | Загрузить JSON настроек |

### Быстрые ссылки

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/shortcuts` | Список всех |
| `POST` | `/api/shortcuts` | Добавить |
| `PUT` | `/api/shortcuts/:id` | Обновить |
| `DELETE` | `/api/shortcuts/:id` | Удалить |
| `POST` | `/api/shortcuts/:id/click` | Увеличить счётчик |
| `GET` | `/api/shortcuts/export` | Скачать как JSON |
| `POST` | `/api/shortcuts/import` | Импорт из HTML/JSON |

### Виджеты

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/weather` | Текущая погода (lat/lon) |
| `GET` | `/api/weather/geocode` | Город → координаты |
| `GET` | `/api/weather/reverse` | Координаты → город |
| `GET` | `/api/countdowns` | Список счётчиков |
| `POST` | `/api/countdowns` | Добавить счётчик |
| `DELETE` | `/api/countdowns/:id` | Удалить счётчик |
| `GET` | `/api/world-clocks` | Мировые часы |
| `POST` | `/api/world-clocks` | Добавить часы |
| `GET` | `/api/notes` | Получить заметку |
| `POST` | `/api/notes` | Сохранить заметку |

### Данные

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/backup/create` | Скачать бэкап базы |
| `POST` | `/api/backup/restore` | Восстановить из бэкапа |
| `GET` | `/api/events` | SSE для синхронизации между вкладками |

---

## 📁 Структура проекта

```
botyaranewtab/
├── app.py                  # Flask-приложение + все API-роуты
├── run.py                  # Точка входа с баннером
├── config.py               # Хост, порт, пути, версия
├── database.py             # Слой SQLite + миграции
├── utils.py                # Бэкапы, сканирование шрифтов
├── weather.py              # Интеграция с Open-Meteo
├── search_engine.py        # Bang-команды, калькулятор, конвертер
├── greetings.py            # 50+ приветствий по времени / языку
├── translations.py         # Строки i18n (en, ru)
├── favicon_parser.py       # Загрузка favicon + кэш
├── color_extractor.py      # Доминирующий цвет из картинок (Pillow)
│
├── templates/
│   └── index.html          # Одностраничный интерфейс
│
├── static/
│   ├── css/
│   │   └── style.css       # Все стили
│   ├── js/
│   │   ├── app.js          # Главный контроллер, синхронизация
│   │   ├── settings.js     # Логика модалки настроек
│   │   ├── search.js       # Строка поиска + превью
│   │   ├── shortcuts.js    # Сетка ссылок + папки
│   │   ├── widgets.js      # Часы, погода, счётчики
│   │   ├── background.js   # Движок обоев
│   │   ├── themes.js       # 15+ определений тем
│   │   ├── i18n.js         # Переводы на фронте
│   │   ├── hotkeys.js      # Горячие клавиши
│   │   ├── toast.js        # Уведомления
│   │   ├── confetti.js     # 🎉
│   │   └── sw.js           # Service worker (PWA)
│   ├── fonts/              # Inter, Geist, Manrope, Symbols
│   ├── backgrounds/        # Загруженные обои
│   ├── icons/              # Кэш favicon'ов
│   └── manifest.json       # PWA-манифест
│
├── docs/screenshots/       # Картинки для README
├── backups/                # Бэкапы базы
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 🛠️ Стек технологий

**Почему именно это:**

- **Flask** — лёгкий, без магии, легко расширять. Django — оверкилл, FastAPI — оверкилл, голый `http.server` — слишком скудно.
- **SQLite** — идеально для локальных одно-пользовательских приложений. Никакой установки, сервера, демона.
- **Чистый JS** — без сборки, без бандлера, без фреймворк-чехарды. Каждый файл загружается напрямую. Эта новая вкладка открывается **меньше чем за 50мс** на холодном кэше.
- **waitress** — продакшн-grade WSGI-сервер, без предупреждений Flask dev-сервера
- **rich** — красивый вывод в терминале
- **Pillow** — извлечение доминирующего цвета из обоев
- **BeautifulSoup** — парсинг favicon'ов со страниц
- **Open-Meteo** — погода без API-ключа

---

## 🤝 Участие в разработке

Это личный проект, но вклад приветствуется. Пара правил:

1. **Сначала issue** для крупных изменений — возможно, я уже что-то планирую
2. **Сохраняй философию без сборки** — никаких npm, бандлеров, TypeScript
3. **Тестируй минимум в Chrome и Firefox**
4. **Одна фича на PR** — легче ревьюить
5. **Соблюдай существующий стиль** — модули, JSDoc-комментарии, `const` вместо `let`

Нашёл баг? [Открой issue](https://github.com/dimasbotyara/botyaranewtab/issues) с:
- Что делал
- Что ожидал
- Что произошло
- Браузер + ОС + версия Python
- Вывод консоли (F12 → Console), если есть

---

## 🥚 Пасхалка

В строке поиска спрятан маленький секрет. Попробуй ввести имя разработчика и нажать Enter.

<details>
<summary>⚠️ Спойлер — кликни, чтобы раскрыть</summary>

Набери **`dimasbotyara`** в строке поиска и нажми Enter. 🎉

</details>

---

## 📜 Лицензия

MIT — подробности в [LICENSE](LICENSE).

Ты можешь использовать этот код как угодно: личное, коммерческое, форкать, продавать, распечатать и повесить на стену. Просто оставь копирайт.

---

## 👤 Автор

**dimasbotyara**

- GitHub: [@dimasbotyara](https://github.com/dimasbotyara)
- Проект: [botyaranewtab](https://github.com/dimasbotyara/botyaranewtab)

---

<div align="center">

**Если проект оказался полезен — поставь ⭐, это греет душу**

Сделано с 🌙 и слишком большим количеством кофе

</div>
