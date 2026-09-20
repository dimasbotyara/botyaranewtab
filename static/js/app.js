/* Main Application Controller */
const App = {
    settings: {},
    saveTimers: {},

    async init() {
        // 1. Load initial settings
        try {
            const resp = await fetch('/api/settings');
            this.settings = await resp.json();
        } catch (e) {
            console.error('Failed to load settings from server, using fallback', e);
            this.settings = {};
        }

        // 2. Init UI Modules
        await I18n.init();
        Toast.init();
        Confetti.init();
        Themes.apply(this.settings.theme || 'catppuccin-mocha');
        Background.init();
        Search.init();
        Shortcuts.init();
        Widgets.init();
        Settings.init();
        Hotkeys.init();

        // 3. Apply appearance & layouts
        this.applySettings(this.settings);

        // 4. First run onboarding flow
        if (this.settings.first_run) {
            this.showFirstRunModal();
        }

        // 5. Connect SSE for real-time live sync between tabs
        this.initSSE();

        // 6. Service worker registration
        if ('serviceWorker' in navigator && this.settings.pwa_enabled !== false) {
            navigator.serviceWorker.register('/sw.js').catch(err => {
                console.log('SW registration skipped:', err);
            });
        }

        // 7. Dynamic title updates
        Widgets.updateGreeting();
    },

    applySettings(s) {
        const root = document.documentElement;

        // Theme & Accents
        Themes.apply(s.theme || 'catppuccin-mocha');
        if (s.accent_color) {
            root.style.setProperty('--accent', s.accent_color);
        }

        // Auto theme (light by day, dark by night)
        if (s.auto_theme) {
            const hour = new Date().getHours();
            const isDay = hour >= 7 && hour < 19;
            const autoTheme = isDay ? (s.auto_theme_light || 'catppuccin-latte') : (s.auto_theme_dark || 'catppuccin-mocha');
            Themes.apply(autoTheme);
        }

        // Font Family
        if (s.font_family) {
            let fontStack = `'${s.font_family}', 'SymbolsNerdFont', system-ui, sans-serif`;
            if (s.font_family === 'System') fontStack = `system-ui, -apple-system, BlinkMacSystemFont, sans-serif, 'SymbolsNerdFont'`;
            if (s.font_family === 'Monospace') fontStack = `'Courier New', monospace, 'SymbolsNerdFont'`;
            root.style.setProperty('--font-main', fontStack);
        }

        // Font Sizes
        if (s.font_size_global) root.style.setProperty('--font-size-global', `${s.font_size_global}px`);
        if (s.font_size_clock) root.style.setProperty('--font-size-clock', `${s.font_size_clock}px`);
        if (s.font_size_greeting) root.style.setProperty('--font-size-greeting', `${s.font_size_greeting}px`);
        if (s.font_size_shortcuts) root.style.setProperty('--font-size-shortcuts', `${s.font_size_shortcuts}px`);

        // Corner Radius, Opacity, Blur
        if (s.border_radius !== undefined) root.style.setProperty('--radius', `${s.border_radius}px`);
        if (s.element_opacity !== undefined) root.style.setProperty('--element-opacity', s.element_opacity);
        if (s.backdrop_blur !== undefined) root.style.setProperty('--backdrop-blur', `${s.backdrop_blur}px`);

        // Layout (center / left / right)
        const main = document.getElementById('main-content');
        if (main) {
            main.className = `main-content layout-${s.layout || 'center'}`;
            if (s.compact_mode) main.classList.add('compact-mode');
            if (s.animation_type) main.classList.add(`anim-${s.animation_type}`);
        }

        // Background
        Background.apply(s);

        // Widgets
        Widgets.update(s);

        // Shortcuts
        Shortcuts.render();

        // Settings Button appearance & position
        this.updateSettingsButton(s);

        // Custom CSS injection
        const customStyle = document.getElementById('custom-css-style');
        if (customStyle) {
            customStyle.textContent = s.custom_css || '';
        }

        // Focus & Zen modes
        if (s.focus_mode) document.body.classList.add('mode-focus');
        else document.body.classList.remove('mode-focus');

        if (s.zen_mode) document.body.classList.add('mode-zen');
        else document.body.classList.remove('mode-zen');

        // Apply translations
        I18n.applyAll();
    },

    updateSetting(key, value, sync = true) {
        this.settings[key] = value;
        this.applySettings(this.settings);

        if (sync) {
            clearTimeout(this.saveTimers[key]);
            this.saveTimers[key] = setTimeout(() => {
                fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ [key]: value })
                }).catch(() => {});
            }, 250);
        }
    },

    updateSettingsButton(s) {
        const btn = document.getElementById('settings-btn');
        if (!btn) return;

        const style = s.settings_button_style || 'icon_corner';
        const pos = s.settings_button_position || 'bottom-right';

        btn.className = `settings-btn pos-${pos} style-${style}`;
        if (style === 'hidden') {
            btn.classList.add('hidden');
        } else {
            btn.classList.remove('hidden');
        }

        const iconSpan = btn.querySelector('.nf');
        if (style === 'text_only') {
            btn.innerHTML = `<span data-i18n="settings">${I18n.t('settings')}</span>`;
        } else if (style === 'icon_text') {
            btn.innerHTML = `<span class="nf">󰒓</span> <span data-i18n="settings">${I18n.t('settings')}</span>`;
        } else {
            btn.innerHTML = `<span class="nf">󰒓</span>`;
        }

        btn.onclick = () => Settings.toggle();

        // Right-click background open
        window.oncontextmenu = (e) => {
            if (s.settings_right_click && (e.target.id === 'bg-layer' || e.target.id === 'bg-overlay' || e.target.tagName === 'MAIN' || e.target.id === 'main-content')) {
                e.preventDefault();
                Settings.open();
            }
        };

        // Click greeting open
        const greetingEl = document.getElementById('widget-greeting');
        if (greetingEl) {
            greetingEl.style.cursor = s.settings_click_greeting ? 'pointer' : 'default';
            greetingEl.onclick = () => {
                if (s.settings_click_greeting) Settings.open();
            };
        }

        // Icon inside search bar
        const searchSettingsBtn = document.getElementById('search-settings-btn');
        if (searchSettingsBtn) {
            if (s.settings_in_search) {
                searchSettingsBtn.classList.remove('hidden');
                searchSettingsBtn.innerHTML = '<span class="nf">󰒓</span>';
                searchSettingsBtn.onclick = () => Settings.open();
            } else {
                searchSettingsBtn.classList.add('hidden');
            }
        }
    },

    toggleFocusMode() {
        const current = !this.settings.focus_mode;
        this.updateSetting('focus_mode', current);
        Toast.info(`Focus Mode: ${current ? I18n.t('enabled') : I18n.t('disabled')}`);
    },

    toggleZenMode() {
        const current = !this.settings.zen_mode;
        this.updateSetting('zen_mode', current);
        Toast.info(`Zen Mode: ${current ? I18n.t('enabled') : I18n.t('disabled')}`);
    },

    showFirstRunModal() {
        const modal = document.getElementById('first-run-modal');
        const input = document.getElementById('first-run-name');
        const goBtn = document.getElementById('first-run-go');
        const skipBtn = document.getElementById('first-run-skip');

        if (!modal) return;
        modal.classList.remove('hidden');

        const finish = (name = '') => {
            modal.classList.add('hidden');
            this.updateSetting('username', name.trim());
            this.updateSetting('first_run', false);
            Widgets.updateGreeting();
            Confetti.fire(3000);
            Toast.success(I18n.t('welcome'));
        };

        goBtn.onclick = () => finish(input.value);
        skipBtn.onclick = () => finish('');
        input.onkeydown = (e) => {
            if (e.key === 'Enter') finish(input.value);
        };
    },

    initSSE() {
        if (!window.EventSource) return;
        const evtSource = new EventSource('/api/events');
        evtSource.onmessage = (e) => {
            try {
                const msg = JSON.parse(e.data);
                if (msg.type === 'settings_updated') {
                    Object.assign(this.settings, msg.data);
                    this.applySettings(this.settings);
                }
            } catch (err) {}
        };
    }
};

document.addEventListener('DOMContentLoaded', () => App.init());
