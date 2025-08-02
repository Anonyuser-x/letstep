document.addEventListener('DOMContentLoaded', () => {

    // --- GENEL PANEL ELEMANLARI (TÜM SAYFALARDA ORTAK) ---
    const adminLayout = document.querySelector('.admin-layout');
    const sidebarToggleBtn = document.getElementById('sidebar-toggle');
    const teacherUsernameSpan = document.getElementById('teacher-username');

    // --- SAYFA TANIMLAYICILARI ---
    const dashboardPage = document.getElementById('dashboard-page');
    const studentsPage = document.getElementById('students-page');
    const reportsPage = document.getElementById('reports-page');

    // --- MODAL ELEMANLARI ---
    const addStudentModal = document.getElementById('add-student-modal');
    const addStudentBtn = document.getElementById('add-student-btn');
    const addStudentForm = document.getElementById('add-student-form');
    const closeModalBtns = document.querySelectorAll('.close-modal-btn');
    const confirmationModal = document.getElementById('confirmation-modal');
    let studentIdToDelete = null;

    // --- SPINNER HTML ---
    const spinner = `<tr class="spinner-row"><td colspan="100%"><div class="spinner-wrapper"><div class="spinner"></div></div></td></tr>`;

    // ===============================================================
    // --- GENEL UI & YARDIMCI FONKSİYONLAR ---
    // ===============================================================

    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        if (!container) return;
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const iconClass = type === 'success' ? 'fas fa-check-circle' : 'fas fa-times-circle';
        toast.innerHTML = `<i class="toast-icon ${iconClass}"></i><span class="toast-message">${message}</span>`;
        container.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 100);
        setTimeout(() => {
            toast.classList.remove('show');
            toast.addEventListener('transitionend', () => toast.remove());
        }, 5000);
    }

    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', () => adminLayout.classList.toggle('sidebar-collapsed'));
    }

    // ===============================================================
    // --- MODAL YÖNETİMİ ---
    // ===============================================================

    if (addStudentBtn && addStudentModal) {
        addStudentBtn.onclick = () => { addStudentModal.style.display = 'block'; };
    }

    closeModalBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const modalToClose = btn.closest('.modal');
            if (modalToClose) { modalToClose.style.display = 'none'; }
        });
    });

    window.addEventListener('click', (event) => {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    });

    function openConfirmationModal(studentId) {
        studentIdToDelete = studentId;
        if (confirmationModal) confirmationModal.style.display = 'block';
    }

    // ===============================================================
    // --- API & VERİ YÜKLEME FONKSİYONLARI ---
    // ===============================================================

    async function fetchAPI(url, options = {}) {
        try {
            const response = await fetch(url, options);
            if (response.status === 204) return null; // Silme gibi 'No Content' yanıtları için
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || `HTTP error! Status: ${response.status}`);
            }
            return data;
        } catch (error) {
            console.error('API Hatası:', error);
            showToast(error.message, 'error');
            throw error; // Hatayı tekrar fırlat ki çağıran fonksiyon yakalayabilsin
        }
    }

    async function fetchCurrentTeacher() {
        try {
            const user = await fetchAPI('/auth/users/me');
            if (teacherUsernameSpan) {
                teacherUsernameSpan.textContent = user.username || user.email;
            }
        } catch (error) {
            if (teacherUsernameSpan) teacherUsernameSpan.textContent = 'Hata!';
        }
    }

    async function loadDashboardData() {
        const statTotalStudents = document.getElementById('stat-total-students');
        const statTodayActivity = document.getElementById('stat-today-activity');
        const statAssignedTasks = document.getElementById('stat-assigned-tasks');
        const activitiesTableBody = document.getElementById('recent-activities-table');

        try {
            // İstatistikler
            const stats = await fetchAPI('/teacher/dashboard-stats');
            if (statTotalStudents) statTotalStudents.textContent = stats.total_students ?? '0';
            if (statTodayActivity) statTodayActivity.textContent = stats.today_activity_count ?? '0';
            if (statAssignedTasks) statAssignedTasks.textContent = stats.total_assignments ?? '0';

            // Egzersiz Özetleri
            const summary = await fetchAPI('/teacher/exercise-summary');
            if (activitiesTableBody) {
                activitiesTableBody.innerHTML = '';
                if (!summary || summary.length === 0) {
                    activitiesTableBody.innerHTML = `<tr><td colspan="3">Gösterilecek aktivite bulunamadı.</td></tr>`;
                } else {
                    summary.forEach(item => {
                        const row = document.createElement('tr');
                        // *** DÜZELTME BURADA: item.exercise_type yerine item.exercise_name kullanıldı ***
                        row.innerHTML = `
                            <td>${item.student_name}</td>
                            <td>${item.exercise_name}</td>
                            <td>${item.count}</td>
                        `;
                        activitiesTableBody.appendChild(row);
                    });
                }
            }
        } catch (error) {
            if (activitiesTableBody) activitiesTableBody.innerHTML = `<tr><td colspan="3">Veri yüklenirken bir hata oluştu.</td></tr>`;
        }
    }

    async function loadMyStudentsData() {
        const studentsTableBody = document.getElementById('students-table-body');
        if (!studentsTableBody) return;
        studentsTableBody.innerHTML = spinner;

        try {
            const students = await fetchAPI('/teacher/my-students');
            studentsTableBody.innerHTML = '';
            if (!students || students.length === 0) {
                studentsTableBody.innerHTML = `<tr><td colspan="4">Sisteme kayıtlı öğrenciniz bulunamadı.</td></tr>`;
                return;
            }
            students.forEach(student => {
                const row = document.createElement('tr');
                row.dataset.studentName = student.username.toLowerCase();
                row.innerHTML = `
                    <td>${student.username}</td>
                    <td>${student.email || '-'}</td>
                    <td>${student.last_activity || 'Veri Yok'}</td>
                    <td class="table-actions">
                        <a href="/admin-reports?student_id=${student.id}" class="action-btn view" title="Raporu Görüntüle"><i class="fas fa-chart-pie"></i></a>
                        <button class="action-btn delete" data-id="${student.id}" title="Öğrenciyi Kaldır"><i class="fas fa-trash-alt"></i></button>
                    </td>
                `;
                studentsTableBody.appendChild(row);
                row.querySelector('.delete').addEventListener('click', (e) => openConfirmationModal(e.currentTarget.dataset.id));
            });
        } catch (error) {
            if (studentsTableBody) studentsTableBody.innerHTML = `<tr><td colspan="4">Öğrenciler yüklenemedi.</td></tr>`;
        }
    }

    async function loadReportsData() {
        const studentsReportTableBody = document.getElementById('students-report-table-body');
        if (!studentsReportTableBody) return;

        // Streamlit uygulamanızın çalıştığı adresi buraya yazın.
        // Genellikle varsayılan olarak http://localhost:8501'dir.
        const STREAMLIT_APP_URL = "http://localhost:8501";

        studentsReportTableBody.innerHTML = spinner;

        try {
            const students = await fetchAPI('/teacher/my-students');
            studentsReportTableBody.innerHTML = '';

            if (!students || students.length === 0) {
                studentsReportTableBody.innerHTML = `<tr><td colspan="3">Rapor oluşturulacak öğrenci bulunamadı.</td></tr>`;
                return;
            }

            students.forEach(student => {
                const row = document.createElement('tr');

                // --- İŞTE DEĞİŞİKLİK BURADA ---
                // Eski URL: const reportUrl = `/admin-reports/view?student_id=${student.id}&token=${window.ACCESS_TOKEN}`;
                // YENİ URL: Doğrudan Streamlit uygulamasına yönlendiriyoruz.
                const reportUrl = `${STREAMLIT_APP_URL}/?student_id=${student.id}&token=${window.ACCESS_TOKEN}`;

                row.innerHTML = `
                    <td>${student.id}</td>
                    <td>${student.username}</td>
                    <td>
                        <a href="${reportUrl}" class="btn btn-sm btn-primary" target="_blank">Raporu Görüntüle</a>
                    </td>
                `;

                studentsReportTableBody.appendChild(row);
            });
        } catch (error) {
            if (studentsReportTableBody) {
                studentsReportTableBody.innerHTML = `<tr><td colspan="3">Öğrenciler yüklenemedi. Hata: ${error.message}</td></tr>`;
            }
        }
    }
    // ===============================================================
    // --- EVENT LISTENERS (FORM GÖNDERİMİ, ARAMA vb.) ---
    // ===============================================================

    if (addStudentForm) {
        addStudentForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = addStudentForm.querySelector('button[type="submit"]');
            const codeInput = document.getElementById('student-invitation-code');

            submitBtn.disabled = true;
            submitBtn.textContent = 'Ekleniyor...';

            try {
                const newStudent = await fetchAPI('/teacher/associate-student', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ invitation_code: codeInput.value.trim() })
                });
                showToast(`Öğrenci "${newStudent.username}" başarıyla eklendi!`, 'success');
                addStudentModal.style.display = 'none';
                addStudentForm.reset();
                if (studentsPage) loadMyStudentsData(); // Öğrenci sayfasındaysak listeyi yenile
            } catch (error) {
                // Hata zaten fetchAPI içinde gösteriliyor.
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Onayla ve Ekle';
            }
        });
    }

    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', async () => {
            if (!studentIdToDelete) return;
            confirmDeleteBtn.disabled = true;
            confirmDeleteBtn.textContent = 'Siliniyor...';

            try {
                // Yeni DELETE endpoint'ini çağırıyoruz.
                await fetchAPI(`/teacher/my-students/${studentIdToDelete}`, {
                    method: 'DELETE'
                });
                showToast('Öğrenci başarıyla listeden kaldırıldı.', 'success');
                confirmationModal.style.display = 'none';
                loadMyStudentsData(); // Listeyi yenile
            } catch (error) {
                 // Hata zaten fetchAPI içinde gösteriliyor.
            } finally {
                 confirmDeleteBtn.disabled = false;
                 confirmDeleteBtn.textContent = 'Evet, Sil';
                 studentIdToDelete = null;
            }
        });
    }

    const searchInput = document.getElementById('student-search-input');
    if (searchInput) {
        searchInput.addEventListener('keyup', () => {
            const searchTerm = searchInput.value.toLowerCase().trim();
            document.querySelectorAll('#students-table-body tr').forEach(row => {
                if (row.classList.contains('spinner-row')) return;
                const studentName = row.dataset.studentName || '';
                row.style.display = studentName.includes(searchTerm) ? '' : 'none';
            });
        });
    }

    // ===============================================================
    // --- BAŞLATMA (INITIALIZATION) ---
    // ===============================================================
    fetchCurrentTeacher();

    if (dashboardPage) { loadDashboardData(); }
    if (studentsPage) { loadMyStudentsData(); }
    if (reportsPage) { loadReportsData(); }
});