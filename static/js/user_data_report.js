document.addEventListener('DOMContentLoaded', () => {
    const API_ENDPOINTS = {
        OVERVIEW: '/reports/me',
        JOURNEY: '/reports/me/journey',
        TROPHIES: '/reports/me/trophies'
    };

    const elements = {
        tabs: document.querySelector('.tabs'),
        tabButtons: document.querySelectorAll('.tab-btn'),
        tabContents: document.querySelectorAll('.tab-content'),
        overview: {
            chartCanvas: document.getElementById('progressChart'),
            statShowcase: document.getElementById('stat-showcase-container'),
            activityList: document.querySelector('.activity-card .activity-list'),
            focusSection: document.getElementById('overview-focus-section'),
            weeklySection: document.getElementById('overview-weekly-section'),
            weeklyChartCanvas: document.getElementById('weeklyChart'),
        },
        journey: {
            loader: document.getElementById('loader'),
            container: document.getElementById('journey-container'),
            staircase: document.getElementById('staircase-container'),
            details: document.getElementById('details-content'),
            trophySection: document.getElementById('trophy-section'),
        }
    };

    const state = {
        overviewChart: null,
        weeklyChart: null,
        journeyData: [],
        overviewData: null
    };

    // Sekme Yönetimi
    elements.tabs.addEventListener('click', (e) => {
        const targetButton = e.target.closest('.tab-btn:not(.dashboard-btn)');
        if (!targetButton) return;
        const tabId = targetButton.dataset.tab;
        elements.tabButtons.forEach(btn => {
            if (!btn.classList.contains('dashboard-btn')) { btn.classList.remove('active'); }
        });
        elements.tabContents.forEach(content => content.classList.remove('active'));
        targetButton.classList.add('active');
        document.getElementById(`content-${tabId}`).classList.add('active');
    });

    // Başlangıç
    async function initializeAll() {
        // Bu sıralama önemli, çünkü Overview raporu Journey verisini kullanabiliyor.
        await initializeJourneyReport();
        await initializeOverviewReport();
    }
    initializeAll();

    // 1. GENEL BAKIŞ FONKSİYONLARI
    async function initializeOverviewReport() {
        try {
            const report = await fetchData(API_ENDPOINTS.OVERVIEW);
            state.overviewData = report;

            renderOverviewStats(report.overall_stats);
            renderRecentActivities(report.recent_activities);
            renderOverviewChart(report.chart_data);
            renderWeeklyPerformance(report.weekly_performance);

            if (state.journeyData && state.journeyData.length > 0) {
                renderFocusSection(report.overall_stats.most_challenging_category);
            }
        } catch (error) {
            console.error("Genel Bakış raporu işlenirken bir hata oluştu:", error);
            elements.overview.statShowcase.innerHTML = `<p style="text-align:center; width:100%;">Genel bakış verileri yüklenemedi. Lütfen daha sonra tekrar deneyin.</p>`;
        }
    }

    function renderOverviewStats(stats) {
        if (!stats) return;
         elements.overview.statShowcase.innerHTML = `
                <div class="stat-card-lg red"><div class="icon-bg"><i class="fas fa-calculator"></i></div><div class="stat-info"><div class="value">${stats.total_questions_solved}</div><div class="label">Toplam Soru</div></div></div>
                <div class="stat-card-lg green"><div class="icon-bg"><i class="fas fa-star"></i></div><div class="stat-info"><div class="value">${stats.most_challenging_category}</div><div class="label">Gelişim Alanın</div></div></div>
                <div class="stat-card-lg orange"><div class="icon-bg"><i class="fas fa-stopwatch"></i></div><div class="stat-info"><div class="value">${stats.avg_reaction_time}s</div><div class="label">Ortalama Hızın</div></div></div>
                <div class="stat-card-lg blue"><div class="icon-bg"><i class="fas fa-check-circle"></i></div><div class="stat-info"><div class="value">${stats.total_correct_answers}</div><div class="label">Toplam Doğru</div></div></div>`;
        }
    function renderRecentActivities(activities) {
        const list = elements.overview.activityList;
        list.innerHTML = '';
        if (!activities || activities.length === 0) {
            list.innerHTML = `<li>Harika! Tekrar etmen gereken bir egzersiz bulunmuyor.</li>`;
            return;
        }
        activities.forEach(activity => {
            const date = new Date(activity.datetime).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long' });
            list.innerHTML += `<li><div class="activity-icon"><i class="fas fa-puzzle-piece"></i></div><div class="activity-details"><strong class="activity-title">${activity.game_type}</strong><span class="activity-date">${date} - Doğrusu: ${activity.correct_answer}</span></div></li>`;
        });
    }

    function renderOverviewChart(chartData) {
        if (state.overviewChart) state.overviewChart.destroy();
        if (!chartData || !chartData.labels || chartData.labels.length === 0) {
            document.querySelector('.chart-container-overview').innerHTML = '<p class="placeholder-text" style="text-align:center; padding-top: 4rem;">Grafik için yeterli veri yok.</p>';
            return;
        }
        const backgroundColors = ['#8b5cf6', '#3b82f6', '#ef4444', '#f59e0b', '#16a34a', '#6b7280'];
        state.overviewChart = new Chart(elements.overview.chartCanvas.getContext('2d'), {
            type: 'doughnut', data: { labels: chartData.labels, datasets: [{
                label: 'Egzersiz Sayısı', data: chartData.data,
                backgroundColor: backgroundColors, borderColor: '#fff', borderWidth: 4
            }]},
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { padding: 15 } } } }
        });
    }

    String.prototype.capitalize = function() { return this.charAt(0).toUpperCase() + this.slice(1); }

    function renderFocusSection(category) {
        if (category === "Yok" || !state.journeyData || state.journeyData.length === 0) {
            elements.overview.focusSection.style.display = 'none';
            return;
        }
        elements.overview.focusSection.style.display = 'block';

        const categoryData = state.journeyData
            // --- NİHAİ DÜZELTME BURADA ---
            // 'act.category' özelliğinin var olup olmadığını kontrol ederek hatayı önlüyoruz.
            .map(day => ({ date: day.journey_date, activities: day.activities.filter(act => act.category && act.category.capitalize() === category) }))
            .filter(day => day.activities.length > 0)
            .map(day => ({
                date: new Date(day.date).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' }),
                avgTime: day.activities.reduce((sum, act) => sum + act.reaction_time, 0) / day.activities.length
            }));

        if (categoryData.length < 2) {
            elements.overview.focusSection.style.display = 'none';
            return;
        }

        elements.overview.focusSection.innerHTML = `<div class="card focus-card"><div><h2>Gelişim Odağı: <span style="color: var(--primary-color);">${category}</span></h2><p>Bu alandaki hızının zamanla nasıl geliştiğini grafikte görebilirsin.</p></div><div class="focus-chart-container"><canvas id="focusChart"></canvas></div></div>`;

        new Chart(document.getElementById('focusChart').getContext('2d'), {
            type: 'line', data: { labels: categoryData.map(d => d.date), datasets: [{
                label: 'Ortalama Hız (s)', data: categoryData.map(d => d.avgTime),
                borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true, tension: 0.4
            }]},
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
        });
    }

    function renderWeeklyPerformance(weeklyData) {
        if (!weeklyData || Object.values(weeklyData).every(v => v === 0)) {
            elements.overview.weeklySection.style.display = 'none';
            return;
        };
        elements.overview.weeklySection.style.display = 'block';
        if (state.weeklyChart) state.weeklyChart.destroy();
        state.weeklyChart = new Chart(elements.overview.weeklyChartCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: Object.keys(weeklyData),
                datasets: [{
                    label: 'Tekrar Sayısı', data: Object.values(weeklyData),
                    backgroundColor: 'rgba(59, 130, 246, 0.6)', borderColor: '#3b82f6',
                    borderWidth: 2, borderRadius: 5
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 }}}, plugins: { legend: { display: false }}}
        });
    }

    // 2. GELİŞİM MERDİVENİ FONKSİYONLARI
    async function initializeJourneyReport() {
        try {
            const report = await fetchData(API_ENDPOINTS.JOURNEY);
            if (!report.journey_data || report.journey_data.length === 0) {
                elements.journey.loader.innerHTML = `<i class="fas fa-map-signs"></i><p>Henüz bir gelişim merdivenin yok.<br>Egzersizleri tamamla ve basamakları çıkmaya başla!</p>`;
                return;
            }
            state.journeyData = report.journey_data.map((day, index) => ({ ...day, dayNumber: index + 1 }));
            elements.journey.loader.style.display = 'none';
            elements.journey.container.style.display = 'block';
            renderJourneyStairs();
            if (state.journeyData.length > 0) { showJourneyDayDetails(state.journeyData[state.journeyData.length - 1], state.journeyData.length - 1); }
            initializeTrophySection();
        } catch (error) {
            console.error('Yolculuk verileri yüklenemedi:', error);
            elements.journey.loader.innerHTML = `<i class="fas fa-exclamation-triangle"></i><p>Rapor yüklenirken bir sorun oluştu.</p>`;
        }
    }

    function renderJourneyStairs() {
        const container = elements.journey.staircase; container.innerHTML = '';
        const icons = ['fa-seedling', 'fa-rocket', 'fa-award', 'fa-star', 'fa-trophy'];
        state.journeyData.forEach((day, index) => {
            const step = document.createElement('div'); step.className = 'stair-step'; step.dataset.index = index;
            const iconClass = icons[index % icons.length];
            step.innerHTML = `<span class="stair-step-num">${day.dayNumber}</span> <span class="stair-step-date">${new Date(day.journey_date).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })}</span><i class="fas ${iconClass}"></i>`;
            step.addEventListener('click', () => showJourneyDayDetails(day, index));
            container.appendChild(step);
        });
    }

    function showJourneyDayDetails(day, index) {
        const dateLocale = new Date(day.journey_date).toLocaleDateString('tr-TR', { weekday: 'long', day: 'numeric', month: 'long' });
        elements.journey.details.innerHTML = `
            <div class="details-info"><p class="date">📅 ${dateLocale}</p><p>⏱️ Ortalama Hız: <strong>${day.reaction_time.toFixed(2)}s</strong></p><p>🎯 Tekrar Sayısı: <strong>${day.total_questions} egzersiz</strong></p></div>
            <div><p style="font-weight: 600;">🧠 O Gün Tekrar Edilenler:</p><ul class="activity-list">${day.activities.map(act => `<li><div class="activity-icon"><i class="fas fa-puzzle-piece"></i></div><div class="activity-details"><strong class="activity-title">${act.game_type}</strong></div></li>`).join('')}</ul></div>`;
        highlightActiveStep(index);
    }

    async function initializeTrophySection() {
        try {
            const trophies = await fetchData(API_ENDPOINTS.TROPHIES);
            if (trophies.length === 0) return;
            elements.journey.trophySection.innerHTML = `<div class="card"><h3><i class="fas fa-trophy" style="color:#f59e0b;"></i> Madalya Köşesi</h3><div class="trophy-grid">${trophies.map(t => `<div class="trophy-card ${t.color_class}"><i class="icon ${t.icon}"></i><h4>${t.title}</h4><p>${t.description}</p></div>`).join('')}</div></div>`;
        } catch (error) {
            console.error("Madalyalar alınamadı:", error);
        }
    }

    function highlightActiveStep(index) {
        elements.journey.staircase.querySelectorAll('.stair-step.active').forEach(el => el.classList.remove('active'));
        const step = elements.journey.staircase.querySelector(`.stair-step[data-index='${index}']`);
        if (step) step.classList.add('active');
    }

    async function fetchData(url) {
        const response = await fetch(url, { credentials: 'include' });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }
});