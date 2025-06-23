// landing.js - основной файл с исправлениями и улучшениями

/**
 * Класс для управления темой приложения
 * Реализует:
 * - Сохранение темы в localStorage
 * - Переключение между светлой и темной темами
 * - Обработку исключений для отдельных элементов
 */
class ThemeManager {
  constructor() {
    this.themeToggle = document.getElementById('themeToggle');
    this.initTheme();
    this.setupEventListeners();
  }

  // Инициализация темы из localStorage или установка светлой по умолчанию
  initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    this.applyTheme(savedTheme);
  }

  // Применение выбранной темы ко всему документу
  applyTheme(theme) {
    if (theme === 'dark') {
      document.body.classList.add('dark-theme');
      
      // Исключения - элементы, которые должны оставаться светлыми
      // (карточки отзывов и формы записи)
      document.querySelectorAll('#reviews .card, #order .card, #order .form-label').forEach(el => {
        el.classList.add('force-light');
      });
      
      this.updateIcon('dark');
    } else {
      document.body.classList.remove('dark-theme');
      
      // Удаляем классы исключений при возврате к светлой теме
      document.querySelectorAll('.force-light').forEach(el => {
        el.classList.remove('force-light');
      });
      
      this.updateIcon('light');
    }
  }

  // Переключение между темами
  toggleTheme() {
    const isDark = document.body.classList.contains('dark-theme');
    const newTheme = isDark ? 'light' : 'dark';
    
    localStorage.setItem('theme', newTheme);
    this.applyTheme(newTheme);
  }

  // Обновление иконки переключателя темы
  updateIcon(theme) {
    const icon = this.themeToggle?.querySelector('i');
    if (!icon) return;

    icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
  }

  // Настройка обработчиков событий
  setupEventListeners() {
    this.themeToggle?.addEventListener('click', () => this.toggleTheme());
  }
}

/**
 * Класс для плавной прокрутки к якорным ссылкам
 * Особенности:
 * - Учет высоты навигационной панели
 * - Автоматическое закрытие мобильного меню
 */
class SmoothScroll {
  constructor() {
    this.setupAnchorLinks();
  }

  // Настройка плавного скролла для всех якорных ссылок
  setupAnchorLinks() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = anchor.getAttribute('href');
        const targetElement = document.querySelector(targetId);
        
        if (targetElement) {
          // Прокрутка с учетом высоты навигации (70px)
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

/**
 * Главный класс приложения
 * Объединяет все компоненты и функциональность:
 * - Управление мастерами
 * - Управление услугами
 * - Анимации
 * - Тему
 * - Прокрутку
 */
class App {
  constructor() {
    this.initMasters();
    this.initServices();
    this.initAnimations();
    new ThemeManager();
    new SmoothScroll();
  }

  // Инициализация данных о мастерах (в реальном проекте - запрос к API)
  initMasters() {
    this.masters = [
      {
        id: 1,
        name: "Алексей 'Бритва' Петров",
        photo: "{% static 'img/masters/master1.jpg' %}",
        description: "Специалист по классическим и современным стрижкам. Стаж 8 лет.",
        instagram: "@barber_alex"
      },
      // ... остальные мастера
    ];
  }

  // Инициализация данных об услугах
  initServices() {
    this.services = [
      { id: 1, name: "Мужская стрижка", price: 1200 },
      // ... остальные услуги
    ];
  }

  // Настройка анимаций появления элементов при скролле
  initAnimations() {
    const animateOnScroll = () => {
      const elements = document.querySelectorAll('.fade-in');
      
      elements.forEach(el => {
        const elementTop = el.getBoundingClientRect().top;
        const windowHeight = window.innerHeight;
        
        // Анимация срабатывает когда элемент на 100px ниже верха окна
        if (elementTop < windowHeight - 100) {
          el.style.opacity = '1';
          el.style.transform = 'translateY(0)';
        }
      });
    };

    // Инициализация анимаций - установка начального состояния
    document.querySelectorAll('.fade-in').forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(20px)';
      el.style.transition = 'all 0.6s ease';
    });

    // Запускаем проверку при первой загрузке
    animateOnScroll();
    
    // И при каждом скролле
    window.addEventListener('scroll', animateOnScroll);
  }
}

// Запуск приложения после полной загрузки DOM
document.addEventListener('DOMContentLoaded', () => new App());