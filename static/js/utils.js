/* Shared helpers — loaded before every other module. */

/**
 * Escape a value for safe interpolation into an HTML template string.
 * Every piece of user-controlled data (shortcut titles, notes, countdowns,
 * search history, file names…) must go through this before hitting innerHTML.
 */
function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, (c) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
    }[c]));
}

/** Only hex colours reach a style attribute; anything else falls back. */
function safeColor(value, fallback = 'var(--accent)') {
    const text = String(value || '').trim();
    return /^#[0-9a-fA-F]{3,8}$/.test(text) ? text : fallback;
}

/** Escape for use inside a CSS url("…") / attribute value. */
function safeUrl(value) {
    const text = String(value || '').trim();
    // Relative path inside /static only
    if (!text || /^[a-zA-Z][\w+.-]*:/.test(text) || text.includes('..')) return '';
    return text.replace(/["'()\\<>\s]/g, '');
}

/**
 * Apply colours declared as data-bg="…" attributes.
 *
 * Strict CSP forbids style="…" in generated markup, so colours travel as data
 * attributes and are applied through CSSOM (which CSP does not block).
 * Call this after every innerHTML assignment that rendered such elements.
 */
function applyDynamicColors(root) {
    const scope = root || document;
    scope.querySelectorAll('[data-bg]').forEach((el) => {
        el.style.backgroundColor = safeColor(el.dataset.bg, 'var(--accent)');
    });
    scope.querySelectorAll('[data-bg-var]').forEach((el) => {
        // data-bg-var="--accent" → value lives in a CSS custom property
        const name = el.dataset.bgVar;
        if (/^--[\w-]+$/.test(name || '')) {
            el.style.backgroundColor = `var(${name})`;
        }
    });
}

/** Tiny stable hash — used to cache-bust generated stylesheets. */
function hashString(value) {
    let hash = 5381;
    const text = String(value ?? '');
    for (let i = 0; i < text.length; i++) {
        hash = ((hash << 5) + hash + text.charCodeAt(i)) | 0;
    }
    return (hash >>> 0).toString(36);
}

const Utils = { esc, safeColor, safeUrl, applyDynamicColors, hashString };
