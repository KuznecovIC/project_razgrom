// landing.js - основной файл с исправлениями и улучшениями

class ThemeManager {
  constructor() {
    this.themeToggle = document.getElementById('themeToggle');
    this.initTheme();
    this.setupEventListeners();
  }

  initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    this.applyTheme(savedTheme);
  }

  applyTheme(theme) {
    if (theme === 'dark') {
      document.body.classList.add('dark-theme');
      
      // Исключения - элементы, которые должны оставаться светлыми
      document.querySelectorAll('#reviews .card, #order .card, #order .form-label').forEach(el => {
        el.classList.add('force-light');
      });
      
      this.updateIcon('dark');
    } else {
      document.body.classList.remove('dark-theme');
      
      // Удаляем классы исключений
      document.querySelectorAll('.force-light').forEach(el => {
        el.classList.remove('force-light');
      });
      
      this.updateIcon('light');
    }
  }

  toggleTheme() {
    const isDark = document.body.classList.contains('dark-theme');
    const newTheme = isDark ? 'light' : 'dark';
    
    localStorage.setItem('theme', newTheme);
    this.applyTheme(newTheme);
  }

  updateIcon(theme) {
    const icon = this.themeToggle?.querySelector('i');
    if (!icon) return;

    icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
  }

  setupEventListeners() {
    this.themeToggle?.addEventListener('click', () => this.toggleTheme());
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
    this.initMasters();
    this.initServices();
    this.initAnimations();
    new ThemeManager();
    new SmoothScroll();
  }

  initMasters() {
    // Мастера с красивым оформлением
    this.masters = [
      {
        id: 1,
        name: "Алексей 'Бритва' Петров",
        photo: "{% static 'img/masters/master1.jpg' %}",
        description: "Специалист по классическим и современным стрижкам. Стаж 8 лет.",
        instagram: "@barber_alex"
      },
      {
        id: 2,
        name: "Дмитрий 'Стиль' Иванов",
        photo: "{% static 'img/masters/master2.jpg' %}",
        description: "Эксперт по бородам и уходу за ними. Любит сложные формы.",
        instagram: "@beard_master"
      },
      {
        id: 3,
        name: "Сергей 'Точность' Смирнов",
        photo: "{% static 'img/masters/master3.jpg' %}",
        description: "Мастер детализации. Идеальные линии и четкие контуры.",
        instagram: "@sharp_lines"
      }
    ];
  }

  initServices() {
    // Услуги с ценами
    this.services = [
      { id: 1, name: "Мужская стрижка", price: 1200 },
      { id: 2, name: "Детская стрижка", price: 800 },
      { id: 3, name: "Стрижка машинкой", price: 700 },
      { id: 4, name: "Оформление бороды", price: 600 },
      { id: 5, name: "Королевское бритьё", price: 900 },
      { id: 6, name: "Комплекс (стрижка+борода)", price: 1500 },
      { id: 7, name: "Камуфляж седины", price: 500 },
      { id: 8, name: "Укладка", price: 300 }
    ];
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

// Запуск приложения при загрузке DOM
document.addEventListener('DOMContentLoaded', () => new App());