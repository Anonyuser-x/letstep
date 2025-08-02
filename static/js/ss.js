document.addEventListener('DOMContentLoaded', () => {
    // === HTML ELEMANLARINI SEÇME ===
    // Formlar
    const formUsername = document.getElementById('form-update-username');
    const formEmail = document.getElementById('form-update-email');
    const formPassword = document.getElementById('form-update-password');

    // Bilgi Görüntüleme Alanları
    const displayUsername = document.getElementById('current-username-display');
    const displayEmail = document.getElementById('current-email-display');
    const inputInvitationCode = document.getElementById('invitation-code');

    // Butonlar ve Bildirim Alanı
    const btnRegenerateCode = document.getElementById('regenerate-code-btn');
    const btnCopyCode = document.getElementById('copy-code-btn');
    const notificationArea = document.getElementById('toast-notification-area');

    // --- 1. MODERN BİLDİRİM GÖSTERME FONKSİYONU ---
    // Sadece bu fonksiyon kullanılacak. Eski 'showMessage' tamamen silindi.
    function showToast(text, type = 'success') {
        if (!notificationArea) {
            console.error('KRİTİK HATA: HTML içinde id="toast-notification-area" olan div bulunamadı!');
            return;
        }

        const iconClass = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
        const toastId = 'toast-' + Date.now();
        const toastHTML = `
            <div id="${toastId}" class="toast-notification ${type}">
                <i class="icon ${iconClass}"></i>
                <span class="message">${text}</span>
            </div>
        `;
        notificationArea.insertAdjacentHTML('beforeend', toastHTML);
        const toastElement = document.getElementById(toastId);

        setTimeout(() => toastElement.classList.add('show'), 10);
        setTimeout(() => {
            toastElement.classList.remove('show');
            setTimeout(() => toastElement.remove(), 500);
        }, 4000);
    }

    // --- 2. SAYFA YÜKLENDİĞİNDE VERİLERİ API'DEN ÇEKME ---
    // Bu fonksiyon, diğer tüm fonksiyonlardan önce çalışır ve bilgileri doldurur.
    async function loadInitialData() {
        try {
            // Not: Bu endpoint'in kullanıcı bilgilerini döndürdüğü varsayılıyor.
            // Genellikle /auth/users/me veya benzeri bir endpoint olur.
            const response = await fetch('/auth/users/me');

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: `Sunucu hatası: ${response.status}` }));
                throw new Error(errorData.detail);
            }
            const user = await response.json();

            // API'den gelen verilerle arayüzü güncelle
            displayUsername.textContent = user.username || 'Belirtilmemiş';
            displayEmail.textContent = user.email || 'Belirtilmemiş';
            inputInvitationCode.value = user.invitation_code || 'Kod alınamadı';

        } catch (error) {
            // Hata durumunda, doğru 'showToast' fonksiyonu ile kullanıcıyı bilgilendir.
            showToast(`Bilgiler yüklenemedi: ${error.message}`, 'error');
            displayUsername.textContent = 'Yüklenemedi';
            displayEmail.textContent = 'Yüklenemedi';
            inputInvitationCode.value = 'HATA!';
        }
    }

    // --- 3. API İSTEKLERİNİ YÖNETEN YARDIMCI FONKSİYON ---
    async function handleApiRequest(url, method, payload, successMessage, formElement) {
        try {
            const options = {
                method: method,
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
            };
            if (method !== 'GET' && payload) {
                options.body = JSON.stringify(payload);
            }

            const response = await fetch(url, options);
            const result = await response.json();

            if (!response.ok) {
                // FastAPI'den gelen standart 'detail' hata mesajını kullan
                throw new Error(result.detail || 'Bilinmeyen bir sunucu hatası oluştu.');
            }

            showToast(successMessage, 'success');
            if (formElement) formElement.reset();
            return result;

        } catch (error) {
            showToast(error.message, 'error');
            return null;
        }
    }

    // --- 4. EVENT LISTENERS (OLAY DİNLEYİCİLERİ) ---

    // Kullanıcı Adı Güncelleme Formu
    formUsername.addEventListener('submit', async (e) => {
        e.preventDefault();
        const newUsername = document.getElementById('new-username').value;
        const result = await handleApiRequest(
            '/api/user/username',
            'PUT',
            { new_username: newUsername },
            'Kullanıcı adınız başarıyla güncellendi.',
            formUsername
        );
        if (result && result.username) {
            displayUsername.textContent = result.username;
        }
    });

    // E-posta Güncelleme Formu
    formEmail.addEventListener('submit', async (e) => {
        e.preventDefault();
        const newEmail = document.getElementById('new-email').value;
        const result = await handleApiRequest(
            '/api/user/email',
            'PUT',
            { new_email: newEmail },
            'E-posta adresiniz başarıyla güncellendi.',
            formEmail
        );
        if (result && result.email) {
            displayEmail.textContent = result.email;
        }
    });

    // Şifre Güncelleme Formu
    formPassword.addEventListener('submit', async (e) => {
        e.preventDefault();
        const currentPassword = document.getElementById('current-password').value;
        const newPassword = document.getElementById('new-password').value;
        // Bu endpoint router'a göre özel bir mesaj döndürüyor, biz de onu alıp gösterebiliriz.
        const result = await handleApiRequest(
            '/api/user/password',
            'PUT',
            { current_password: currentPassword, new_password: newPassword },
            "İşlem başarılı.", // API kendi mesajını döndürdüğü için genel bir mesaj veriyoruz.
            formPassword
        );
        // API'den gelen mesajı ayrıca göstermek isterseniz:
        // if(result && result.message) { showToast(result.message, 'success'); }
    });

    // Davet Kodu Yenileme Butonu
    btnRegenerateCode.addEventListener('click', async () => {
        const result = await handleApiRequest(
            '/api/user/invitation-code/regenerate',
            'POST',
            {}, // Body boş
            'Yeni davet kodu oluşturuldu.'
        );
        if (result && result.invitation_code) {
            inputInvitationCode.value = result.invitation_code;
        }
    });

    // Kopyala Butonu
    btnCopyCode.addEventListener('click', () => {
        const codeToCopy = inputInvitationCode.value;
        if (!codeToCopy || codeToCopy.includes('HATA')) {
            showToast('Kopyalanacak geçerli bir kod yok.', 'error');
            return;
        }
        navigator.clipboard.writeText(codeToCopy).then(() => {
            showToast('Davet kodu panoya kopyalandı!', 'success');
        }).catch(err => {
            showToast('Kod otomatik kopyalanamadı.', 'error');
        });
    });

    // --- 5. İLK ÇAĞRI ---
    // Sayfa yüklendiğinde tüm süreci başlat.
    loadInitialData();
});