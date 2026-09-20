/* Background manager */
const Background = {
    bgLayer: null,
    bgOverlay: null,
    bgVignette: null,
    parallaxHandler: null,
    kenBurnsInterval: null,
    rotateInterval: null,
    backgrounds: [],

    init() {
        this.bgLayer = document.getElementById('bg-layer');
        this.bgOverlay = document.getElementById('bg-overlay');
        this.bgVignette = document.getElementById('bg-vignette');
    },

    async apply(settings) {
        if (!this.bgLayer) this.init();
        const s = settings;

        // Reset
        this.bgLayer.style.cssText = '';
        this.bgLayer.className = 'bg-layer';
        this.removeParallax();
        this.removeKenBurns();

        const source = s.bg_source || 'theme';

        if (source === 'theme') {
            this.bgLayer.style.background = `var(--bg-base)`;
        } else if (source === 'solid') {
            this.bgLayer.style.background = s.bg_solid_color || '#1e1e2e';
        } else if (source === 'gradient') {
            const from = s.bg_gradient_from || '#1e1e2e';
            const to = s.bg_gradient_to || '#313244';
            const angle = s.bg_gradient_angle || 135;
            this.bgLayer.style.background = `linear-gradient(${angle}deg, ${from}, ${to})`;
        } else if (source === 'image') {
            await this.applyImage(s);
        }

        // Effects
        this.applyEffects(s);

        // Vignette
        if (s.bg_vignette) {
            this.bgVignette.classList.remove('hidden');
        } else {
            this.bgVignette.classList.add('hidden');
        }

        // Parallax
        if (s.bg_parallax && source === 'image') {
            this.enableParallax();
        }

        // Ken Burns
        if (s.bg_ken_burns && source === 'image') {
            this.enableKenBurns();
        }

        // Rotate
        if (s.bg_rotate_enabled && source === 'image') {
            this.enableRotate(s.bg_rotate_interval || 30);
        }
    },

    async applyImage(s) {
        let imageUrl = '';
        const bgId = s.bg_image_id;

        if (bgId) {
            // Fetch background info
            try {
                const resp = await fetch('/api/backgrounds');
                this.backgrounds = await resp.json();
                const bg = this.backgrounds.find(b => b.id === bgId);
                if (bg) {
                    imageUrl = `/static/backgrounds/${bg.filename}`;
                }
            } catch (e) {
                console.error('Failed to load backgrounds:', e);
            }
        }

        if (!imageUrl && this.backgrounds.length > 0) {
            // Pick random
            const bg = this.backgrounds[Math.floor(Math.random() * this.backgrounds.length)];
            imageUrl = `/static/backgrounds/${bg.filename}`;
        }

        if (!imageUrl) return;

        const scaleMode = s.bg_scale_mode || 'cover';
        const position = s.bg_position || 'center';

        this.bgLayer.style.backgroundImage = `url('${imageUrl}')`;
        this.bgLayer.style.backgroundPosition = position;
        this.bgLayer.style.backgroundRepeat = scaleMode === 'tile' ? 'repeat' : 'no-repeat';

        switch (scaleMode) {
            case 'cover':
                this.bgLayer.style.backgroundSize = 'cover';
                break;
            case 'contain':
                this.bgLayer.style.backgroundSize = 'contain';
                break;
            case 'stretch':
                this.bgLayer.style.backgroundSize = '100% 100%';
                break;
            case 'tile':
                this.bgLayer.style.backgroundSize = 'auto';
                break;
            case 'center':
                this.bgLayer.style.backgroundSize = 'auto';
                break;
            case 'fit-width':
                this.bgLayer.style.backgroundSize = '100% auto';
                break;
            case 'fit-height':
                this.bgLayer.style.backgroundSize = 'auto 100%';
                break;
            case 'fill-blur':
                this.bgLayer.style.backgroundSize = 'cover';
                // Add blurred copy behind
                this.bgLayer.classList.add('bg-fill-blur');
                break;
        }

        // Adaptive color
        if (s.bg_adaptive_color && bgId) {
            try {
                const colorResp = await fetch(`/api/backgrounds/${bgId}/colors`);
                const colors = await colorResp.json();
                if (colors.dominant) {
                    document.documentElement.style.setProperty('--accent', colors.dominant);
                }
            } catch (e) {
                console.error('Adaptive color error:', e);
            }
        }
    },

    applyEffects(s) {
        const filters = [];

        if (s.bg_blur > 0) filters.push(`blur(${s.bg_blur}px)`);
        if (s.bg_brightness !== 100) filters.push(`brightness(${s.bg_brightness}%)`);
        if (s.bg_saturation !== 100) filters.push(`saturate(${s.bg_saturation}%)`);
        if (s.bg_grayscale) filters.push('grayscale(100%)');
        if (s.bg_sepia > 0) filters.push(`sepia(${s.bg_sepia}%)`);

        this.bgLayer.style.filter = filters.length ? filters.join(' ') : 'none';

        // Dim overlay
        if (s.bg_dim > 0) {
            this.bgOverlay.style.background = `rgba(0, 0, 0, ${s.bg_dim / 100})`;
            this.bgOverlay.style.display = 'block';
        } else {
            this.bgOverlay.style.display = 'none';
        }
    },

    enableParallax() {
        this.parallaxHandler = (e) => {
            const x = (e.clientX / window.innerWidth - 0.5) * 20;
            const y = (e.clientY / window.innerHeight - 0.5) * 20;
            this.bgLayer.style.transform = `translate(${x}px, ${y}px) scale(1.05)`;
        };
        document.addEventListener('mousemove', this.parallaxHandler);
    },

    removeParallax() {
        if (this.parallaxHandler) {
            document.removeEventListener('mousemove', this.parallaxHandler);
            this.parallaxHandler = null;
            if (this.bgLayer) this.bgLayer.style.transform = '';
        }
    },

    enableKenBurns() {
        this.bgLayer.classList.add('ken-burns');
    },

    removeKenBurns() {
        if (this.bgLayer) this.bgLayer.classList.remove('ken-burns');
    },

    enableRotate(intervalMin) {
        if (this.rotateInterval) clearInterval(this.rotateInterval);
        this.rotateInterval = setInterval(async () => {
            if (this.backgrounds.length > 1) {
                const bg = this.backgrounds[Math.floor(Math.random() * this.backgrounds.length)];
                this.bgLayer.style.backgroundImage = `url('/static/backgrounds/${bg.filename}')`;
            }
        }, intervalMin * 60 * 1000);
    },

    updatePreview(settings) {
        const preview = document.getElementById('bg-preview');
        if (!preview) return;

        // Clone background styles to preview
        preview.style.cssText = '';
        const s = settings;

        if (s.bg_source === 'theme') {
            preview.style.background = getComputedStyle(document.documentElement).getPropertyValue('--bg-base');
        } else if (s.bg_source === 'solid') {
            preview.style.background = s.bg_solid_color || '#1e1e2e';
        } else if (s.bg_source === 'gradient') {
            preview.style.background = `linear-gradient(${s.bg_gradient_angle || 135}deg, ${s.bg_gradient_from || '#1e1e2e'}, ${s.bg_gradient_to || '#313244'})`;
        } else if (s.bg_source === 'image' && s.bg_image_id) {
            const bg = this.backgrounds.find(b => b.id === s.bg_image_id);
            if (bg) {
                preview.style.backgroundImage = `url('/static/backgrounds/${bg.filename}')`;
                preview.style.backgroundSize = s.bg_scale_mode === 'tile' ? 'auto' : (s.bg_scale_mode || 'cover');
                preview.style.backgroundPosition = s.bg_position || 'center';
                preview.style.backgroundRepeat = s.bg_scale_mode === 'tile' ? 'repeat' : 'no-repeat';
            }
        }

        // Effects on preview
        const filters = [];
        if (s.bg_blur > 0) filters.push(`blur(${Math.max(1, s.bg_blur / 3)}px)`);
        if (s.bg_brightness !== 100) filters.push(`brightness(${s.bg_brightness}%)`);
        if (s.bg_saturation !== 100) filters.push(`saturate(${s.bg_saturation}%)`);
        if (s.bg_grayscale) filters.push('grayscale(100%)');
        if (s.bg_sepia > 0) filters.push(`sepia(${s.bg_sepia}%)`);
        preview.style.filter = filters.join(' ') || 'none';

        if (s.bg_dim > 0) {
            preview.style.boxShadow = `inset 0 0 0 1000px rgba(0,0,0,${s.bg_dim / 100})`;
        }
    }
};
