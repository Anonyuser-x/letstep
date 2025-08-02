document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('reset-password-form');
    const messageDiv = document.getElementById('form-message');
    const passwordInput = document.getElementById('new-password');

    // URL'den token'ı al
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');

    if (!token) {
        messageDiv.textContent = 'Geçersiz veya eksik sıfırlama linki.';
        messageDiv.classList.add('error');
        form.style.display = 'none';
        return;
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        messageDiv.textContent = '';
        messageDiv.className = 'form-message';

        const new_password = passwordInput.value;

        try {
            // URL'e token'ı query parametresi olarak ekliyoruz
            const response = await fetch(`/auth/reset-password?token=${token}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ new_password: new_password })
            });

            const result = await response.json();

            if (response.ok) {
                messageDiv.textContent = 'Şifreniz başarıyla güncellendi! Giriş sayfasına yönlendiriliyorsunuz...';
                messageDiv.classList.add('success');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 3000);
            } else {
                messageDiv.textContent = result.detail || 'Bir hata oluştu.';
                messageDiv.classList.add('error');
            }
        } catch (error) {
            messageDiv.textContent = 'Sunucuya bağlanılamadı.';
            messageDiv.classList.add('error');
        }
    });
});