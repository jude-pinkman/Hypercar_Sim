// ==========================================
// HYPERCAR HOMEPAGE INTERACTIONS
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    initParallaxEffects();
    initVehicleCardInteractions();
    initSmoothScrolling();
});

// ==========================================
// PARALLAX BACKGROUND EFFECTS
// ==========================================

function initParallaxEffects() {
    const orbs = document.querySelectorAll('.gradient-orb');

    document.addEventListener('mousemove', (e) => {
        const mouseX = e.clientX / window.innerWidth;
        const mouseY = e.clientY / window.innerHeight;

        orbs.forEach((orb, index) => {
            const speed = (index + 1) * 0.05;
            const x = (mouseX - 0.5) * 100 * speed;
            const y = (mouseY - 0.5) * 100 * speed;

            orb.style.transform = `translate(${x}px, ${y}px)`;
        });
    });
}

// ==========================================
// VEHICLE CARD INTERACTIONS
// ==========================================

function initVehicleCardInteractions() {
    const vehicleCards = document.querySelectorAll('.vehicle-card');

    vehicleCards.forEach(card => {
        card.addEventListener('mouseenter', function () {
            // Add pulse animation to glow
            const glow = this.querySelector('.vehicle-glow');
            if (glow) {
                glow.style.animation = 'glowPulse 1.5s ease-in-out infinite';
            }
        });

        card.addEventListener('mouseleave', function () {
            const glow = this.querySelector('.vehicle-glow');
            if (glow) {
                glow.style.animation = '';
            }
        });

        // Click to navigate to simulator with vehicle pre-selected
        card.addEventListener('click', function () {
            const vehicleId = this.getAttribute('data-vehicle');
            window.location.href = `index.html?vehicle=${vehicleId}`;
        });
    });
}

// ==========================================
// SMOOTH SCROLLING
// ==========================================

function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));

            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// ==========================================
// SCROLL ANIMATIONS
// ==========================================

const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe feature cards
document.querySelectorAll('.feature-card').forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(30px)';
    card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(card);
});

// ==========================================
// DYNAMIC STATS COUNTER
// ==========================================

function animateCounter(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
}

// Trigger counter animation when stats bar is visible
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const statNumbers = entry.target.querySelectorAll('.stat-number');
            statNumbers.forEach(stat => {
                const text = stat.textContent;
                const number = parseInt(text.replace(/\D/g, ''));
                if (number) {
                    animateCounter(stat, number, 1500);
                }
            });
            statsObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

const statsBar = document.querySelector('.stats-bar');
if (statsBar) {
    statsObserver.observe(statsBar);
}

// ==========================================
// NAVIGATION SCROLL EFFECT
// ==========================================

let lastScroll = 0;
const nav = document.querySelector('.main-nav');

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;

    if (currentScroll > 100) {
        nav.style.background = 'rgba(10, 10, 10, 0.95)';
        nav.style.boxShadow = '0 5px 20px rgba(0, 0, 0, 0.3)';
    } else {
        nav.style.background = 'rgba(10, 10, 10, 0.8)';
        nav.style.boxShadow = 'none';
    }

    lastScroll = currentScroll;
});

// ==========================================
// KEYBOARD SHORTCUTS
// ==========================================

document.addEventListener('keydown', (e) => {
    // Press 'S' to go to simulator
    if (e.key === 's' || e.key === 'S') {
        if (!e.target.matches('input, textarea')) {
            window.location.href = 'index.html';
        }
    }

    // Press 'A' to go to about
    if (e.key === 'a' || e.key === 'A') {
        if (!e.target.matches('input, textarea')) {
            window.location.href = 'about.html';
        }
    }
});

// Add CSS animation for glow pulse
const style = document.createElement('style');
style.textContent = `
    @keyframes glowPulse {
        0%, 100% {
            opacity: 0.3;
            transform: scale(1);
        }
        50% {
            opacity: 0.5;
            transform: scale(1.1);
        }
    }
`;
document.head.appendChild(style);