/* Shortcuts manager with folders */
const Shortcuts = {
    container: null,
    grid: null,
    data: [],
    editingId: null,
    customIconPath: null,

    init() {
        this.container = document.getElementById('shortcuts-container');
        this.grid = document.getElementById('shortcuts-grid');

        // Settings add button
        document.getElementById('add-shortcut-btn-settings')?.addEventListener('click', () => this.openModal());

        // Modal events
        document.getElementById('shortcut-modal-save')?.addEventListener('click', () => this.saveFromModal());
        document.getElementById('shortcut-modal-cancel')?.addEventListener('click', () => this.closeModal());
        document.getElementById('shortcut-modal-delete')?.addEventListener('click', () => this.deleteFromModal());
        document.querySelector('.shortcut-modal-backdrop')?.addEventListener('click', () => this.closeModal());

        document.getElementById('btn-shortcut-icon')?.addEventListener('click', () => {
            document.getElementById('input-shortcut-icon').click();
        });
        document.getElementById('input-shortcut-icon')?.addEventListener('change', (e) => this.handleIconUpload(e));

        // Folder overlay
        document.querySelector('.folder-backdrop')?.addEventListener('click', () => this.closeFolder());
        document.getElementById('folder-close-btn')?.addEventListener('click', () => this.closeFolder());

        this.load();
    },

    async load() {
        try {
            const resp = await fetch('/api/shortcuts');
            this.data = await resp.json();
            this.render();
        } catch (e) {
            console.error('Failed to load shortcuts:', e);
        }
    },

    render() {
        const s = App.settings;
        const size = s.shortcuts_size || 'medium';
        const showLabels = s.shortcuts_show_labels !== false;
        const cols = s.shortcuts_columns || 0;

        this.grid.className = `shortcuts-grid size-${size}`;
        if (cols > 0) {
            this.grid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
        } else {
            this.grid.style.gridTemplateColumns = '';
        }

        // Separate into folders and ungrouped
        const groups = {};
        const ungrouped = [];

        this.data.forEach(sc => {
            const g = (sc.group_name || '').trim();
            if (g) {
                if (!groups[g]) groups[g] = [];
                groups[g].push(sc);
            } else {
                ungrouped.push(sc);
            }
        });

        let html = '';

        // Render folder icons
        for (const [groupName, items] of Object.entries(groups)) {
            const previewIcons = items.slice(0, 4);
            html += `
            <div class="shortcut-item shortcut-folder" data-group="${groupName}" title="${groupName} (${items.length})">
            <div class="shortcut-icon folder-icon">
            <div class="folder-preview">
            ${previewIcons.map(sc => {
                const iconSrc = sc.custom_icon_path || sc.icon_path;
                return iconSrc
                ? `<img src="/static/${iconSrc}" alt="" class="folder-mini-icon">`
                : `<div class="folder-mini-letter" style="background:${sc.color || 'var(--accent)'}">${(sc.title || '?')[0]}</div>`;
            }).join('')}
            </div>
            </div>
            ${showLabels ? `<span class="shortcut-label">${groupName}</span>` : ''}
            </div>
            `;
        }

        // Render ungrouped
        for (const sc of ungrouped) {
            html += this.renderShortcutItem(sc, showLabels);
        }

        this.grid.innerHTML = html;

        // Folder click
        this.grid.querySelectorAll('.shortcut-folder').forEach(el => {
            el.addEventListener('click', () => {
                const group = el.dataset.group;
                this.openFolder(group, groups[group]);
            });
        });

        // Direct shortcut clicks
        this.grid.querySelectorAll('.shortcut-item:not(.shortcut-folder)').forEach(el => {
            el.addEventListener('click', () => {
                const id = parseInt(el.dataset.id);
                fetch(`/api/shortcuts/${id}/click`, { method: 'POST' });
            });
            el.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                this.openModal(parseInt(el.dataset.id));
            });
        });
    },

    renderShortcutItem(sc, showLabels) {
        const iconSrc = sc.custom_icon_path || sc.icon_path;
        const iconHtml = iconSrc
        ? `<img src="/static/${iconSrc}" alt="" class="shortcut-icon-img" loading="lazy">`
        : `<div class="shortcut-icon-letter" style="background:${sc.color || 'var(--accent)'}">${(sc.title || '?')[0].toUpperCase()}</div>`;

        return `
        <a href="${sc.url}" class="shortcut-item" data-id="${sc.id}"
        title="${sc.title}${sc.clicks ? ` (${sc.clicks} ${I18n.t('shortcuts_clicks')})` : ''}">
        <div class="shortcut-icon">${iconHtml}</div>
        ${showLabels ? `<span class="shortcut-label">${sc.title}</span>` : ''}
        </a>
        `;
    },

    openFolder(groupName, items) {
        const overlay = document.getElementById('folder-overlay');
        const title = document.getElementById('folder-title');
        const grid = document.getElementById('folder-grid');

        title.textContent = groupName;
        const showLabels = App.settings.shortcuts_show_labels !== false;

        grid.innerHTML = items.map(sc => this.renderShortcutItem(sc, showLabels)).join('');

        // Click + context menu for items inside folder
        grid.querySelectorAll('.shortcut-item').forEach(el => {
            el.addEventListener('click', () => {
                fetch(`/api/shortcuts/${el.dataset.id}/click`, { method: 'POST' });
            });
            el.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                this.closeFolder();
                this.openModal(parseInt(el.dataset.id));
            });
        });

        overlay.classList.remove('hidden');
        requestAnimationFrame(() => overlay.classList.add('open'));
    },

    closeFolder() {
        const overlay = document.getElementById('folder-overlay');
        overlay.classList.remove('open');
        setTimeout(() => overlay.classList.add('hidden'), 200);
    },

    openModal(editId = null) {
        this.editingId = editId;
        this.customIconPath = null;
        const modal = document.getElementById('shortcut-modal');
        const titleEl = document.getElementById('shortcut-modal-title');
        const deleteBtn = document.getElementById('shortcut-modal-delete');

        if (editId) {
            const sc = this.data.find(s => s.id === editId);
            if (sc) {
                document.getElementById('shortcut-edit-url').value = sc.url;
                document.getElementById('shortcut-edit-title').value = sc.title;
                document.getElementById('shortcut-edit-group').value = sc.group_name || '';
                document.getElementById('shortcut-edit-color').value = sc.color || '#cba6f7';
                titleEl.setAttribute('data-i18n', 'edit_shortcut');
                titleEl.textContent = I18n.t('edit_shortcut');
                deleteBtn.classList.remove('hidden');
            }
        } else {
            document.getElementById('shortcut-edit-url').value = '';
            document.getElementById('shortcut-edit-title').value = '';
            document.getElementById('shortcut-edit-group').value = '';
            document.getElementById('shortcut-edit-color').value = '#cba6f7';
            titleEl.setAttribute('data-i18n', 'add_shortcut');
            titleEl.textContent = I18n.t('add_shortcut');
            deleteBtn.classList.add('hidden');
        }

        document.getElementById('shortcut-icon-name').textContent = '';
        modal.classList.remove('hidden');
        requestAnimationFrame(() => modal.classList.add('open'));
    },

    closeModal() {
        const modal = document.getElementById('shortcut-modal');
        modal.classList.remove('open');
        setTimeout(() => modal.classList.add('hidden'), 200);
    },

    async saveFromModal() {
        const url = document.getElementById('shortcut-edit-url').value.trim();
        const title = document.getElementById('shortcut-edit-title').value.trim();
        const group = document.getElementById('shortcut-edit-group').value.trim();
        const color = document.getElementById('shortcut-edit-color').value;

        if (!url) return;

        const body = { url, title, group_name: group, color };
        if (this.customIconPath) body.custom_icon_path = this.customIconPath;

        try {
            if (this.editingId) {
                await fetch(`/api/shortcuts/${this.editingId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
            } else {
                await fetch('/api/shortcuts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
            }
            Toast.success(I18n.t('toast_shortcut_added'));
            this.closeModal();
            this.load();
        } catch (e) {
            Toast.error(I18n.t('toast_error'));
        }
    },

    async deleteFromModal() {
        if (!this.editingId) return;
        if (!confirm(I18n.t('confirm_delete'))) return;
        try {
            await fetch(`/api/shortcuts/${this.editingId}`, { method: 'DELETE' });
            Toast.success(I18n.t('toast_shortcut_deleted'));
            this.closeModal();
            this.load();
        } catch (e) {
            Toast.error(I18n.t('toast_error'));
        }
    },

    async handleIconUpload(e) {
        const file = e.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        try {
            const resp = await fetch('/api/shortcuts/icon', { method: 'POST', body: formData });
            const data = await resp.json();
            this.customIconPath = data.path;
            document.getElementById('shortcut-icon-name').textContent = file.name;
        } catch (e) {
            Toast.error(I18n.t('toast_error'));
        }
    }
};
