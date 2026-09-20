/* Settings modal controller — full version */
const Settings = {
    modal: null,
    lastTab: 'general',
    isOpen: false,

    init() {
        this.modal = document.getElementById('settings-modal');
        document.querySelectorAll('.settings-tab').forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });
        document.getElementById('settings-close-btn')?.addEventListener('click', () => this.close());
        document.querySelector('.settings-backdrop')?.addEventListener('click', () => this.close());
        this.bindInputs();
        this.bindButtons();
    },

    open(tab) {
        if (tab) this.lastTab = tab;
        this.switchTab(this.lastTab);
        this.loadCurrentValues();
        this.modal.classList.remove('hidden');
        requestAnimationFrame(() => this.modal.classList.add('open'));
        this.isOpen = true;
    },

    close() {
        this.modal.classList.remove('open');
        setTimeout(() => this.modal.classList.add('hidden'), 200);
        this.isOpen = false;
    },

    toggle() { if (this.isOpen) this.close(); else this.open(); },

    switchTab(tabId) {
        this.lastTab = tabId;
        document.querySelectorAll('.settings-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tabId));
        document.querySelectorAll('.settings-panel').forEach(p => p.classList.toggle('active', p.dataset.panel === tabId));
        if (tabId === 'background') this.loadBackgroundImages();
        if (tabId === 'shortcuts') this.loadShortcutsList();
        if (tabId === 'appearance') { this.loadThemeGrid(); this.loadAccentPalette(); }
        if (tabId === 'widgets') this.loadWidgetSettings();
    },

    loadCurrentValues() {
        const s = App.settings;
        this.setVal('set-language', s.language);
        this.setVal('set-username', s.username);
        this.setVal('set-title-template', s.title_template);
        this.setVal('set-settings-btn-style', s.settings_button_style);
        this.setVal('set-settings-btn-pos', s.settings_button_position);
        this.setChecked('set-right-click', s.settings_right_click);
        this.setChecked('set-click-greeting', s.settings_click_greeting);
        this.setChecked('set-in-search', s.settings_in_search);
        this.setChecked('set-focus-mode', s.focus_mode);
        this.setChecked('set-zen-mode', s.zen_mode);
        this.setVal('set-accent-color', s.accent_color);
        this.setVal('set-accent-color-hex', s.accent_color);
        this.setChecked('set-auto-theme', s.auto_theme);
        this.setVal('set-animation', s.animation_type);
        this.setChecked('set-compact', s.compact_mode);
        this.setRange('set-font-global', s.font_size_global, 'val-font-global');
        this.setRange('set-font-clock', s.font_size_clock, 'val-font-clock');
        this.setRange('set-font-greeting', s.font_size_greeting, 'val-font-greeting');
        this.setRange('set-font-shortcuts', s.font_size_shortcuts, 'val-font-shortcuts');
        this.setRange('set-border-radius', s.border_radius, 'val-border-radius');
        this.setRange('set-opacity', s.element_opacity, 'val-opacity', v => Math.round(v * 100));
        this.setRange('set-backdrop-blur', s.backdrop_blur, 'val-backdrop-blur');
        this.setVal('set-bg-scale', s.bg_scale_mode);
        this.setVal('set-bg-solid-color', s.bg_solid_color);
        this.setVal('set-bg-grad-from', s.bg_gradient_from);
        this.setVal('set-bg-grad-to', s.bg_gradient_to);
        this.setRange('set-bg-grad-angle', s.bg_gradient_angle, 'val-bg-grad-angle');
        this.setRange('set-bg-blur', s.bg_blur, 'val-bg-blur');
        this.setRange('set-bg-dim', s.bg_dim, 'val-bg-dim');
        this.setRange('set-bg-brightness', s.bg_brightness, 'val-bg-brightness');
        this.setRange('set-bg-saturation', s.bg_saturation, 'val-bg-saturation');
        this.setRange('set-bg-sepia', s.bg_sepia, 'val-bg-sepia');
        this.setChecked('set-bg-grayscale', s.bg_grayscale);
        this.setChecked('set-bg-vignette', s.bg_vignette);
        this.setChecked('set-bg-parallax', s.bg_parallax);
        this.setChecked('set-bg-ken-burns', s.bg_ken_burns);
        this.setChecked('set-bg-adaptive', s.bg_adaptive_color);
        this.setChecked('set-bg-rotate', s.bg_rotate_enabled);
        this.setRange('set-bg-rotate-interval', s.bg_rotate_interval, 'val-bg-rotate-interval');
        document.querySelectorAll('.bg-src-btn').forEach(b => b.classList.toggle('active', b.dataset.source === s.bg_source));
        this.toggleBgSubOptions(s.bg_source);
        document.querySelectorAll('.pos-btn').forEach(b => b.classList.toggle('active', b.dataset.pos === s.bg_position));
        document.querySelectorAll('.layout-btn').forEach(b => b.classList.toggle('active', b.dataset.layout === s.layout));
        this.setVal('set-search-engine', s.search_engine);
        this.setChecked('set-search-bangs', s.search_bangs);
        this.setChecked('set-search-history', s.search_history_enabled);
        this.setChecked('set-search-autocomplete', s.search_autocomplete);
        this.setChecked('set-search-calculator', s.search_calculator);
        this.setChecked('set-search-color', s.search_color_preview);
        this.setChecked('set-search-units', s.search_unit_converter);
        this.setVal('set-shortcuts-size', s.shortcuts_size);
        this.setChecked('set-shortcuts-labels', s.shortcuts_show_labels);
        this.setRange('set-shortcuts-cols', s.shortcuts_columns, 'val-shortcuts-cols', v => v === 0 ? 'auto' : v);
        this.setChecked('set-widget-clock', s.widget_clock);
        this.setVal('set-clock-format', s.clock_format || '24h');
        this.setChecked('set-clock-seconds', s.clock_show_seconds);
        document.getElementById('clock-settings')?.classList.toggle('hidden', !s.widget_clock);
        this.setChecked('set-widget-greeting', s.widget_greeting);
        this.setChecked('set-widget-day-progress', s.widget_day_progress);
        this.setChecked('set-widget-weather', s.widget_weather);
        this.setChecked('set-widget-notes', s.widget_notes);
        this.setChecked('set-widget-countdowns', s.widget_countdowns);
        this.setChecked('set-widget-world-clocks', s.widget_world_clocks);
        this.setChecked('set-widget-calendar', s.widget_calendar);
        this.setChecked('set-sound-enabled', s.sound_enabled);
        this.setVal('set-custom-css', s.custom_css);
        this.loadFontsDropdown(s.font_family);
        this.setVal('set-weather-city', s.weather_city || '');
        this.setVal('set-weather-units', s.weather_units || 'celsius');
        // Update swatch
        const swatch = document.getElementById('accent-color-swatch');
        if (swatch) swatch.style.background = s.accent_color;
        // Rotate visibility
        document.getElementById('bg-rotate-interval-group').style.display = s.bg_rotate_enabled ? '' : 'none';
        // Widget sub-settings
        document.getElementById('weather-settings')?.classList.toggle('hidden', !s.widget_weather);
        document.getElementById('countdowns-settings')?.classList.toggle('hidden', !s.widget_countdowns);
        document.getElementById('world-clocks-settings')?.classList.toggle('hidden', !s.widget_world_clocks);
        Background.updatePreview(s);
    },

    loadAccentPalette() {
        const palette = document.getElementById('accent-palette');
        if (!palette) return;

        const currentTheme = App.settings.theme || 'catppuccin-mocha';
        const theme = Themes.list[currentTheme];

        // Build a palette from the current theme + popular palettes
        const colors = new Set();

        // Current theme accents
        if (theme?.colors) {
            for (const [key, val] of Object.entries(theme.colors)) {
                if (!key.includes('bg-') && !key.includes('text-') && !key.includes('border') && val.startsWith('#')) {
                    colors.add(val);
                }
            }
        }

        // Extra popular accent colors
        const extras = [
            '#cba6f7', '#f38ba8', '#a6e3a1', '#89b4fa', '#f9e2af', '#f5c2e7', '#fab387', '#94e2d5', '#b4befe',
            '#c6a0f6', '#ed8796', '#a6da95', '#8aadf4', '#eed49f', '#f5bde6',
            '#bd93f9', '#ff79c6', '#50fa7b', '#8be9fd', '#f1fa8c',
            '#7aa2f7', '#bb9af7', '#9ece6a', '#7dcfff', '#e0af68', '#f7768e',
            '#88c0d0', '#81a1c1', '#a3be8c', '#bf616a', '#ebcb8b', '#b48ead',
            '#fabd2f', '#fe8019', '#b8bb26', '#83a598', '#fb4934',
            '#7c3aed', '#a855f7', '#f43f5e', '#34d399', '#fbbf24',
        ];
        extras.forEach(c => colors.add(c));

        const currentAccent = App.settings.accent_color || '#cba6f7';

        palette.innerHTML = Array.from(colors).map(c => `
        <button class="accent-dot ${c === currentAccent ? 'active' : ''}" data-color="${c}"
        style="background:${c}" title="${c}"></button>
        `).join('');

        palette.querySelectorAll('.accent-dot').forEach(dot => {
            dot.addEventListener('click', () => {
                const color = dot.dataset.color;
                palette.querySelectorAll('.accent-dot').forEach(d => d.classList.toggle('active', d.dataset.color === color));
                App.updateSetting('accent_color', color);
                document.getElementById('set-accent-color').value = color;
                document.getElementById('set-accent-color-hex').value = color;
                const swatch = document.getElementById('accent-color-swatch');
                if (swatch) swatch.style.background = color;
            });
        });
    },

    bindInputs() {
        const autoSave = (id, key, transform) => {
            const el = document.getElementById(id);
            if (!el) return;
            const event = el.type === 'checkbox' ? 'change' : 'input';
            el.addEventListener(event, () => {
                let value;
                if (el.type === 'checkbox') value = el.checked;
                else if (el.type === 'range') value = parseFloat(el.value);
                else value = el.value;
                if (transform) value = transform(value);
                App.updateSetting(key, value);
                Background.updatePreview(App.settings);
            });
        };

        autoSave('set-language', 'language', v => { I18n.setLanguage(v); return v; });
        autoSave('set-username', 'username');
        autoSave('set-title-template', 'title_template');
        autoSave('set-settings-btn-style', 'settings_button_style');
        autoSave('set-settings-btn-pos', 'settings_button_position');
        autoSave('set-right-click', 'settings_right_click');
        autoSave('set-click-greeting', 'settings_click_greeting');
        autoSave('set-in-search', 'settings_in_search');
        autoSave('set-focus-mode', 'focus_mode');
        autoSave('set-zen-mode', 'zen_mode');
        autoSave('set-accent-color', 'accent_color');
        autoSave('set-auto-theme', 'auto_theme');
        autoSave('set-animation', 'animation_type');
        autoSave('set-compact', 'compact_mode');
        autoSave('set-font-global', 'font_size_global');
        autoSave('set-font-clock', 'font_size_clock');
        autoSave('set-font-greeting', 'font_size_greeting');
        autoSave('set-font-shortcuts', 'font_size_shortcuts');
        autoSave('set-border-radius', 'border_radius');
        autoSave('set-opacity', 'element_opacity');
        autoSave('set-backdrop-blur', 'backdrop_blur');
        autoSave('set-custom-css', 'custom_css');

        document.getElementById('set-accent-color')?.addEventListener('input', (e) => {
            document.getElementById('set-accent-color-hex').value = e.target.value;
            const swatch = document.getElementById('accent-color-swatch');
            if (swatch) swatch.style.background = e.target.value;
        });
            document.getElementById('set-accent-color-hex')?.addEventListener('input', (e) => {
                const v = e.target.value.trim();
                if (/^#[0-9a-f]{6}$/i.test(v)) {
                    document.getElementById('set-accent-color').value = v;
                    App.updateSetting('accent_color', v);
                    const swatch = document.getElementById('accent-color-swatch');
                    if (swatch) swatch.style.background = v;
                }
            });

            autoSave('set-bg-scale', 'bg_scale_mode');
            autoSave('set-bg-solid-color', 'bg_solid_color');
            autoSave('set-bg-grad-from', 'bg_gradient_from');
            autoSave('set-bg-grad-to', 'bg_gradient_to');
            autoSave('set-bg-grad-angle', 'bg_gradient_angle');
            autoSave('set-bg-blur', 'bg_blur');
            autoSave('set-bg-dim', 'bg_dim');
            autoSave('set-bg-brightness', 'bg_brightness');
            autoSave('set-bg-saturation', 'bg_saturation');
            autoSave('set-bg-sepia', 'bg_sepia');
            autoSave('set-bg-grayscale', 'bg_grayscale');
            autoSave('set-bg-vignette', 'bg_vignette');
            autoSave('set-bg-parallax', 'bg_parallax');
            autoSave('set-bg-ken-burns', 'bg_ken_burns');
            autoSave('set-bg-adaptive', 'bg_adaptive_color');
            autoSave('set-bg-rotate', 'bg_rotate_enabled');
            autoSave('set-bg-rotate-interval', 'bg_rotate_interval');
            autoSave('set-search-engine', 'search_engine');
            autoSave('set-search-bangs', 'search_bangs');
            autoSave('set-search-history', 'search_history_enabled');
            autoSave('set-search-autocomplete', 'search_autocomplete');
            autoSave('set-search-calculator', 'search_calculator');
            autoSave('set-search-color', 'search_color_preview');
            autoSave('set-search-units', 'search_unit_converter');
            autoSave('set-shortcuts-size', 'shortcuts_size');
            autoSave('set-shortcuts-labels', 'shortcuts_show_labels');
            autoSave('set-shortcuts-cols', 'shortcuts_columns');
            autoSave('set-widget-clock', 'widget_clock');
            autoSave('set-clock-format', 'clock_format');
            autoSave('set-clock-seconds', 'clock_show_seconds');
            autoSave('set-widget-greeting', 'widget_greeting');
            autoSave('set-widget-day-progress', 'widget_day_progress');
            autoSave('set-widget-weather', 'widget_weather');
            autoSave('set-widget-notes', 'widget_notes');
            autoSave('set-widget-countdowns', 'widget_countdowns');
            autoSave('set-widget-world-clocks', 'widget_world_clocks');
            autoSave('set-widget-calendar', 'widget_calendar');
            autoSave('set-weather-units', 'weather_units');
            autoSave('set-sound-enabled', 'sound_enabled');

            document.getElementById('set-font-family')?.addEventListener('change', (e) => {
                App.updateSetting('font_family', e.target.value);
            });

            // Range value displays
            this.bindRangeDisplay('set-font-global', 'val-font-global');
            this.bindRangeDisplay('set-font-clock', 'val-font-clock');
            this.bindRangeDisplay('set-font-greeting', 'val-font-greeting');
            this.bindRangeDisplay('set-font-shortcuts', 'val-font-shortcuts');
            this.bindRangeDisplay('set-border-radius', 'val-border-radius');
            this.bindRangeDisplay('set-opacity', 'val-opacity', v => Math.round(v * 100));
            this.bindRangeDisplay('set-backdrop-blur', 'val-backdrop-blur');
            this.bindRangeDisplay('set-bg-grad-angle', 'val-bg-grad-angle');
            this.bindRangeDisplay('set-bg-blur', 'val-bg-blur');
            this.bindRangeDisplay('set-bg-dim', 'val-bg-dim');
            this.bindRangeDisplay('set-bg-brightness', 'val-bg-brightness');
            this.bindRangeDisplay('set-bg-saturation', 'val-bg-saturation');
            this.bindRangeDisplay('set-bg-sepia', 'val-bg-sepia');
            this.bindRangeDisplay('set-bg-rotate-interval', 'val-bg-rotate-interval');
            this.bindRangeDisplay('set-shortcuts-cols', 'val-shortcuts-cols', v => v == 0 ? 'auto' : v);

            // Background source
            document.querySelectorAll('.bg-src-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.bg-src-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    App.updateSetting('bg_source', btn.dataset.source);
                    this.toggleBgSubOptions(btn.dataset.source);
                    Background.updatePreview(App.settings);
                });
            });

            document.querySelectorAll('.pos-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.pos-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    App.updateSetting('bg_position', btn.dataset.pos);
                    Background.updatePreview(App.settings);
                });
            });

            document.querySelectorAll('.layout-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.layout-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    App.updateSetting('layout', btn.dataset.layout);
                });
            });

            document.querySelectorAll('.ratio-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.ratio-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    const preview = document.getElementById('bg-preview');
                    if (preview) { preview.className = 'bg-preview'; preview.classList.add(`ratio-${btn.dataset.ratio.replace(':', '-')}`); }
                });
            });

            document.getElementById('set-bg-rotate')?.addEventListener('change', (e) => {
                document.getElementById('bg-rotate-interval-group').style.display = e.target.checked ? '' : 'none';
            });

            document.getElementById('set-widget-clock')?.addEventListener('change', (e) => {
                document.getElementById('clock-settings')?.classList.toggle('hidden', !e.target.checked);
            });
            document.getElementById('set-widget-weather')?.addEventListener('change', (e) => {
                document.getElementById('weather-settings')?.classList.toggle('hidden', !e.target.checked);
            });
            document.getElementById('set-widget-countdowns')?.addEventListener('change', (e) => {
                document.getElementById('countdowns-settings')?.classList.toggle('hidden', !e.target.checked);
            });
            document.getElementById('set-widget-world-clocks')?.addEventListener('change', (e) => {
                document.getElementById('world-clocks-settings')?.classList.toggle('hidden', !e.target.checked);
            });
    },

    bindButtons() {
        document.getElementById('btn-upload-bg')?.addEventListener('click', () => document.getElementById('input-upload-bg').click());
        document.getElementById('input-upload-bg')?.addEventListener('change', (e) => this.handleBgUpload(e));
        document.getElementById('btn-install-font')?.addEventListener('click', () => document.getElementById('input-install-font').click());
        document.getElementById('input-install-font')?.addEventListener('change', (e) => this.handleFontInstall(e));
        document.getElementById('btn-import-bookmarks')?.addEventListener('click', () => document.getElementById('input-import-bookmarks').click());
        document.getElementById('input-import-bookmarks')?.addEventListener('change', async (e) => {
            const file = e.target.files[0]; if (!file) return;
            const fd = new FormData(); fd.append('file', file);
            const resp = await fetch('/api/shortcuts/import', { method: 'POST', body: fd });
            const data = await resp.json();
            Toast.success(`Imported ${data.added || 0} shortcuts`);
            Shortcuts.load(); this.loadShortcutsList();
        });
        document.getElementById('btn-clear-history')?.addEventListener('click', async () => { await fetch('/api/search/history', { method: 'DELETE' }); Toast.success(I18n.t('search_history_cleared')); });
        document.getElementById('btn-restore-backup')?.addEventListener('click', () => document.getElementById('input-restore-backup').click());
        document.getElementById('input-restore-backup')?.addEventListener('change', async (e) => {
            const file = e.target.files[0]; if (!file) return;
            const fd = new FormData(); fd.append('file', file);
            const resp = await fetch('/api/backup/restore', { method: 'POST', body: fd });
            if (resp.ok) { Toast.success(I18n.t('toast_backup_restored')); setTimeout(() => location.reload(), 500); }
            else Toast.error(I18n.t('toast_error'));
        });
            document.getElementById('btn-import-settings')?.addEventListener('click', () => document.getElementById('input-import-settings').click());
            document.getElementById('input-import-settings')?.addEventListener('change', async (e) => {
                const file = e.target.files[0]; if (!file) return;
                const fd = new FormData(); fd.append('file', file);
                const resp = await fetch('/api/settings/import', { method: 'POST', body: fd });
                if (resp.ok) { Toast.success(I18n.t('toast_settings_imported')); setTimeout(() => location.reload(), 500); }
            });
            document.getElementById('btn-reset-all')?.addEventListener('click', async () => {
                if (!confirm(I18n.t('reset_confirm'))) return;
                await fetch('/api/settings/reset', { method: 'POST' });
                Toast.success(I18n.t('toast_settings_reset')); setTimeout(() => location.reload(), 500);
            });
            document.getElementById('btn-weather-detect')?.addEventListener('click', () => {
                if (!navigator.geolocation) { Toast.error('Geolocation not supported'); return; }
                navigator.geolocation.getCurrentPosition(async (pos) => {
                    const lat = pos.coords.latitude;
                    const lon = pos.coords.longitude;
                    App.updateSetting('weather_lat', lat);
                    App.updateSetting('weather_lon', lon);
                    try {
                        const resp = await fetch(`/api/weather/reverse?lat=${lat}&lon=${lon}`);
                        const data = await resp.json();
                        if (data.name) {
                            App.updateSetting('weather_city', data.name);
                            const cityInput = document.getElementById('set-weather-city');
                            if (cityInput) cityInput.value = data.name;
                            Toast.success(`📍 ${data.name}`);
                        } else {
                            Toast.success('Location detected!');
                        }
                    } catch (e) {
                        Toast.success('Location detected!');
                    }
                    Widgets.weatherCache = null;
                    Widgets.weatherLastFetch = 0;
                    Widgets.loadWeather(App.settings);
                }, () => Toast.error('Geolocation denied'));
            });

            const cityInput = document.getElementById('set-weather-city');
            if (cityInput) {
                cityInput.addEventListener('input', (e) => {
                    App.updateSetting('weather_city', e.target.value.trim());
                });
                const geocodeCity = async () => {
                    const city = cityInput.value.trim();
                    if (!city) return;
                    try {
                        const resp = await fetch(`/api/weather/geocode?city=${encodeURIComponent(city)}`);
                        const data = await resp.json();
                        console.log('[GEOCODE] response:', data);
                        console.log('[GEOCODE] data.lat type:', typeof data.lat, 'value:', data.lat);
                        if (data.lat) {
                            App.updateSetting('weather_city', data.name);
                            App.updateSetting('weather_lat', data.lat);
                            App.updateSetting('weather_lon', data.lon);
                            console.log('[GEOCODE] after 3 calls, App.settings:',
                                        App.settings.weather_city,
                                        App.settings.weather_lat,
                                        App.settings.weather_lon);
                            cityInput.value = data.name;
                            Toast.success(`📍 ${data.name}, ${data.country}`);
                            Widgets.weatherCache = null;
                            Widgets.weatherLastFetch = 0;
                            Widgets.loadWeather(App.settings);
                        } else {
                            Toast.error('City not found');
                        }
                    } catch (err) {
                        Toast.error('City not found');
                    }
                };
                cityInput.addEventListener('change', geocodeCity);
                cityInput.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter') { e.preventDefault(); geocodeCity(); }
                });
            }
            document.getElementById('btn-add-countdown')?.addEventListener('click', async () => {
                const title = prompt(I18n.t('countdown_title')); if (!title) return;
                const date = prompt(I18n.t('countdown_date') + ' (YYYY-MM-DD)'); if (!date) return;
                const emoji = prompt(I18n.t('countdown_emoji'), '📅') || '📅';
                await fetch('/api/countdowns', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title, target_date: date, emoji }) });
                this.loadWidgetSettings(); Widgets.loadCountdowns();
            });
            document.getElementById('btn-add-world-clock')?.addEventListener('click', async () => {
                const label = prompt(I18n.t('world_clock_label') || 'Label'); if (!label) return;
                const tz = prompt(I18n.t('world_clock_tz') || 'Timezone (e.g. Asia/Tokyo)'); if (!tz) return;
                await fetch('/api/world-clocks', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ label, timezone: tz }) });
                this.loadWidgetSettings(); Widgets.loadWorldClocks();
            });

            // Add shortcut from settings
            document.getElementById('add-shortcut-btn-settings')?.addEventListener('click', () => Shortcuts.openModal());
    },

    async handleBgUpload(e) {
        const file = e.target.files[0]; if (!file) return;
        const fd = new FormData(); fd.append('file', file);
        const resp = await fetch('/api/backgrounds', { method: 'POST', body: fd });
        const bg = await resp.json();
        Toast.success(I18n.t('toast_bg_uploaded'));
        App.updateSetting('bg_source', 'image'); App.updateSetting('bg_image_id', bg.id);
        this.loadBackgroundImages();
    },

    async handleFontInstall(e) {
        const file = e.target.files[0]; if (!file) return;
        const fd = new FormData(); fd.append('file', file);
        const resp = await fetch('/api/fonts/install', { method: 'POST', body: fd });
        const data = await resp.json();
        if (data.ok) { Toast.success(I18n.t('toast_font_installed')); this.loadFontsDropdown(data.name); App.updateSetting('font_family', data.name); }
    },

    async loadBackgroundImages() {
        const grid = document.getElementById('bg-images-grid'); if (!grid) return;
        const resp = await fetch('/api/backgrounds');
        const images = await resp.json();
        Background.backgrounds = images;
        if (!images.length) { grid.innerHTML = `<div class="settings-hint">${I18n.t('bg_no_images')}</div>`; return; }
        grid.innerHTML = images.map(img => `
        <div class="bg-thumb-item ${App.settings.bg_image_id === img.id ? 'selected' : ''}" data-id="${img.id}">
        <img src="/static/backgrounds/${img.filename}" alt="${img.original_name || ''}">
        <button class="bg-thumb-del" data-id="${img.id}">✕</button>
        </div>
        `).join('');
        grid.querySelectorAll('.bg-thumb-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.classList.contains('bg-thumb-del')) return;
                const id = parseInt(item.dataset.id);
                App.updateSetting('bg_source', 'image'); App.updateSetting('bg_image_id', id);
                grid.querySelectorAll('.bg-thumb-item').forEach(i => i.classList.toggle('selected', parseInt(i.dataset.id) === id));
                Background.updatePreview(App.settings);
            });
        });
        grid.querySelectorAll('.bg-thumb-del').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                if (!confirm(I18n.t('bg_delete_confirm'))) return;
                const id = parseInt(btn.dataset.id);
                await fetch(`/api/backgrounds/${id}`, { method: 'DELETE' });
                Toast.success(I18n.t('toast_bg_deleted')); this.loadBackgroundImages();
                if (App.settings.bg_image_id === id) App.updateSetting('bg_image_id', null);
            });
        });
    },

    async loadShortcutsList() {
        const list = document.getElementById('settings-shortcuts-list'); if (!list) return;
        const resp = await fetch('/api/shortcuts'); const data = await resp.json();
        if (!data.length) { list.innerHTML = `<p class="settings-hint">${I18n.t('shortcuts_no_items')}</p>`; return; }
        list.innerHTML = data.map(sc => `
        <div class="settings-shortcut-row"><span class="sc-title">${sc.title}</span><span class="sc-url">${sc.url}</span>
        <div class="sc-actions"><button class="setting-btn small btn-sc-edit" data-id="${sc.id}">${I18n.t('edit')}</button>
        <button class="setting-btn small danger btn-sc-del" data-id="${sc.id}">✕</button></div></div>
        `).join('');
        list.querySelectorAll('.btn-sc-edit').forEach(b => b.addEventListener('click', () => Shortcuts.openModal(parseInt(b.dataset.id))));
        list.querySelectorAll('.btn-sc-del').forEach(b => b.addEventListener('click', async () => {
            if (!confirm(I18n.t('confirm_delete'))) return;
            await fetch(`/api/shortcuts/${b.dataset.id}`, { method: 'DELETE' });
            Toast.success(I18n.t('toast_shortcut_deleted')); Shortcuts.load(); this.loadShortcutsList();
        }));
    },

    loadThemeGrid() {
        const grid = document.getElementById('theme-grid'); if (!grid) return;
        const currentTheme = App.settings.theme || 'catppuccin-mocha';
        grid.innerHTML = Themes.getThemeList().map(t => `
        <div class="theme-card ${t.id === currentTheme ? 'active' : ''}" data-theme="${t.id}">
        <div class="theme-card-preview" style="background:${t.colors['--bg-base']}">
        <span style="background:${t.colors['--accent']}"></span>
        <span style="background:${t.colors['--bg-surface']}"></span>
        <span style="background:${t.colors['--text-primary']}"></span>
        </div>
        <div class="theme-card-name">${t.name}</div>
        </div>
        `).join('');
        grid.querySelectorAll('.theme-card').forEach(card => {
            card.addEventListener('click', () => {
                grid.querySelectorAll('.theme-card').forEach(c => c.classList.toggle('active', c.dataset.theme === card.dataset.theme));
                App.updateSetting('theme', card.dataset.theme);
                Themes.apply(card.dataset.theme);
                Toast.info(I18n.t('toast_theme_applied'));
                this.loadAccentPalette();
                Background.updatePreview(App.settings);
            });
        });
    },

    async loadFontsDropdown(selectedFont) {
        const select = document.getElementById('set-font-family'); if (!select) return;
        const resp = await fetch('/api/fonts'); const fonts = await resp.json();
        select.innerHTML = fonts.map(f => `<option value="${f.name}" ${f.name === selectedFont ? 'selected' : ''}>${f.name}${f.builtin ? '' : ' (Custom)'}</option>`).join('');
    },

    async loadWidgetSettings() {
        const cdContainer = document.getElementById('countdowns-list');
        if (cdContainer) {
            const resp = await fetch('/api/countdowns'); const cds = await resp.json();
            cdContainer.innerHTML = cds.map(c => `<div class="widget-config-item"><span>${c.emoji} <strong>${c.title}</strong> (${c.target_date})</span><button class="setting-btn small danger btn-cd-del" data-id="${c.id}">✕</button></div>`).join('');
            cdContainer.querySelectorAll('.btn-cd-del').forEach(b => b.addEventListener('click', async () => { await fetch(`/api/countdowns/${b.dataset.id}`, { method: 'DELETE' }); this.loadWidgetSettings(); Widgets.loadCountdowns(); }));
        }
        const wcContainer = document.getElementById('world-clocks-list');
        if (wcContainer) {
            const resp = await fetch('/api/world-clocks'); const wcs = await resp.json();
            wcContainer.innerHTML = wcs.map(w => `<div class="widget-config-item"><span><strong>${w.label}</strong> (${w.timezone})</span><button class="setting-btn small danger btn-wc-del" data-id="${w.id}">✕</button></div>`).join('');
            wcContainer.querySelectorAll('.btn-wc-del').forEach(b => b.addEventListener('click', async () => { await fetch(`/api/world-clocks/${b.dataset.id}`, { method: 'DELETE' }); this.loadWidgetSettings(); Widgets.loadWorldClocks(); }));
        }
    },

    toggleBgSubOptions(source) {
        document.getElementById('bg-image-options')?.classList.toggle('hidden', source !== 'image');
        document.getElementById('bg-gradient-options')?.classList.toggle('hidden', source !== 'gradient');
        document.getElementById('bg-solid-options')?.classList.toggle('hidden', source !== 'solid');
    },

    setVal(id, val) { const el = document.getElementById(id); if (el && val != null) el.value = val; },
    setChecked(id, val) { const el = document.getElementById(id); if (el) el.checked = Boolean(val); },
    setRange(id, val, valId, transform) {
        const el = document.getElementById(id); const ve = document.getElementById(valId);
        if (el && val != null) { el.value = val; if (ve) ve.textContent = transform ? transform(val) : val; }
    },
    bindRangeDisplay(id, valId, transform) {
        const el = document.getElementById(id); const ve = document.getElementById(valId);
        if (el && ve) el.addEventListener('input', () => { ve.textContent = transform ? transform(el.value) : el.value; });
    }
};
