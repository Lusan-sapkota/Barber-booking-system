// Theme Management
class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        // Set initial theme
        this.setTheme(this.currentTheme);
        
        // Setup navbar theme toggle
        this.setupNavbarToggle();
        
        // Listen for system theme changes
        this.watchSystemTheme();
    }

    setupNavbarToggle() {
        const navToggle = document.getElementById('navThemeToggle');
        if (navToggle) {
            navToggle.addEventListener('click', () => this.toggleTheme());
            this.updateNavToggleIcon(navToggle);
        }
    }

    updateNavToggleIcon(toggle) {
        const icon = toggle.querySelector('i');
        if (icon) {
            icon.className = `fas fa-${this.currentTheme === 'dark' ? 'sun' : 'moon'}`;
            toggle.title = `Switch to ${this.currentTheme === 'dark' ? 'light' : 'dark'} mode`;
        }
    }

    setTheme(theme) {
        this.currentTheme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update navbar toggle icon
        const navToggle = document.getElementById('navThemeToggle');
        if (navToggle) {
            this.updateNavToggleIcon(navToggle);
        }
        
        // Update meta theme-color for mobile browsers
        this.updateMetaThemeColor(theme);
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
        localStorage.setItem('theme-manual', 'true');
        
        // Add ripple effect to navbar toggle
        this.addRippleEffect();
    }

    addRippleEffect() {
        const navToggle = document.getElementById('navThemeToggle');
        if (navToggle) {
            navToggle.style.transform = 'scale(0.95)';
            setTimeout(() => {
                navToggle.style.transform = 'scale(1)';
            }, 150);
        }
    }

    updateMetaThemeColor(theme) {
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.name = 'theme-color';
            document.head.appendChild(metaThemeColor);
        }
        
        metaThemeColor.content = theme === 'dark' ? '#1a1a1a' : '#ffffff';
    }

    watchSystemTheme() {
        // Watch for system theme changes
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            mediaQuery.addEventListener('change', (e) => {
                // Only auto-switch if user hasn't manually set a preference
                if (!localStorage.getItem('theme-manual')) {
                    this.setTheme(e.matches ? 'dark' : 'light');
                }
            });
            
            // Set initial theme based on system preference if no manual preference
            if (!localStorage.getItem('theme')) {
                this.setTheme(mediaQuery.matches ? 'dark' : 'light');
            }
        }
    }

    // Auto-detect system theme
    detectSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    // Reset to system theme
    resetToSystemTheme() {
        localStorage.removeItem('theme');
        localStorage.removeItem('theme-manual');
        this.setTheme(this.detectSystemTheme());
    }
}

// Initialize theme manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.themeManager = new ThemeManager();
    
    // Add keyboard shortcut for theme toggle (Ctrl/Cmd + Shift + T)
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
            e.preventDefault();
            window.themeManager.toggleTheme();
        }
    });
});

// Listen for theme changes to update other components
window.addEventListener('themeChanged', function(e) {
    console.log(`Theme changed to: ${e.detail.theme}`);
});