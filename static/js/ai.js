// static/js/ai.js - TÜM SAYFALAR İÇİN TAM, TEMİZ VE ÇALIŞAN VERSİYON

document.addEventListener('DOMContentLoaded', () => {

    // =================================================================================
    // 1. MERKEZİ API İSTEK FONKSİYONU
    // =================================================================================
    const apiFetch = async (url, options = {}) => {
        const config = {
            ...options,
            headers: { 'Content-Type': 'application/json', ...options.headers },
            credentials: 'include' // HttpOnly çerezlerin gönderilmesi için zorunlu
        };
        try {
            const response = await fetch(url, config);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: `Sunucu Hatası: ${response.status}` }));
                throw new Error(errorData.detail);
            }
            const contentType = response.headers.get("content-type");
            return contentType && contentType.includes("application/json") ? response.json() : null;
        } catch (error) {
            console.error("API İsteği Hatası:", error.message);
            throw error; // Hatayı, onu çağıran fonksiyona geri fırlat
        }
    };

    // =================================================================================
    // 2. SAYFA YÖNLENDİRME VE BAŞLATMA MANTIĞI
    // =================================================================================
    // Hangi sayfada olduğumuzu kontrol edip ilgili başlatma fonksiyonunu çağırıyoruz.

    // Yönetim Paneli / Haftalık Plan Sayfası (ai_weekly.html)
    if (document.getElementById('aiPanel')) {
        initializeAiDashboard();
    }
    // Anlık Öneriler Sayfası (ai_recommendation.html)
    else if (document.querySelector('.recommendations-section')) {
        initializeRecommendationPage();
    }
    // Ana Giriş Sayfası (ai.html)
    else if (document.getElementById('navigateToPlanner')) {
        console.log("AI ana sayfası yüklendi.");
    }

    // =================================================================================
    // 3. SAYFA BAŞLATMA FONKSİYONLARI
    // =================================================================================

    // ai_weekly.html için
    function initializeAiDashboard() {
        // Sekme (Tab) değiştirme mantığı
        const tabs = document.querySelectorAll('.nav-tab');
        const contents = document.querySelectorAll('.tab-content');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(item => item.classList.remove('active'));
                contents.forEach(item => item.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById(tab.dataset.tab).classList.add('active');
            });
        });

        loadWeeklyPlan(document.getElementById('aiWeeklyPlan'));
        initializeManualPlanner();
    }

    // ai_recommendation.html için
    function initializeRecommendationPage() {
        fetchAndRenderDailyTasks(document.getElementById('recommendationArea'));
    }

    // =================================================================================
    // 4. VERİ ÇEKME VE GÖRSELLEŞTİRME FONKSİYONLARI
    // =================================================================================

    // --- HAFTALIK PLAN İÇİN ---

    async function loadWeeklyPlan(container) {
        if (!container) return;
        container.innerHTML = '<p class="loading">Haftalık planın kontrol ediliyor...</p>';
        try {
            const existingPlan = await apiFetch('/ai/get-weekly-plan');
            renderWeeklyPlanAsTable(existingPlan, container);
        } catch (error) {
            if (error.message && error.message.includes("bulunamadı")) {
                container.innerHTML = `
                    <div class="no-plan-found">
                        <h4>Plan Bulunamadı</h4>
                        <p>Bu hafta için henüz bir yapay zeka planı oluşturulmadı.</p>
                        <button id="createPlanBtn" class="nav-button">🤖 Yeni Plan Oluştur</button>
                    </div>`;
                document.getElementById('createPlanBtn').addEventListener('click', handleCreatePlanClick);
            } else {
                container.innerHTML = `<p class="error">Plan yüklenirken bir hata oluştu: ${error.message}</p>`;
            }
        }
    }

    async function handleCreatePlanClick(event) {
        const container = document.getElementById('aiWeeklyPlan');
        const button = event.target;
        button.disabled = true;
        button.textContent = 'Oluşturuluyor...';
        try {
            const newPlan = await apiFetch('/ai/generate-weekly-plan', { method: 'POST' });
            renderWeeklyPlanAsTable(newPlan, container);
        } catch(error) {
            container.innerHTML = `<p class="error">Plan oluşturulamadı: ${error.message}</p>`;
        }
    }

    function renderWeeklyPlanAsTable(planData, container) {
        if (!planData || !planData.tasks || planData.tasks.length === 0) {
            container.innerHTML = `<p class="error">Görüntülenecek geçerli bir plan verisi bulunamadı.</p>`;
            return;
        }

        const introHTML = `
            <div class="plan-intro">
                <h3>${planData.subject || 'Haftalık Planınız'}</h3>
                <p>${planData.goal || 'Yapay zeka tarafından sizin için özenle hazırlandı.'}</p>
            </div>
        `;

        const daysInOrder = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar'];
        const schedule = daysInOrder.reduce((acc, day) => ({ ...acc, [day]: [] }), {});

        planData.tasks.forEach(task => {
            if (schedule[task.day_of_week]) {
                schedule[task.day_of_week].push(`<li>${task.activity}<span>${task.duration_minutes} dk</span></li>`);
            }
        });

        const tableHTML = `
            <div class="table-responsive">
                <table class="weekly-schedule-table">
                    <thead>
                        <tr>
                            ${daysInOrder.map(day => `<th>${day}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            ${daysInOrder.map(day => `
                                <td>
                                    <ul>
                                        ${schedule[day].join('') || '<li><em>Boş</em></li>'}
                                    </ul>
                                </td>
                            `).join('')}
                        </tr>
                    </tbody>
                </table>
            </div>
        `;

        container.innerHTML = introHTML + tableHTML;
    }

    // --- GÜNLÜK INTERAKTİF GÖREVLER İÇİN ---

    async function fetchAndRenderDailyTasks(container) {
        if (!container) return;
        container.innerHTML = '<p class="loading">Sana özel adımlar yükleniyor...</p>';
        try {
            const tasks = await apiFetch('/ai/get-daily-tasks');
            renderInteractiveTasks(tasks, container);
        } catch (error) {
            container.innerHTML = `<p class="error">${error.message}</p>`;
            // Hata durumunda ilerleme çubuğunu gizle
            const progressContainer = document.getElementById('progressContainer');
            if(progressContainer) progressContainer.style.display = 'none';
        }
    }

    function renderInteractiveTasks(tasks, container) {
        container.innerHTML = '';
        if (!tasks || tasks.length === 0) {
            container.innerHTML = `<div class="recommendation-card-plain"><p>Bugün için henüz bir görev oluşturulmadı. Harika bir gün seni bekliyor!</p></div>`;
            return;
        }

        tasks.forEach(task => {
            const card = document.createElement('div');
            card.className = 'recommendation-card';
            card.innerHTML = `
                <input type="checkbox" id="task-${task.id}" class="task-checkbox" data-task-id="${task.id}" ${task.is_completed ? 'checked' : ''}>
                <label for="task-${task.id}">${task.description}</label>
            `;
            container.appendChild(card);
        });

        container.addEventListener('change', async (e) => {
            if (e.target.classList.contains('task-checkbox')) {
                const taskId = e.target.dataset.taskId;
                e.target.disabled = true; // Spam'i önle
                try {
                    await apiFetch(`/ai/complete-daily-task/${taskId}`, { method: 'POST' });
                    updateProgressBar();
                } catch (error) {
                    console.error("Görev güncellenemedi:", error);
                    e.target.checked = !e.target.checked;
                } finally {
                    e.target.disabled = false; // Checkbox'ı tekrar aktif et
                }
            }
        });

        // Sayfa ilk yüklendiğinde ilerleme çubuğunu ayarla
        updateProgressBar();
    }

    // =================================================================================
    // 5. YARDIMCI FONKSİYONLAR
    // =================================================================================

    function updateProgressBar() {
        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const completionMessage = document.getElementById('completionMessage');
        const checkboxes = document.querySelectorAll('.task-checkbox');

        if (!progressContainer || !progressBar || !progressText || !completionMessage) return;

        if (checkboxes.length === 0) {
            progressContainer.style.display = 'none';
            return;
        }

        progressContainer.style.display = 'block';
        const totalTasks = checkboxes.length;
        const completedTasks = document.querySelectorAll('.task-checkbox:checked').length;
        const percentage = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

        progressBar.style.width = `${percentage}%`;
        progressText.textContent = `${completedTasks} / ${totalTasks} adım tamamlandı.`;

        if (percentage === 100) {
            completionMessage.style.display = 'block';
            progressText.style.display = 'none';
        } else {
            completionMessage.style.display = 'none';
            progressText.style.display = 'block';
        }
    }

    function initializeManualPlanner() {
        const addTaskBtn = document.getElementById('addTaskBtn');
        if (!addTaskBtn) return;

        const taskInput = document.getElementById('taskInput');
        const daySelect = document.getElementById('daySelect');
        const userWeeklyPlanContainer = document.getElementById('userWeeklyPlan');
        const dayNames = { monday: "Pazartesi", tuesday: "Salı", wednesday: "Çarşamba", thursday: "Perşembe", friday: "Cuma", saturday: "Cumartesi", sunday: "Pazar" };

        Object.keys(dayNames).forEach(dayKey => {
            if (!userWeeklyPlanContainer.querySelector(`#${dayKey}`)) {
                const dayContainer = document.createElement('div');
                dayContainer.className = 'plan-day-manual';
                dayContainer.id = dayKey;
                dayContainer.innerHTML = `<h4>${dayNames[dayKey]}</h4><ul></ul>`;
                userWeeklyPlanContainer.appendChild(dayContainer);
            }
        });

        addTaskBtn.addEventListener('click', () => {
            const taskText = taskInput.value.trim();
            if (taskText === "") { alert("Lütfen bir görev girin."); return; }
            const taskList = userWeeklyPlanContainer.querySelector(`#${daySelect.value} ul`);
            const newTask = document.createElement('li');
            newTask.textContent = taskText;
            taskList.appendChild(newTask);
            taskInput.value = "";
        });
    }
});