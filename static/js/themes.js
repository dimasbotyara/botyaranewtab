/* Theme definitions — 15 themes including Catppuccin, Nord, Dracula, etc. */
const Themes = {
    list: {
        'catppuccin-mocha': {
            name: 'Catppuccin Mocha',
            type: 'dark',
            colors: {
                '--bg-base': '#1e1e2e',
                '--bg-surface': '#313244',
                '--bg-overlay': '#45475a',
                '--text-primary': '#cdd6f4',
                '--text-secondary': '#a6adc8',
                '--text-muted': '#6c7086',
                '--accent': '#cba6f7',
                '--accent-hover': '#b4befe',
                '--border': '#585b70',
                '--success': '#a6e3a1',
                '--warning': '#f9e2af',
                '--error': '#f38ba8',
                '--red': '#f38ba8',
                '--green': '#a6e3a1',
                '--blue': '#89b4fa',
                '--yellow': '#f9e2af',
                '--pink': '#f5c2e7',
                '--teal': '#94e2d5',
                '--peach': '#fab387',
                '--lavender': '#b4befe',
                '--mauve': '#cba6f7',
            }
        },
        'catppuccin-macchiato': {
            name: 'Catppuccin Macchiato',
            type: 'dark',
            colors: {
                '--bg-base': '#24273a',
                '--bg-surface': '#363a4f',
                '--bg-overlay': '#494d64',
                '--text-primary': '#cad3f5',
                '--text-secondary': '#a5adcb',
                '--text-muted': '#6e738d',
                '--accent': '#c6a0f6',
                '--accent-hover': '#b7bdf8',
                '--border': '#5b6078',
                '--success': '#a6da95',
                '--warning': '#eed49f',
                '--error': '#ed8796',
            }
        },
        'catppuccin-frappe': {
            name: 'Catppuccin Frappé',
            type: 'dark',
            colors: {
                '--bg-base': '#303446',
                '--bg-surface': '#414559',
                '--bg-overlay': '#51576d',
                '--text-primary': '#c6d0f5',
                '--text-secondary': '#a5adce',
                '--text-muted': '#737994',
                '--accent': '#ca9ee6',
                '--accent-hover': '#babbf1',
                '--border': '#626880',
                '--success': '#a6d189',
                '--warning': '#e5c890',
                '--error': '#e78284',
            }
        },
        'catppuccin-latte': {
            name: 'Catppuccin Latte',
            type: 'light',
            colors: {
                '--bg-base': '#eff1f5',
                '--bg-surface': '#e6e9ef',
                '--bg-overlay': '#dce0e8',
                '--text-primary': '#4c4f69',
                '--text-secondary': '#5c5f77',
                '--text-muted': '#9ca0b0',
                '--accent': '#8839ef',
                '--accent-hover': '#7287fd',
                '--border': '#ccd0da',
                '--success': '#40a02b',
                '--warning': '#df8e1d',
                '--error': '#d20f39',
            }
        },
        'nord': {
            name: 'Nord',
            type: 'dark',
            colors: {
                '--bg-base': '#2e3440',
                '--bg-surface': '#3b4252',
                '--bg-overlay': '#434c5e',
                '--text-primary': '#eceff4',
                '--text-secondary': '#d8dee9',
                '--text-muted': '#4c566a',
                '--accent': '#88c0d0',
                '--accent-hover': '#81a1c1',
                '--border': '#4c566a',
                '--success': '#a3be8c',
                '--warning': '#ebcb8b',
                '--error': '#bf616a',
            }
        },
        'nord-light': {
            name: 'Nord Light',
            type: 'light',
            colors: {
                '--bg-base': '#eceff4',
                '--bg-surface': '#e5e9f0',
                '--bg-overlay': '#d8dee9',
                '--text-primary': '#2e3440',
                '--text-secondary': '#3b4252',
                '--text-muted': '#4c566a',
                '--accent': '#5e81ac',
                '--accent-hover': '#81a1c1',
                '--border': '#d8dee9',
                '--success': '#a3be8c',
                '--warning': '#ebcb8b',
                '--error': '#bf616a',
            }
        },
        'dracula': {
            name: 'Dracula',
            type: 'dark',
            colors: {
                '--bg-base': '#282a36',
                '--bg-surface': '#44475a',
                '--bg-overlay': '#6272a4',
                '--text-primary': '#f8f8f2',
                '--text-secondary': '#f8f8f2',
                '--text-muted': '#6272a4',
                '--accent': '#bd93f9',
                '--accent-hover': '#ff79c6',
                '--border': '#44475a',
                '--success': '#50fa7b',
                '--warning': '#f1fa8c',
                '--error': '#ff5555',
            }
        },
        'tokyo-night': {
            name: 'Tokyo Night',
            type: 'dark',
            colors: {
                '--bg-base': '#1a1b26',
                '--bg-surface': '#24283b',
                '--bg-overlay': '#414868',
                '--text-primary': '#c0caf5',
                '--text-secondary': '#a9b1d6',
                '--text-muted': '#565f89',
                '--accent': '#7aa2f7',
                '--accent-hover': '#bb9af7',
                '--border': '#3b4261',
                '--success': '#9ece6a',
                '--warning': '#e0af68',
                '--error': '#f7768e',
            }
        },
        'gruvbox-dark': {
            name: 'Gruvbox Dark',
            type: 'dark',
            colors: {
                '--bg-base': '#282828',
                '--bg-surface': '#3c3836',
                '--bg-overlay': '#504945',
                '--text-primary': '#ebdbb2',
                '--text-secondary': '#d5c4a1',
                '--text-muted': '#665c54',
                '--accent': '#fabd2f',
                '--accent-hover': '#fe8019',
                '--border': '#504945',
                '--success': '#b8bb26',
                '--warning': '#fabd2f',
                '--error': '#fb4934',
            }
        },
        'gruvbox-light': {
            name: 'Gruvbox Light',
            type: 'light',
            colors: {
                '--bg-base': '#fbf1c7',
                '--bg-surface': '#ebdbb2',
                '--bg-overlay': '#d5c4a1',
                '--text-primary': '#3c3836',
                '--text-secondary': '#504945',
                '--text-muted': '#928374',
                '--accent': '#d65d0e',
                '--accent-hover': '#af3a03',
                '--border': '#d5c4a1',
                '--success': '#79740e',
                '--warning': '#b57614',
                '--error': '#9d0006',
            }
        },
        'solarized-dark': {
            name: 'Solarized Dark',
            type: 'dark',
            colors: {
                '--bg-base': '#002b36',
                '--bg-surface': '#073642',
                '--bg-overlay': '#586e75',
                '--text-primary': '#fdf6e3',
                '--text-secondary': '#eee8d5',
                '--text-muted': '#657b83',
                '--accent': '#268bd2',
                '--accent-hover': '#2aa198',
                '--border': '#073642',
                '--success': '#859900',
                '--warning': '#b58900',
                '--error': '#dc322f',
            }
        },
        'one-dark': {
            name: 'One Dark',
            type: 'dark',
            colors: {
                '--bg-base': '#282c34',
                '--bg-surface': '#2c313c',
                '--bg-overlay': '#3e4452',
                '--text-primary': '#abb2bf',
                '--text-secondary': '#828997',
                '--text-muted': '#5c6370',
                '--accent': '#61afef',
                '--accent-hover': '#c678dd',
                '--border': '#3e4452',
                '--success': '#98c379',
                '--warning': '#e5c07b',
                '--error': '#e06c75',
            }
        },
        'rose-pine': {
            name: 'Rosé Pine',
            type: 'dark',
            colors: {
                '--bg-base': '#191724',
                '--bg-surface': '#1f1d2e',
                '--bg-overlay': '#26233a',
                '--text-primary': '#e0def4',
                '--text-secondary': '#908caa',
                '--text-muted': '#6e6a86',
                '--accent': '#c4a7e7',
                '--accent-hover': '#ebbcba',
                '--border': '#26233a',
                '--success': '#9ccfd8',
                '--warning': '#f6c177',
                '--error': '#eb6f92',
            }
        },
        'ayu-dark': {
            name: 'Ayu Dark',
            type: 'dark',
            colors: {
                '--bg-base': '#0d1017',
                '--bg-surface': '#131721',
                '--bg-overlay': '#1c212b',
                '--text-primary': '#bfbdb6',
                '--text-secondary': '#9b9689',
                '--text-muted': '#565b66',
                '--accent': '#e6b450',
                '--accent-hover': '#ffb454',
                '--border': '#1c212b',
                '--success': '#7fd962',
                '--warning': '#e6b450',
                '--error': '#d95757',
            }
        },
        'midnight': {
            name: 'Midnight',
            type: 'dark',
            colors: {
                '--bg-base': '#0f0f1a',
                '--bg-surface': '#1a1a2e',
                '--bg-overlay': '#25253d',
                '--text-primary': '#e0e0f0',
                '--text-secondary': '#a0a0c0',
                '--text-muted': '#505070',
                '--accent': '#7c3aed',
                '--accent-hover': '#a855f7',
                '--border': '#25253d',
                '--success': '#34d399',
                '--warning': '#fbbf24',
                '--error': '#f43f5e',
            }
        },
    },

    apply(themeName) {
        const theme = this.list[themeName];
        if (!theme) return;

        const root = document.documentElement;
        root.setAttribute('data-theme', themeName);

        for (const [prop, val] of Object.entries(theme.colors)) {
            root.style.setProperty(prop, val);
        }

        // Apply accent override if set
        const accentOverride = App?.settings?.accent_color;
        if (accentOverride && accentOverride !== theme.colors['--accent']) {
            root.style.setProperty('--accent', accentOverride);
        }
    },

    getThemeList() {
        return Object.entries(this.list).map(([id, t]) => ({
            id,
            name: t.name,
            type: t.type,
            colors: t.colors,
        }));
    }
};
