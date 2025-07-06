/**
 * Управление темой приложения с улучшенной обработкой
 */
class ThemeManager {
  constructor() {
    this.themeToggle = document.getElementById('themeToggle');
    if (!this.themeToggle) return;
    
    try {
      this.initTheme();
      this.setupEventListeners();
    } catch (error) {
      console.error('ThemeManager error:', error);
    }
  }

  initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    this.applyTheme(savedTheme);
  }

  applyTheme(theme) {
    try {
      document.body.classList.toggle('dark-theme', theme === 'dark');
      this.updateIcon(theme);
      localStorage.setItem('theme', theme);
    } catch (error) {
      console.error('Error applying theme:', error);
    }
  }

  toggleTheme() {
    const isDark = document.body.classList.contains('dark-theme');
    this.applyTheme(isDark ? 'light' : 'dark');
  }

  updateIcon(theme) {
    const icon = this.themeToggle?.querySelector('i');
    if (!icon) return;
    
    icon.classList.toggle('bi-sun-fill', theme === 'dark');
    icon.classList.toggle('bi-moon-fill', theme === 'light');
  }

  setupEventListeners() {
    this.themeToggle?.addEventListener('click', () => this.toggleTheme());
  }
}

/**
 * Улучшенная плавная прокрутка
 */
class SmoothScroll {
  constructor() {
    try {
      this.setupAnchorLinks();
    } catch (error) {
      console.error('SmoothScroll error:', error);
    }
  }

  setupAnchorLinks() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = anchor.getAttribute('href');
        const targetElement = document.querySelector(targetId);
        
        if (targetElement) {
          this.scrollToElement(targetElement);
          this.closeMobileMenu();
        }
      });
    });
  }

  scrollToElement(element) {
    const offset = 70; // Высота навигации
    const targetPosition = element.getBoundingClientRect().top + window.pageYOffset;
    
    window.scrollTo({
      top: targetPosition - offset,
      behavior: 'smooth'
    });
  }

  closeMobileMenu() {
    try {
      const navbarCollapse = document.querySelector('.navbar-collapse.show');
      if (navbarCollapse && typeof bootstrap?.Collapse === 'function') {
        new bootstrap.Collapse(navbarCollapse, { toggle: false }).hide();
      }
    } catch (error) {
      console.error('Error closing mobile menu:', error);
    }
  }
}

/**
 * Главный класс приложения с улучшенной инициализацией
 */
class App {
  constructor() {
    this.initComponents();
    this.initAnimations();
  }

  initComponents() {
    try {
      new ThemeManager();
      new SmoothScroll();
    } catch (error) {
      console.error('Error initializing components:', error);
    }
  }

  initAnimations() {
    const animateOnScroll = () => {
      const windowHeight = window.innerHeight;
      const triggerOffset = 100;
      
      document.querySelectorAll('.fade-in').forEach(el => {
        const elementTop = el.getBoundingClientRect().top;
        const isVisible = elementTop < windowHeight - triggerOffset;
        
        el.style.opacity = isVisible ? '1' : '0';
        el.style.transform = isVisible ? 'translateY(0)' : 'translateY(20px)';
      });
    };

    // Инициализация анимаций
    document.querySelectorAll('.fade-in').forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(20px)';
      el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    });

    // Первая проверка
    requestAnimationFrame(animateOnScroll);
    
    // Обработчик скролла с троттлингом
    let isScrolling;
    window.addEventListener('scroll', () => {
      window.cancelAnimationFrame(isScrolling);
      isScrolling = requestAnimationFrame(animateOnScroll);
    }, { passive: true });
  }
}

// Безопасная инициализация
document.addEventListener('DOMContentLoaded', () => {
  try {
    new App();
  } catch (error) {
    console.error('Application initialization failed:', error);
  }
});
