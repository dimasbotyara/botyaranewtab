/* Keyboard Shortcuts & Global Hotkeys */
const Hotkeys = {
    eggSequence: '',

    init() {
        document.addEventListener('keydown', (e) => this.handleKey(e));
    },

    handleKey(e) {
        const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
        const isInputFocused = activeTag === 'input' || activeTag === 'textarea' || activeTag === 'select';

        // 1. Easter Egg string tracker ("dimasbotyara")
        if (!isInputFocused && e.key.length === 1) {
            this.eggSequence += e.key.toLowerCase();
            if (this.eggSequence.length > 20) {
                this.eggSequence = this.eggSequence.slice(-20);
            }
            if (this.eggSequence.includes('dimasbotyara')) {
                this.eggSequence = '';
                Confetti.fire(5000);
                Toast.success(I18n.t('easter_egg_triggered'));
            }
        }

        // 2. Escape: Close modals, autocompletes, or blur
        if (e.key === 'Escape') {
            if (Settings.isOpen) {
                Settings.close();
                return;
            }
            const shortcutModal = document.getElementById('shortcut-modal');
            if (shortcutModal && !shortcutModal.classList.contains('hidden')) {
                Shortcuts.closeModal();
                return;
            }
            Search.clear();
            return;
        }

        // 3. "/" to focus search bar (if not typing in another input)
        if (e.key === '/' && !isInputFocused) {
            e.preventDefault();
            Search.focus();
            return;
        }

        // 4. Ctrl+, -> Open/Close Settings
        if ((e.ctrlKey || e.metaKey) && e.key === ',') {
            e.preventDefault();
            Settings.toggle();
            return;
        }

        // 5. Ctrl+K -> Command Palette / Focus Search with bang
        if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
            e.preventDefault();
            Search.focus();
            if (!Search.input.value.startsWith('!')) {
                Search.input.value = '!';
                Search.onInput();
            }
            return;
        }

        // 6. Ctrl + Shift + F -> Toggle Focus Mode
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'F' || e.key === 'f')) {
            e.preventDefault();
            App.toggleFocusMode();
            return;
        }

        // 7. Ctrl + Shift + Z -> Toggle Zen Mode
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'Z' || e.key === 'z')) {
            e.preventDefault();
            App.toggleZenMode();
            return;
        }

        // 8. Ctrl + 1..9 -> Open Nth Shortcut
        if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key >= '1' && e.key <= '9') {
            const index = parseInt(e.key) - 1;
            if (Shortcuts.data && Shortcuts.data[index]) {
                e.preventDefault();
                window.location.href = Shortcuts.data[index].url;
            }
        }
    }
};
