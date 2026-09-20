/* Widgets module */
const Widgets = {
    clockInterval: null,
    notesSaveTimer: null,
    weatherCache: null,
    weatherLastFetch: 0,

    init() {
        this.startClock();
        this.updateGreeting();
    },

    update(settings) {
        const s = settings;

        // Clock
        this.toggle('widget-clock', s.widget_clock);

        // Greeting
        this.toggle('widget-greeting', s.widget_greeting);

        // Day progress
        this.toggle('widget-day-progress', s.widget_day_progress);
        if (s.widget_day_progress) this.updateProgress();

        // Weather
        this.toggle('widget-weather', s.widget_weather);
        if (s.widget_weather) this.loadWeather(s);

        // Notes
        this.toggle('widget-notes', s.widget_notes);
        if (s.widget_notes) this.initNotes();

        // Countdowns
        this.toggle('widget-countdowns', s.widget_countdowns);
        if (s.widget_countdowns) this.loadCountdowns();

        // World clocks
        this.toggle('widget-world-clocks', s.widget_world_clocks);
        if (s.widget_world_clocks) this.loadWorldClocks();

        // Calendar
        this.toggle('widget-calendar', s.widget_calendar);
        if (s.widget_calendar) this.renderCalendar();
    },

    toggle(id, show) {
        const el = document.getElementById(id);
        if (el) {
            if (show) el.classList.remove('hidden');
            else el.classList.add('hidden');
        }
    },

    startClock() {
        const update = () => {
            const now = new Date();
            const timeEl = document.getElementById('clock-time');
            const dateEl = document.getElementById('clock-date');
            const s = App.settings;

            if (timeEl) {
                const is12h = s.clock_format === '12h';
                const opts = {
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: is12h,
                };
                if (s.clock_show_seconds) opts.second = '2-digit';
                timeEl.textContent = now.toLocaleTimeString([], opts);
            }
            if (dateEl) {
                const lang = I18n.currentLang === 'ru' ? 'ru-RU' : 'en-US';
                dateEl.textContent = now.toLocaleDateString(lang, {
                    weekday: 'long', day: 'numeric', month: 'long'
                });
            }

            // Update title
            this.updateTitle(now);

            // Update progress
            if (App.settings.widget_day_progress) this.updateProgress(now);
        };

            update();
            this.clockInterval = setInterval(update, 1000);
    },

    updateTitle(now) {
        const s = App.settings;
        let template = s.title_template || '🌙 {time} — botyaranewtab';
        const time = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const lang = I18n.currentLang === 'ru' ? 'ru-RU' : 'en-US';
        const date = now.toLocaleDateString(lang, { day: 'numeric', month: 'short' });

        template = template.replace('{time}', time);
        template = template.replace('{date}', date);
        template = template.replace('{name}', s.username || '');
        template = template.replace('{greeting}', document.getElementById('greeting-text')?.textContent || '');

        document.title = template;
    },

    async updateGreeting() {
        const now = new Date();
        const hour = now.getHours();
        const s = App.settings;
        const lang = I18n.currentLang;
        const name = s.username || '';

        try {
            const resp = await fetch(`/api/greeting?hour=${hour}&lang=${lang}&name=${encodeURIComponent(name)}`);
            const data = await resp.json();
            const greetingEl = document.getElementById('greeting-text');
            if (greetingEl) {
                greetingEl.textContent = data.greeting;
            }
        } catch (e) {
            console.error('Greeting error:', e);
        }

        // Refresh greeting every 5 minutes
        setTimeout(() => this.updateGreeting(), 5 * 60 * 1000);
    },

    updateProgress(now) {
        now = now || new Date();

        // Day progress
        const dayStart = new Date(now);
        dayStart.setHours(0, 0, 0, 0);
        const dayPct = Math.round(((now - dayStart) / 86400000) * 100);
        const dayFill = document.getElementById('day-progress-fill');
        const dayPctEl = document.getElementById('day-progress-pct');
        if (dayFill) dayFill.style.width = dayPct + '%';
        if (dayPctEl) dayPctEl.textContent = dayPct + '%';

        // Month progress
        const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
        const monthPct = Math.round((now.getDate() / daysInMonth) * 100);
        const monthFill = document.getElementById('month-progress-fill');
        const monthPctEl = document.getElementById('month-progress-pct');
        if (monthFill) monthFill.style.width = monthPct + '%';
        if (monthPctEl) monthPctEl.textContent = monthPct + '%';
    },

    async loadWeather(s) {
        s = s || App.settings;
        if (!s.weather_lat || !s.weather_lon) return;
        if (Date.now() - this.weatherLastFetch < 600000 && this.weatherCache) {
            this.renderWeather(this.weatherCache);
            return;
        }

        try {
            const resp = await fetch(`/api/weather?lat=${s.weather_lat}&lon=${s.weather_lon}&units=${s.weather_units || 'celsius'}`);
            const data = await resp.json();
            if (!data.error) {
                this.weatherCache = data;
                this.weatherLastFetch = Date.now();
                this.renderWeather(data);
            }
        } catch (e) {
            console.error('Weather error:', e);
        }
    },

    renderWeather(data) {
        document.getElementById('weather-icon').textContent = data.icon;
        document.getElementById('weather-temp').textContent = `${data.temperature}${data.unit}`;
        const descKey = I18n.currentLang === 'ru' ? 'description_ru' : 'description_en';
        document.getElementById('weather-desc').textContent = data[descKey];
    },

    async initNotes() {
        const textarea = document.getElementById('notes-textarea');
        if (!textarea) return;

        try {
            const resp = await fetch('/api/notes');
            const data = await resp.json();
            textarea.value = data.content || '';
        } catch (e) {}

        textarea.removeEventListener('input', this._noteHandler);
        this._noteHandler = () => {
            clearTimeout(this.notesSaveTimer);
            this.notesSaveTimer = setTimeout(() => {
                fetch('/api/notes', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: textarea.value })
                });
            }, 500);
        };
        textarea.addEventListener('input', this._noteHandler);
    },

    async loadCountdowns() {
        try {
            const resp = await fetch('/api/countdowns');
            const data = await resp.json();
            const container = document.getElementById('widget-countdowns');
            if (!container) return;

            const now = new Date();
            let html = data.map(cd => {
                const target = new Date(cd.target_date);
                const diff = Math.ceil((target - now) / 86400000);
                const label = diff >= 0 ? `${diff} ${I18n.t('days_left')}` : `${Math.abs(diff)} ${I18n.t('days_ago')}`;

                return `<div class="countdown-item">${cd.emoji} <strong>${cd.title}</strong>: ${label}</div>`;
            }).join('');

            container.innerHTML = html || `<div class="widget-empty">${I18n.t('no_results')}</div>`;
        } catch (e) {}
    },

    async loadWorldClocks() {
        try {
            const resp = await fetch('/api/world-clocks');
            const data = await resp.json();
            const container = document.getElementById('widget-world-clocks');
            if (!container) return;

            const html = data.map(wc => {
                let time;
                try {
                    time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', timeZone: wc.timezone });
                } catch (e) {
                    time = '??:??';
                }
                return `<div class="world-clock-item"><span class="wc-label">${wc.label}</span><span class="wc-time">${time}</span></div>`;
            }).join('');

            container.innerHTML = html || '';
        } catch (e) {}
    },

    renderCalendar() {
        const container = document.getElementById('widget-calendar');
        if (!container) return;

        const now = new Date();
        const year = now.getFullYear();
        const month = now.getMonth();
        const today = now.getDate();
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        const lang = I18n.currentLang === 'ru' ? 'ru-RU' : 'en-US';
        const monthName = now.toLocaleDateString(lang, { month: 'long', year: 'numeric' });

        const dayNames = I18n.currentLang === 'ru'
            ? ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
            : ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];

        let html = `<div class="cal-header">${monthName}</div>`;
        html += `<div class="cal-grid">`;
        dayNames.forEach(d => html += `<div class="cal-day-name">${d}</div>`);

        // Adjust for Monday start
        const startDay = (firstDay + 6) % 7;
        for (let i = 0; i < startDay; i++) {
            html += `<div class="cal-day empty"></div>`;
        }
        for (let d = 1; d <= daysInMonth; d++) {
            const cls = d === today ? 'cal-day today' : 'cal-day';
            html += `<div class="${cls}">${d}</div>`;
        }
        html += `</div>`;

        container.innerHTML = html;
    }
};
