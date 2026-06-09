/**
 * NeoMuse Application JS
 * Handles form confirmations, dark mode toggle, and accessibility features
 */

// ============================================================================
// Dark Mode Toggle
// ============================================================================

function initDarkModeToggle() {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const storedMode = localStorage.getItem('theme-mode');
    const isDark = storedMode ? storedMode === 'dark' : prefersDark;

    if (isDark) {
        document.documentElement.style.colorScheme = 'dark';
        document.body.classList.add('dark-mode');
    }
}

// ============================================================================
// Keyboard Shortcuts
// ============================================================================

function initKeyboardShortcuts() {
    document.addEventListener('keydown', function (e) {
        // Ctrl/Cmd + K to focus search (if search exists)
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Escape to dismiss modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const instance = bootstrap.Modal.getInstance(modal);
                if (instance) instance.hide();
            });
        }
    });
}

// ============================================================================
// Form Confirmation
// ============================================================================

function initFormConfirmations() {
    document.querySelectorAll('form[data-confirm]').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

// ============================================================================
// Touch Feedback for Mobile
// ============================================================================

function initTouchFeedback() {
    const buttons = document.querySelectorAll('button, [role="button"], .btn');
    buttons.forEach(btn => {
        btn.addEventListener('touchstart', function () {
            this.style.opacity = '0.8';
        });
        btn.addEventListener('touchend', function () {
            this.style.opacity = '1';
        });
    });
}

// ============================================================================
// Smooth Scrolling for Hash Links
// ============================================================================

function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#') return;

            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                target.focus();
            }
        });
    });
}

// ============================================================================
// Table Responsiveness
// ============================================================================

function makeTablesResponsive() {
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
        if (table.offsetWidth > window.innerWidth) {
            table.style.overflowX = 'auto';
        }
    });
}

// ============================================================================
// Loading States for Forms
// ============================================================================

function initFormLoadingStates() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function () {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerText;
                submitBtn.innerText = '⏳ Загрузка...';

                // Re-enable after 2 seconds (safety timeout)
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerText = originalText;
                }, 2000);
            }
        });
    });
}

// ============================================================================
// Lazy Loading Images
// ============================================================================

function initLazyLoadingImages() {
    const images = document.querySelectorAll('img[loading="lazy"]');
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src || img.src;
                    img.classList.add('loaded');
                    observer.unobserve(img);
                }
            });
        });
        images.forEach(img => imageObserver.observe(img));
    }
}

// ============================================================================
// Mobile Sidebar Toggle
// ============================================================================

function initMobileSidebarToggle() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.content');

    if (window.innerWidth <= 768) {
        // Close sidebar on link click
        document.querySelectorAll('.nav-item').forEach(link => {
            link.addEventListener('click', () => {
                if (sidebar) {
                    sidebar.classList.remove('open');
                }
            });
        });

        // Close sidebar when clicking outside
        if (mainContent) {
            mainContent.addEventListener('click', () => {
                if (sidebar && sidebar.classList.contains('open')) {
                    sidebar.classList.remove('open');
                }
            });
        }
    }
}

// ============================================================================
// Notification Toast
// ============================================================================

function showToast(message, type = 'info', duration = 4000) {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'polite');
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Закрыть"></button>
    `;

    const container = document.querySelector('.page-body');
    if (container) {
        container.insertBefore(toast, container.firstChild);
    }

    if (duration > 0) {
        setTimeout(() => {
            toast.remove();
        }, duration);
    }
}

// ============================================================================
// Focus Management
// ============================================================================

function manageFocusOnNavigation() {
    document.querySelectorAll('a[href^="/"]').forEach(link => {
        link.addEventListener('click', function (e) {
            if (this.target !== '_blank' && e.button === 0) {
                setTimeout(() => {
                    const mainContent = document.querySelector('[role="main"]');
                    if (mainContent) {
                        mainContent.focus();
                    }
                }, 100);
            }
        });
    });
}

// ============================================================================
// Initialize All
// ============================================================================

document.addEventListener('DOMContentLoaded', function () {
    initDarkModeToggle();
    initKeyboardShortcuts();
    initFormConfirmations();
    initTouchFeedback();
    initSmoothScrolling();
    makeTablesResponsive();
    initFormLoadingStates();
    initLazyLoadingImages();
    initMobileSidebarToggle();
    manageFocusOnNavigation();

    // Handle window resize
    window.addEventListener('resize', makeTablesResponsive);

    // Respect prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia('(prefers-motion: reduce)').matches;
    if (prefersReducedMotion) {
        document.documentElement.style.setProperty('--duration-fast', '0.01ms');
        document.documentElement.style.setProperty('--duration-normal', '0.01ms');
        document.documentElement.style.setProperty('--duration-slow', '0.01ms');
    }
});

// Expose toast function globally
window.showToast = showToast;

// ============================================================================
// Ripple effect on buttons
// ============================================================================
document.addEventListener('click', function (e) {
    const btn = e.target.closest('.btn, .qa-btn, .quick-tile, .nav-item');
    if (!btn) return;
    const r = document.createElement('span');
    r.className = 'ripple';
    const rect = btn.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    r.style.cssText = `width:${size}px;height:${size}px;left:${e.clientX-rect.left-size/2}px;top:${e.clientY-rect.top-size/2}px`;
    btn.appendChild(r);
    r.addEventListener('animationend', () => r.remove());
});

// ============================================================================
// Card 3D tilt on mouse move
// ============================================================================
function initTilt() {
    if (window.innerWidth < 768) return; // no tilt on mobile — blocks taps
    document.querySelectorAll('.exc-card, .kpi-card, .quick-tile, .info-card').forEach(card => {
        card.addEventListener('mousemove', function (e) {
            const rect = this.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width  - 0.5;
            const y = (e.clientY - rect.top)  / rect.height - 0.5;
            this.style.transform = `translateY(-6px) rotateX(${-y*8}deg) rotateY(${x*8}deg)`;
            this.style.transition = 'transform 0.05s ease';
        });
        card.addEventListener('mouseleave', function () {
            this.style.transform = '';
            this.style.transition = 'transform 0.35s cubic-bezier(0.34,1.2,0.64,1)';
        });
    });
}

// ============================================================================
// Scroll reveal — elements animate when entering viewport
// ============================================================================
function initScrollReveal() {
    if (!('IntersectionObserver' in window)) return;
    const els = document.querySelectorAll('.panel, .exc-card, .exhibit-card, .info-card, .kpi-card');
    const io = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                io.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });
    els.forEach(el => {
        // Only if not already animated by CSS
        if (!el.closest('[style*="animation"]')) {
            el.style.opacity = '0';
            el.style.transform = 'translateY(16px)';
            el.style.transition = 'opacity 0.45s ease, transform 0.45s cubic-bezier(0.4,0,0.2,1)';
            io.observe(el);
        }
    });
}

document.addEventListener('DOMContentLoaded', function () {
    initTilt();
    initScrollReveal();
});

// ============================================================================
// Hero banner — animated geometric pattern canvas
// ============================================================================
(function initHeroCanvas() {
    const canvas = document.getElementById('heroCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let W, H, shapes, raf;

    // Shape types drawn as outlines
    const KINDS = ['circle', 'triangle', 'square', 'diamond', 'hexagon', 'cross'];

    function resize() {
        const rect = canvas.parentElement.getBoundingClientRect();
        W = canvas.width  = rect.width;
        H = canvas.height = rect.height;
    }

    function hexagon(ctx, x, y, r) {
        ctx.beginPath();
        for (let i = 0; i < 6; i++) {
            const a = (Math.PI / 3) * i - Math.PI / 6;
            i === 0 ? ctx.moveTo(x + r * Math.cos(a), y + r * Math.sin(a))
                    : ctx.lineTo(x + r * Math.cos(a), y + r * Math.sin(a));
        }
        ctx.closePath();
    }

    function drawKind(kind, x, y, r, rot) {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(rot);
        ctx.beginPath();
        switch (kind) {
            case 'circle':
                ctx.arc(0, 0, r, 0, Math.PI * 2);
                break;
            case 'triangle':
                ctx.moveTo(0, -r); ctx.lineTo(r * 0.87, r * 0.5); ctx.lineTo(-r * 0.87, r * 0.5);
                ctx.closePath();
                break;
            case 'square':
                ctx.rect(-r, -r, r * 2, r * 2);
                break;
            case 'diamond':
                ctx.moveTo(0, -r * 1.3); ctx.lineTo(r, 0); ctx.lineTo(0, r * 1.3); ctx.lineTo(-r, 0);
                ctx.closePath();
                break;
            case 'hexagon':
                for (let i = 0; i < 6; i++) {
                    const a = (Math.PI / 3) * i - Math.PI / 6;
                    i === 0 ? ctx.moveTo(r * Math.cos(a), r * Math.sin(a))
                            : ctx.lineTo(r * Math.cos(a), r * Math.sin(a));
                }
                ctx.closePath();
                break;
            case 'cross': {
                const t = r * 0.3;
                ctx.rect(-t, -r, t*2, r*2);
                ctx.rect(-r, -t, r*2, t*2);
                break;
            }
        }
        ctx.restore();
    }

    function mkShape() {
        return {
            x: Math.random() * W,
            y: Math.random() * H,
            r: 6 + Math.random() * 22,
            kind: KINDS[Math.floor(Math.random() * KINDS.length)],
            rot: Math.random() * Math.PI * 2,
            rotV: (Math.random() - 0.5) * 0.008,
            vx: (Math.random() - 0.5) * 0.4,
            vy: (Math.random() - 0.5) * 0.3,
            alpha: 0.06 + Math.random() * 0.18,
            filled: Math.random() > 0.6,
            pulse: Math.random() * Math.PI * 2,
            pulseV: 0.012 + Math.random() * 0.018,
        };
    }

    function build() {
        const n = Math.max(14, Math.floor((W * H) / 7000));
        shapes = Array.from({ length: n }, mkShape);
    }

    function tick() {
        ctx.clearRect(0, 0, W, H);
        shapes.forEach(s => {
            s.x   += s.vx;
            s.y   += s.vy;
            s.rot += s.rotV;
            s.pulse += s.pulseV;
            if (s.x < -40) s.x = W + 40;
            if (s.x > W + 40) s.x = -40;
            if (s.y < -40) s.y = H + 40;
            if (s.y > H + 40) s.y = -40;

            const pr = s.r * (1 + 0.12 * Math.sin(s.pulse));
            ctx.save();
            ctx.globalAlpha = s.alpha;
            ctx.strokeStyle = 'rgba(255,255,255,0.9)';
            ctx.fillStyle   = 'rgba(255,255,255,0.9)';
            ctx.lineWidth   = 1.2;
            drawKind(s.kind, s.x, s.y, pr, s.rot);
            s.filled ? ctx.fill() : ctx.stroke();
            ctx.restore();
        });
        raf = requestAnimationFrame(tick);
    }

    function start() {
        resize();
        build();
        tick();
        new ResizeObserver(() => { resize(); build(); }).observe(canvas.parentElement);
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) cancelAnimationFrame(raf); else tick();
        });
    }

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    document.readyState === 'loading'
        ? document.addEventListener('DOMContentLoaded', start)
        : start();
})();

// ============================================================================
// Mobile startup safety — prevent blocking
// ============================================================================
document.addEventListener('DOMContentLoaded', function() {
    // Ensure page is visible even if JS errors
    document.documentElement.style.display = 'block';
    document.body.style.display = 'block';
}, { once: true });

// Hide splash/loading after 2s max (safety net)
if (document.readyState === 'loading') {
    setTimeout(() => {
        const loader = document.querySelector('.loader, .spinner, [style*="loading"]');
        if (loader) loader.style.display = 'none';
    }, 2000);
}
