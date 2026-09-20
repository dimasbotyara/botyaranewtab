/* Search module */
const Search = {
    input: null,
    preview: null,
    autocomplete: null,
    engineBtn: null,
    engineIcon: null,
    addBtn: null,
    engines: {
        google: { icon: '󰊭', type: 'nf' },
        yandex: { icon: 'Y', type: 'text' },
        duckduckgo: { icon: '󰇥', type: 'nf' }
    },
    debounceTimer: null,

    init() {
        this.input = document.getElementById('search-input');
        this.preview = document.getElementById('search-preview');
        this.autocomplete = document.getElementById('search-autocomplete');
        this.engineBtn = document.getElementById('search-engine-btn');
        this.engineIcon = document.getElementById('search-engine-icon');
        this.addBtn = document.getElementById('search-add-btn');

        this.updatePlaceholder();
        this.bindEvents();
    },

    bindEvents() {
        this.input.addEventListener('input', () => {
            clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => this.onInput(), 150);
        });

        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.submit();
            } else if (e.key === 'Escape') {
                this.clear();
            } else if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                this.navigateAutocomplete(e);
            }
        });

        this.engineBtn.addEventListener('click', () => this.cycleEngine());
        this.addBtn.addEventListener('click', () => this.quickAdd());

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                this.hideAutocomplete();
                this.hidePreview();
            }
        });
    },

    updatePlaceholder() {
        const engine = App.settings.search_engine || 'google';
        const names = { google: 'Google', yandex: 'Yandex', duckduckgo: 'DuckDuckGo' };
        this.input.placeholder = I18n.t('or_type_url', `Search ${names[engine]} or enter URL…`);

        const engineData = this.engines[engine] || this.engines.google;
        if (engineData.type === 'nf') {
            this.engineIcon.className = 'nf search-engine-icon-nf';
        } else {
            this.engineIcon.className = 'search-engine-icon-text';
        }
        this.engineIcon.textContent = engineData.icon;
    },

    cycleEngine() {
        const order = ['google', 'yandex', 'duckduckgo'];
        const current = App.settings.search_engine || 'google';
        const idx = (order.indexOf(current) + 1) % order.length;
        App.updateSetting('search_engine', order[idx]);
        this.updatePlaceholder();
        Toast.info(`${order[idx].charAt(0).toUpperCase() + order[idx].slice(1)}`);
    },

    async onInput() {
        const q = this.input.value.trim();

        if (!q) {
            this.hidePreview();
            this.hideAutocomplete();
            this.addBtn.classList.add('hidden');
            return;
        }

        if (this.isUrl(q)) {
            this.addBtn.classList.remove('hidden');
        } else {
            this.addBtn.classList.add('hidden');
        }

        try {
            const resp = await fetch(`/api/search/parse?q=${encodeURIComponent(q)}&engine=${App.settings.search_engine || 'google'}`);
            const result = await resp.json();

            if (result.type === 'calculator' && App.settings.search_calculator) {
                this.showPreview(`<div class="preview-calc"><span class="preview-expr">${result.expression}</span> = <span class="preview-result">${result.result}</span></div>`);
            } else if (result.type === 'color' && App.settings.search_color_preview) {
                this.showPreview(`<div class="preview-color"><div class="color-swatch" style="background:${result.color}"></div><span>${result.color}</span></div>`);
            } else if (result.type === 'conversion' && App.settings.search_unit_converter) {
                this.showPreview(`<div class="preview-conv">${result.value} ${result.from_unit} = <strong>${result.result} ${result.to_unit}</strong></div>`);
            } else {
                this.hidePreview();
            }
        } catch (e) {
            this.hidePreview();
        }

        if (App.settings.search_autocomplete && q.length >= 2) {
            try {
                const resp = await fetch(`/api/search/autocomplete?q=${encodeURIComponent(q)}`);
                const suggestions = await resp.json();
                if (suggestions.length > 0) {
                    this.showAutocomplete(suggestions);
                } else {
                    this.hideAutocomplete();
                }
            } catch (e) {
                this.hideAutocomplete();
            }
        } else {
            this.hideAutocomplete();
        }
    },

    async submit() {
        const q = this.input.value.trim();
        if (!q) return;

        try {
            const resp = await fetch(`/api/search/parse?q=${encodeURIComponent(q)}&engine=${App.settings.search_engine || 'google'}`);
            const result = await resp.json();

            if (result.type === 'command') {
                if (result.action === '__settings__') Settings.open();
                else if (result.action === '__confetti__') { Confetti.fire(); Toast.success(I18n.t('toast_confetti')); }
                else if (result.action === '__focus__') App.toggleFocusMode();
                else if (result.action === '__zen__') App.toggleZenMode();
                this.clear();
                return;
            }

            if (result.type === 'easter_egg') {
                Confetti.fire(5000);
                Toast.success(I18n.t('easter_egg_triggered'));
                this.clear();
                return;
            }

            if (result.type === 'redirect' || result.type === 'calculator' || result.type === 'color' || result.type === 'conversion') {
                window.location.href = result.search_url || result.url;
            }

            if (App.settings.search_history_enabled) {
                fetch('/api/search/history', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: q, engine: App.settings.search_engine })
                });
            }
        } catch (e) {
            const engine = App.settings.search_engine || 'google';
            const urls = { google: 'https://www.google.com/search?q=', yandex: 'https://yandex.ru/search/?text=', duckduckgo: 'https://duckduckgo.com/?q=' };
            window.location.href = (urls[engine] || urls.google) + encodeURIComponent(q);
        }
    },

    clear() {
        this.input.value = '';
        this.hidePreview();
        this.hideAutocomplete();
        this.addBtn.classList.add('hidden');
        this.input.blur();
    },

    showPreview(html) { this.preview.innerHTML = html; this.preview.classList.remove('hidden'); },
    hidePreview() { this.preview.classList.add('hidden'); },

    showAutocomplete(items) {
        this.autocomplete.innerHTML = items.map((item, i) =>
        `<div class="autocomplete-item${i === 0 ? ' selected' : ''}" data-query="${item}">${item}</div>`
        ).join('');
        this.autocomplete.classList.remove('hidden');

        this.autocomplete.querySelectorAll('.autocomplete-item').forEach(el => {
            el.addEventListener('click', () => {
                this.input.value = el.dataset.query;
                this.hideAutocomplete();
                this.submit();
            });
        });
    },

    hideAutocomplete() { this.autocomplete.classList.add('hidden'); },

    navigateAutocomplete(e) {
        const items = this.autocomplete.querySelectorAll('.autocomplete-item');
        if (!items.length) return;
        e.preventDefault();
        const current = this.autocomplete.querySelector('.autocomplete-item.selected');
        let next;
        if (e.key === 'ArrowDown') next = current?.nextElementSibling || items[0];
        else next = current?.previousElementSibling || items[items.length - 1];
        items.forEach(i => i.classList.remove('selected'));
        next.classList.add('selected');
        this.input.value = next.dataset.query;
    },

    isUrl(text) { return /^(https?:\/\/)?([\w-]+\.)+[\w-]+(:\d+)?(\/.*)?$/i.test(text); },

    async quickAdd() {
        const url = this.input.value.trim();
        if (!url) return;
        try {
            await fetch('/api/shortcuts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });
            Toast.success(I18n.t('toast_shortcut_added'));
            Shortcuts.load();
            this.clear();
        } catch (e) {
            Toast.error(I18n.t('toast_error'));
        }
    },

    focus() { this.input.focus(); }
};
