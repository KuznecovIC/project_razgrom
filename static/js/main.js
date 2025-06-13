document.addEventListener('DOMContentLoaded', function() {
    // Анимация при загрузке
    const animateElements = () => {
        const elements = document.querySelectorAll('section');
        elements.forEach((el, index) => {
            setTimeout(() => {
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }, index * 200);
        });
    };

    // Инициализация анимации
    document.querySelectorAll('section').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'all 0.6s ease';
    });

    // Слайдер отзывов
    let currentSlide = 0;
    const slides = document.querySelectorAll('.slide');
    const totalSlides = slides.length;

    const showSlide = (n) => {
        slides.forEach(slide => slide.classList.remove('active'));
        currentSlide = (n + totalSlides) % totalSlides;
        slides[currentSlide].classList.add('active');
    };

    if (document.querySelector('.prev') && document.querySelector('.next')) {
        document.querySelector('.prev').addEventListener('click', () => showSlide(currentSlide - 1));
        document.querySelector('.next').addEventListener('click', () => showSlide(currentSlide + 1));
        
        // Автопереключение
        setInterval(() => showSlide(currentSlide + 1), 5000);
    }

    // Переключатель темы
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
        });

        // Проверка сохраненной темы
        if (localStorage.getItem('darkMode') === 'true') {
            document.body.classList.add('dark-mode');
        }
    }

    // Обработка кнопок записи
    document.querySelectorAll('.book-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const service = this.getAttribute('data-service');
            alert(`Вы выбрали: ${service}\nПеренаправляем на форму записи...`);
            document.querySelector('.booking').scrollIntoView({ behavior: 'smooth' });
        });
    });

    // Показываем индикатор загрузки
    const loader = document.querySelector('.loader');
    if (loader) {
        loader.style.display = 'block';
        setTimeout(() => {
            loader.style.display = 'none';
            animateElements();
        }, 1500);
    }

    // Анимация при скролле
    window.addEventListener('scroll', () => {
        const scrollPosition = window.scrollY;
        if (scrollPosition > 100) {
            document.querySelector('header').style.padding = '10px 20px';
        } else {
            document.querySelector('header').style.padding = '20px';
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // Фильтрация по статусу
    const statusFilter = document.getElementById('status-filter');
    const orderCards = document.querySelectorAll('.order-card');
    
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            const status = this.value;
            
            orderCards.forEach(card => {
                if (status === 'all' || card.classList.contains(`status-${status}`)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // Кнопка обновления
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            this.classList.add('refreshing');
            setTimeout(() => {
                location.reload();
            }, 1000);
        });
    }

    // Обработка кнопки редактирования
    document.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', function() {
            const orderId = this.getAttribute('data-order');
            alert(`Редактирование заявки #${orderId}\n(В реальном проекте здесь будет форма редактирования)`);
        });
    });

    // Анимация загрузки
    const cards = document.querySelectorAll('.order-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = `all 0.5s ease ${index * 0.1}s`;
        
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100);
    });
});

console.log('Барбершоп готов к работе!');