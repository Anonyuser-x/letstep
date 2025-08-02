document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('forgot-password-form');
    const messageDiv = document.getElementById('form-message');
    const emailInput = document.getElementById('email');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        messageDiv.textContent = '';
        messageDiv.className = 'form-message';

        const email = emailInput.value;

        try {
            const response = await fetch('/auth/forgot-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: email })
            });

            const result = await response.json();

            if (response.ok) {
                messageDiv.textContent = result.message;
                messageDiv.classList.add('success');
                form.reset();
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