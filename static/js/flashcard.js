document.addEventListener('DOMContentLoaded', async () => {
    // --- STATE MANAGEMENT ---
    let flashcards = []; // Veriler API'den gelecek
    let currentCard = 0;
    let isFlipped = false;
    let showStats = false;
    let correctCount = 0;
    let totalReviewed = 0;

    // --- DOM ELEMENT REFERENCES ---
    // (DOM referansları aynı kalıyor, değişiklik yok)
    const appContainer = document.getElementById('app-container');
    const statsContainer = document.getElementById('stats-container');
    const showStatsBtn = document.getElementById('show-stats-btn');
    const progressText = document.getElementById('progress-text');
    const accuracyText = document.getElementById('accuracy-text');
    const progressBar = document.getElementById('progress-bar');
    const cardContainer = document.getElementById('card-container');
    const cardFront = document.getElementById('card-front');
    const cardBack = document.getElementById('card-back');
    const frontDifficultyBadge = document.getElementById('front-difficulty-badge');
    const errorTypeBadge = document.getElementById('error-type-badge');
    const similarityScore = document.getElementById('similarity-score');
    const userPronunciationEl = document.getElementById('user-pronunciation');
    const backDifficultyBadge = document.getElementById('back-difficulty-badge');
    const wordTypeBadge = document.getElementById('word-type-badge');
    const correctWordEl = document.getElementById('correct-word');
    const wordDescriptionEl = document.getElementById('word-description');
    const playAudioBtn = document.getElementById('play-audio-btn');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const markButtonsContainer = document.getElementById('mark-buttons-container');
    const markIncorrectBtn = document.getElementById('mark-incorrect-btn');
    const markCorrectBtn = document.getElementById('mark-correct-btn');
    const statsAccuracy = document.getElementById('stats-accuracy');
    const statsReviewed = document.getElementById('stats-reviewed');
    const difficultyDistribution = document.getElementById('difficulty-distribution');
    const continueStudyingBtn = document.getElementById('continue-studying-btn');
    const resetProgressBtn = document.getElementById('reset-progress-btn');


    // --- YENİ: API İLETİŞİMİ ---
    const fetchFlashcards = async () => {
        try {
            const response = await fetch('/flashcards/');
            if (!response.ok) {
                throw new Error('Veriler alınamadı.');
            }
            const data = await response.json();
            flashcards = data;
        } catch (error) {
            console.error("API Hatası:", error);
            // Hata durumunda kullanıcıya bilgi verilebilir
            appContainer.innerHTML = `<div class="text-center p-10"><h2 class="text-2xl font-bold text-red-600">Bir hata oluştu.</h2><p class="text-gray-600">Lütfen daha sonra tekrar deneyin.</p></div>`;
        }
    };

    // --- LOGIC & HELPER FUNCTIONS ---
    // (Levenshtein ve calculateDifficulty fonksiyonları backend'e taşındığı için kaldırılabilir
    // ancak frontend'de anlık hesaplama istenirse kalabilir. Şimdilik bırakıyorum.)

    // --- STYLING HELPERS ---
    const getDifficultyColor = (level) => ({ 'easy': 'bg-gradient-to-r from-green-400 to-green-600', 'medium': 'bg-gradient-to-r from-yellow-400 to-orange-500', 'hard': 'bg-gradient-to-r from-red-400 to-red-600', 'very_hard': 'bg-gradient-to-r from-purple-500 to-red-600' }[level] || 'bg-gradient-to-r from-blue-400 to-blue-600');
    const getDifficultyBg = (level) => ({ 'easy': 'bg-gradient-to-br from-green-50 to-green-100 border-green-300', 'medium': 'bg-gradient-to-br from-yellow-50 to-orange-100 border-orange-300', 'hard': 'bg-gradient-to-br from-red-50 to-red-100 border-red-300', 'very_hard': 'bg-gradient-to-br from-purple-50 to-red-100 border-purple-400' }[level] || 'bg-gradient-to-br from-blue-50 to-blue-100 border-blue-300');
    const getDifficultyText = (level) => ({ 'easy': 'Kolay', 'medium': 'Orta', 'hard': 'Zor', 'very_hard': 'Çok Zor' }[level] || 'Bilinmiyor');


    // --- EVENT HANDLERS & ACTIONS ---
    const nextCard = () => {
        if (currentCard < flashcards.length - 1) {
            currentCard++;
            isFlipped = false;
            renderApp();
        }
    };

    const prevCard = () => {
        if (currentCard > 0) {
            currentCard--;
            isFlipped = false;
            renderApp();
        }
    };

    const flipCard = () => {
        isFlipped = !isFlipped;
        renderApp();
    };

    const markCorrect = async () => {
        const uniqueCardId = flashcards[currentCard].id;

        try {
            const response = await fetch(`/flashcards/${uniqueCardId}/resolve`, {
                method: 'POST',
                // HttpOnly cookie kullanılıyorsa, Authorization header'ına gerek YOKTUR.
                // Tarayıcı bunu otomatik halleder.
                headers: {
                    // Header'ı boş bırakabilir veya sadece Content-Type ekleyebilirsiniz.
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Kart güncellenemedi.');
            }

            flashcards.splice(currentCard, 1);
            if (currentCard >= flashcards.length) {
                currentCard = Math.max(0, flashcards.length - 1);
            }
            isFlipped = false;
            renderApp();

        } catch (error) {
            console.error('Hata:', error);
            alert(`Bir sorun oluştu: ${error.message}`);
        }
    };

    const markIncorrect = () => {
        totalReviewed++;
        nextCard();
    };

    const resetProgress = async () => {
        // Bu fonksiyon artık ilerlemeyi sıfırlamak yerine verileri yeniden yüklemeli
        // Veya bir "reset" endpoint'i çağrılabilir. Şimdilik sayfayı yenilemek en kolayı.
        window.location.reload();
    };

    const playAudio = (text) => {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'tr-TR';
            utterance.rate = 0.8;
            speechSynthesis.speak(utterance);
        } else {
            alert('Tarayıcınız ses sentezleme özelliğini desteklemiyor.');
        }
    };

    // --- RENDER FUNCTIONS ---
    const renderStats = () => {
        // Bu fonksiyon şimdilik aynı kalabilir, ancak `totalReviewed` ve `flashcards.length`
        // başlangıçtaki toplam kart sayısına göre hesaplanmalı.
        // Bu daha karmaşık bir state yönetimi gerektirir, şimdilik basit bırakıyorum.
        const accuracy = totalReviewed > 0 ? Math.round((correctCount / totalReviewed) * 100) : 0;
        statsAccuracy.textContent = `${accuracy}%`;
        statsReviewed.textContent = `${totalReviewed}/${totalReviewed + flashcards.length}`; // Basit bir tahmin
        // ... (geri kalan renderStats kodu aynı)
    };

    const renderApp = () => {
        if (showStats) {
            appContainer.classList.add('hidden');
            statsContainer.classList.remove('hidden');
            renderStats();
            return;
        }

        appContainer.classList.remove('hidden');
        statsContainer.classList.add('hidden');

        // YENİ: Kart kalmadıysa mesaj göster
        if (flashcards.length === 0) {
            appContainer.innerHTML = `
                <div class="text-center p-10 max-w-2xl mx-auto bg-white rounded-3xl shadow-2xl">
                    <h2 class="text-4xl font-bold text-green-600 mb-4">🎉 Harikasınız! 🎉</h2>
                    <p class="text-gray-700 text-xl">Yanlış okuduğunuz hiç kelime kalmadı. Çok iyi gidiyorsunuz!</p>
                </div>
            `;
            return;
        }


        const currentFlashcard = flashcards[currentCard];
        const accuracy = totalReviewed > 0 ? Math.round((correctCount / totalReviewed) * 100) : 0;

        progressText.textContent = `Kart ${currentCard + 1} / ${flashcards.length}`;
        accuracyText.textContent = `Başarı: ${accuracy}%`;
        progressBar.style.width = `${((currentCard + 1) / flashcards.length) * 100}%`;

        const difficulty = currentFlashcard.difficulty_level;

        cardFront.className = `card-front absolute inset-0 w-full h-full rounded-3xl border-2 backface-hidden ${getDifficultyBg(difficulty)}`;
        cardBack.className = `card-back absolute inset-0 w-full h-full rounded-3xl border-2 backface-hidden ${getDifficultyBg(difficulty)}`;

        frontDifficultyBadge.className = `px-4 py-2 rounded-full text-white text-sm font-bold shadow-lg ${getDifficultyColor(difficulty)}`;
        frontDifficultyBadge.textContent = getDifficultyText(difficulty);
        errorTypeBadge.textContent = currentFlashcard.error_type;
        similarityScore.textContent = `${currentFlashcard.similarity_score}%`; // API'den gelen veri
        userPronunciationEl.textContent = currentFlashcard.user_pronunciation;

        backDifficultyBadge.className = `px-4 py-2 rounded-full text-white text-sm font-bold shadow-lg ${getDifficultyColor(difficulty)}`;
        backDifficultyBadge.textContent = getDifficultyText(difficulty);
        wordTypeBadge.textContent = currentFlashcard.word_type.replace('_', ' ');
        correctWordEl.textContent = currentFlashcard.correct_word;
        wordDescriptionEl.textContent = currentFlashcard.description;

        if (isFlipped) {
            cardContainer.classList.add('flipped');
            markButtonsContainer.classList.remove('hidden');
        } else {
            cardContainer.classList.remove('flipped');
            markButtonsContainer.classList.add('hidden');
        }

        prevBtn.disabled = currentCard === 0;
        nextBtn.disabled = currentCard === flashcards.length - 1;
    };


    // --- EVENT LISTENERS ---
    // (Aynı kalıyorlar, değişiklik yok)
    cardContainer.addEventListener('click', flipCard);
    prevBtn.addEventListener('click', prevCard);
    nextBtn.addEventListener('click', nextCard);
    markCorrectBtn.addEventListener('click', markCorrect);
    markIncorrectBtn.addEventListener('click', markIncorrect);
    playAudioBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        playAudio(flashcards[currentCard].correct_word);
    });
    showStatsBtn.addEventListener('click', () => { showStats = true; renderApp(); });
    continueStudyingBtn.addEventListener('click', () => { showStats = false; renderApp(); });
    resetProgressBtn.addEventListener('click', resetProgress);


    // --- INITIALIZATION ---
    lucide.createIcons();
    await fetchFlashcards(); // YENİ: Başlangıçta verileri API'den çek
    renderApp(); // Initial render
});