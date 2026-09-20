/* Confetti effect 🎉 */
const Confetti = {
    canvas: null,
    ctx: null,
    particles: [],
    running: false,

    init() {
        this.canvas = document.getElementById('confetti-canvas');
        if (this.canvas) {
            this.ctx = this.canvas.getContext('2d');
        }
    },

    fire(duration = 3000) {
        if (!this.canvas || !this.ctx) this.init();
        if (!this.canvas) return;

        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        this.canvas.style.display = 'block';

        this.particles = [];
        const colors = ['#f38ba8', '#a6e3a1', '#89b4fa', '#f9e2af', '#cba6f7', '#f5c2e7', '#fab387', '#94e2d5'];

        for (let i = 0; i < 150; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height - this.canvas.height,
                w: Math.random() * 10 + 5,
                h: Math.random() * 6 + 3,
                color: colors[Math.floor(Math.random() * colors.length)],
                vx: (Math.random() - 0.5) * 4,
                vy: Math.random() * 3 + 2,
                spin: Math.random() * 0.2 - 0.1,
                angle: Math.random() * Math.PI * 2,
                opacity: 1,
            });
        }

        this.running = true;
        this.animate();

        setTimeout(() => {
            this.running = false;
            setTimeout(() => {
                this.canvas.style.display = 'none';
            }, 2000);
        }, duration);
    },

    animate() {
        if (!this.running && this.particles.every(p => p.opacity <= 0)) return;

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        this.particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;
            p.angle += p.spin;
            if (!this.running) p.opacity -= 0.02;
            if (p.opacity <= 0) return;

            this.ctx.save();
            this.ctx.globalAlpha = Math.max(0, p.opacity);
            this.ctx.translate(p.x, p.y);
            this.ctx.rotate(p.angle);
            this.ctx.fillStyle = p.color;
            this.ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
            this.ctx.restore();
        });

        requestAnimationFrame(() => this.animate());
    }
};
