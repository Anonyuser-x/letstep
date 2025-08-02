// static/js/auth.js

// DOM yüklendiğinde tüm kodun çalışmasını sağlıyoruz.
document.addEventListener('DOMContentLoaded', () => {

    // Sayfadaki formları ID'lerine göre bulmaya çalışıyoruz.
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    // --- GİRİŞ FORMU MANTIĞI ---
    // Eğer sayfada 'login-form' ID'li bir form varsa, bu kod bloğu çalışır.
    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault();

            const usernameOrEmailInput = document.getElementById('login-username-email');
            const passwordInput = document.getElementById('login-password');
            const errorMessageDiv = document.getElementById('error-message');

            errorMessageDiv.style.display = 'none';
            errorMessageDiv.textContent = '';

            const loginData = {
                username_or_email: usernameOrEmailInput.value,
                password: passwordInput.value
            };

            try {
                const response = await fetch('/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(loginData),
                });

                if (response.ok) {
                    // Giriş başarılı olduğunda backend bir cookie set ettiği için burada
                    // token'ı localStorage'a kaydetmeye gerek kalmayabilir.
                    // Ama yönlendirme yapabiliriz.
                    window.location.href = '/dashboard'; // Başarılı girişte yönlendirilecek sayfa
                } else {
                    const errorData = await response.json();
                    const errorMessage = errorData.detail || 'Giriş yapılamadı. Lütfen bilgilerinizi kontrol edin.';
                    errorMessageDiv.textContent = errorMessage;
                    errorMessageDiv.style.display = 'block';
                }
            } catch (error) {
                console.error('Login Error:', error);
                errorMessageDiv.textContent = 'Bir sunucu hatası oluştu. Lütfen daha sonra tekrar deneyin.';
                errorMessageDiv.style.display = 'block';
            }
        });
    }

    // --- KAYIT FORMU MANTIĞI (Öğrenci ve Öğretmen için birleşik) ---
    // Eğer sayfada 'register-form' ID'li bir form varsa, bu kod bloğu çalışır.
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const messageDiv = document.getElementById('form-message');
            messageDiv.textContent = '';
            messageDiv.className = 'form-message';

            // HTML'deki 'data-role' attribute'ünden rolü alıyoruz (student veya teacher)
            const role = registerForm.dataset.role;
            if (!role) {
                console.error("Formda 'data-role' attribute'ü tanımlanmamış!");
                return;
            }

            // Rol'e göre API endpoint'ini ve başarı mesajını dinamik olarak belirliyoruz.
            const apiUrl = `/auth/register/${role}`;
            const successMessage = (role === 'student' ? 'Öğrenci' : 'Öğretmen') + ' kaydı başarılı! Giriş sayfasına yönlendiriliyorsunuz...';

            // Form verilerini topluyoruz
            const username = document.getElementById('register-username').value;
            const email = document.getElementById('register-email').value;
            const password = document.getElementById('register-password').value;
            const passwordConfirm = document.getElementById('register-password-confirm').value;

            if (password !== passwordConfirm) {
                messageDiv.textContent = 'Şifreler uyuşmuyor. Lütfen kontrol edin.';
                messageDiv.classList.add('error');
                return;
            }

            // Gönderilecek veri objesini hazırlıyoruz.
            const userData = {
                username: username,
                email: email,
                password: password,
            };

            // Eğer rol öğrenci ise, yaş bilgisini de ekliyoruz.
            if (role === 'student') {
                const ageInput = document.getElementById('register-age');
                if (ageInput && ageInput.value) {
                    userData.age = parseInt(ageInput.value, 10);
                }
            }

            try {
                const response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(userData)
                });

                const result = await response.json();

                if (response.ok) {
                    messageDiv.textContent = successMessage;
                    messageDiv.classList.add('success');
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 2000);
                } else {
                    messageDiv.textContent = result.detail || 'Bir hata oluştu. Lütfen tekrar deneyin.';
                    messageDiv.classList.add('error');
                }
            } catch (error) {
                console.error(`${role} kaydı sırasında hata:`, error);
                messageDiv.textContent = 'Sunucuya bağlanılamadı. İnternet bağlantınızı kontrol edin.';
                messageDiv.classList.add('error');
            }
        });
    }
});