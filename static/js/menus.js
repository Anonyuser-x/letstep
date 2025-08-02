document.addEventListener('DOMContentLoaded', () => {
    const userMenuButton = document.getElementById('user-menu-button');
    const userMenuDropdown = document.getElementById('user-menu-dropdown');
    const userMenuUsername = document.getElementById('user-menu-username');
    const userMenuContainer = document.querySelector('.user-menu-container');
    const ctaButtons = document.querySelector('.cta-buttons');

    async function setupUserMenu() {
        try {
            const response = await fetch('/auth/users/me', {
                headers: {
                    'Accept': 'application/json'
                }
            });

            if (response.ok) {
                const user = await response.json();
                userMenuUsername.textContent = user.username;
                userMenuContainer.style.display = 'flex';
                if (ctaButtons) ctaButtons.style.display = 'none';
            } else if (response.status === 401) {
                // Giriş yapılmamışsa
                userMenuContainer.style.display = 'none';
                if (ctaButtons) ctaButtons.style.display = 'flex';
            }
        } catch (error) {
            console.error('Kullanıcı bilgisi alınamadı:', error);
        }
    }

    if (userMenuButton && userMenuDropdown) {
        setupUserMenu();

        userMenuButton.addEventListener('click', (e) => {
            e.stopPropagation();
            userMenuDropdown.classList.toggle('show');
        });

        document.addEventListener('click', (e) => {
            if (!userMenuContainer.contains(e.target)) {
                userMenuDropdown.classList.remove('show');
            }
        });
    }
});
