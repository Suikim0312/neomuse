/**
 * NeoMuse — Particle network background
 * Moving dots connected by lines — clean and subtle
 */
(function () {
    'use strict';

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    function isDark() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ||
               document.body.classList.contains('dark-mode');
    }

    class Dot {
        constructor(W, H) { this.W = W; this.H = H; this.reset(true); }

        reset(init) {
            this.x  = Math.random() * this.W;
            this.y  = init ? Math.random() * this.H : -8;
            const spd = 0.25 + Math.random() * 0.45;
            const ang = Math.random() * Math.PI * 2;
            this.vx = Math.cos(ang) * spd;
            this.vy = Math.sin(ang) * spd * 0.7 + 0.08;
            this.r  = 1.8 + Math.random() * 2.5;
            this.a  = 0.25 + Math.random() * 0.45;
        }

        step() {
            this.x += this.vx;
            this.y += this.vy;
            if (this.x < -20 || this.x > this.W + 20 || this.y > this.H + 20) this.reset(false);
        }

        draw(ctx) {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function mkCanvas() {
        const c = document.createElement('canvas');
        c.id = 'bg-canvas';
        Object.assign(c.style, {
            position: 'fixed', inset: '0', width: '100%', height: '100%',
            pointerEvents: 'none', zIndex: '0',
        });
        document.body.insertBefore(c, document.body.firstChild);

        const layout = document.querySelector('.app-layout');
        if (layout) { layout.style.position = 'relative'; layout.style.zIndex = '1'; }

        return c;
    }

    function run() {
        // Skip on mobile for performance
        if (window.innerWidth < 768 || !document.querySelector('.app-layout')) return;

        const canvas = mkCanvas();
        const ctx    = canvas.getContext('2d');
        const LINK   = 130;
        let W, H, dots, raf;

        function resize() {
            W = canvas.width  = window.innerWidth;
            H = canvas.height = window.innerHeight;
        }

        function build() {
            const n = Math.min(90, Math.floor((W * H) / 12000));
            dots = Array.from({ length: n }, () => new Dot(W, H));
        }

        function tick() {
            ctx.clearRect(0, 0, W, H);

            const dark     = isDark();
            const dotColor = dark ? 'rgba(200,160,90,'  : 'rgba(160,120,60,';
            const lineColor= dark ? '184,115,42'        : '154,95,31';

            // lines
            for (let i = 0; i < dots.length; i++) {
                for (let j = i + 1; j < dots.length; j++) {
                    const dx = dots[i].x - dots[j].x;
                    const dy = dots[i].y - dots[j].y;
                    const d  = Math.sqrt(dx * dx + dy * dy);
                    if (d < LINK) {
                        ctx.save();
                        ctx.globalAlpha = (1 - d / LINK) * 0.35;
                        ctx.strokeStyle = `rgb(${lineColor})`;
                        ctx.lineWidth   = 0.8;
                        ctx.beginPath();
                        ctx.moveTo(dots[i].x, dots[i].y);
                        ctx.lineTo(dots[j].x, dots[j].y);
                        ctx.stroke();
                        ctx.restore();
                    }
                }
            }

            // dots
            dots.forEach(d => {
                ctx.save();
                ctx.globalAlpha = d.a * 0.85;
                ctx.fillStyle   = dotColor + '1)';
                d.step();
                d.draw(ctx);
                ctx.restore();
            });

            raf = requestAnimationFrame(tick);
        }

        resize(); build(); tick();

        new ResizeObserver(() => { resize(); build(); }).observe(document.body);

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) cancelAnimationFrame(raf);
            else tick();
        });
    }

    document.readyState === 'loading'
        ? document.addEventListener('DOMContentLoaded', run)
        : run();
})();
