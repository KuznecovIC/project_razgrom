class ThemeManager {
  constructor() {
    this.themeToggle = document.getElementById('themeToggle');
    this.initTheme();
    this.setupEventListeners();
  }

  initTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    const currentTheme = savedTheme || (prefersDark ? 'dark' : 'light');

    document.body.classList.toggle('dark-mode', currentTheme === 'dark');
    this.updateIcon(currentTheme);
  }

  toggleTheme() {
    const isDark = document.body.classList.toggle('dark-mode');
    const newTheme = isDark ? 'dark' : 'light';

    localStorage.setItem('theme', newTheme);
    this.updateIcon(newTheme);
  }

  updateIcon(theme) {
    const icon = this.themeToggle?.querySelector('i');
    if (!icon) return;

    icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
  }

  setupEventListeners() {
    this.themeToggle?.addEventListener('click', () => this.toggleTheme());
  }

  toggleTheme() {
    localStorage.setItem('theme', 'dark'); // или 'light'

// При загрузке страницы
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
    document.body.classList.add(savedTheme);
}
  }

  updateIcon(theme) {
    if (this.themeToggle) {
      const icon = this.themeToggle.querySelector('i');
      if (icon) {
        icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
      }
    }
  }

  setupEventListeners() {
    if (this.themeToggle) {
      this.themeToggle.addEventListener('click', () => this.toggleTheme());
    }
  }
}

class SmoothScroll {
  constructor() {
    this.setupAnchorLinks();
  }

  setupAnchorLinks() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = anchor.getAttribute('href');
        const targetElement = document.querySelector(targetId);
        
        if (targetElement) {
          window.scrollTo({
            top: targetElement.offsetTop - 70,
            behavior: 'smooth'
          });

          // Закрываем мобильное меню если открыто
          const navbarCollapse = document.querySelector('.navbar-collapse.show');
          if (navbarCollapse) {
            new bootstrap.Collapse(navbarCollapse, { toggle: false }).hide();
          }
        }
      });
    });
  }
}

class App {
  constructor() {
    try {
      new ThemeManager();
      new SmoothScroll();
      this.initAnimations();
    } catch (error) {
      console.error('Ошибка инициализации:', error);
    }
  }
  init() {
    document.addEventListener('DOMContentLoaded', () => {
      try {
        new ThemeManager();
        new SmoothScroll();
        this.initAnimations();
      } catch (error) {
        console.error('Ошибка инициализации:', error);
      }
    });
  }

  initAnimations() {
    const animateOnScroll = () => {
      const elements = document.querySelectorAll('.fade-in');
      
      elements.forEach(el => {
        const elementTop = el.getBoundingClientRect().top;
        const windowHeight = window.innerHeight;
        
        if (elementTop < windowHeight - 100) {
          el.style.opacity = '1';
          el.style.transform = 'translateY(0)';
        }
      });
    };

    // Инициализация анимаций
    document.querySelectorAll('.fade-in').forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(20px)';
      el.style.transition = 'all 0.6s ease';
    });

    // Запускаем при первой загрузке
    animateOnScroll();
    
    // И при скролле
    window.addEventListener('scroll', animateOnScroll);
  }
}
document.addEventListener('DOMContentLoaded', function() {
  const themeToggle = document.getElementById('themeToggle');
  
  // Проверяем сохраненную тему
  const savedTheme = localStorage.getItem('theme') || 'light';
  
  // Применяем сохраненную тему
  if (savedTheme === 'dark') {
    document.body.classList.remove('light-theme');
    document.body.classList.add('dark-theme');
    themeToggle.innerHTML = '<i class="bi bi-sun-fill"></i>';
  }

  // Обработчик переключения темы
  themeToggle.addEventListener('click', function() {
    if (document.body.classList.contains('light-theme')) {
      // Переключаем на темную
      document.body.classList.remove('light-theme');
      document.body.classList.add('dark-theme');
      localStorage.setItem('theme', 'dark');
      themeToggle.innerHTML = '<i class="bi bi-sun-fill"></i>';
    } else {
      // Переключаем на светлую
      document.body.classList.remove('dark-theme');
      document.body.classList.add('light-theme');
      localStorage.setItem('theme', 'light');
      themeToggle.innerHTML = '<i class="bi bi-moon-fill"></i>';
    }
  });

  // Плавная прокрутка для якорных ссылок
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        window.scrollTo({
          top: target.offsetTop - 70,
          behavior: 'smooth'
        });
      }
    });
  });
});

// Запуск приложения
new App();
