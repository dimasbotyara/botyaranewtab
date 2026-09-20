/* Internationalization */
const I18n = {
    translations: {},
    currentLang: 'en',

    async init() {
        const resp = await fetch('/api/translations');
        this.translations = await resp.json();
        this.detectLanguage();
    },

    detectLanguage() {
        const saved = App?.settings?.language;
        if (saved && saved !== 'auto') {
            this.currentLang = saved;
        } else {
            const nav = navigator.language || 'en';
            this.currentLang = nav.startsWith('ru') ? 'ru' : 'en';
        }
    },

    setLanguage(lang) {
        if (lang === 'auto') {
            const nav = navigator.language || 'en';
            this.currentLang = nav.startsWith('ru') ? 'ru' : 'en';
        } else {
            this.currentLang = lang;
        }
        this.applyAll();
    },

    t(key, fallback) {
        const dict = this.translations[this.currentLang] || this.translations['en'] || {};
        return dict[key] || fallback || key;
    },

    applyAll() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            el.textContent = this.t(el.dataset.i18n);
        });
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            el.placeholder = this.t(el.dataset.i18nPlaceholder || el.getAttribute('data-i18n-placeholder'));
        });
    }
};
