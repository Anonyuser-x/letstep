const apiBase = "/exercises/kelime-ses-uyum";
let currentQuestionIndex = 0;
let score = 0;
let questions = [];
let startTime;
let exerciseInfo = {};
let userId = null;

// DOM elemanları
const questionText = document.getElementById("question-text");
const imageOptionsGrid = document.getElementById("image-options-grid");
const progressText = document.getElementById("progress-text");
const progressBar = document.getElementById("progress-bar");
const scoreDisplay = document.getElementById("score-display");
const feedbackMessage = document.getElementById("feedback-message");
const resultsScreen = document.getElementById("results-screen");
const exerciseContainer = document.getElementById("exercise-container");
const levelSelection = document.getElementById("level-selection");

// Kullanıcı ID'sini almak için asenkron fonksiyon
async function fetchUserId() {
    try {
        const res = await fetch("/api/get", { method: "GET", credentials: "include" });
        if (!res.ok) throw new Error("User ID alınamadı");
        const data = await res.json();
        return data.user_id;
    } catch (error) {
        console.error("fetchUserId error:", error);
        alert("Kullanıcı bilgisi alınamadı, lütfen tekrar giriş yapınız.");
        return null;
    }
}

// Seviye seçimi butonları
document.getElementById("btn-ilkokul").onclick = async () => {
    localStorage.setItem("level", "ilkokul");
    userId = await fetchUserId();
    if (userId) startExercise("ilkokul");
};

document.getElementById("btn-ortaokul").onclick = async () => {
    localStorage.setItem("level", "ortaokul");
    userId = await fetchUserId();
    if (userId) startExercise("ortaokul");
};

// Egzersizi başlat
function startExercise(level) {
    levelSelection.style.display = "none";
    exerciseContainer.style.display = "block";
    fetchQuestions(level);
}

// Sunucudan soruları çek
async function fetchQuestions(level) {
    try {
        const res = await fetch(`${apiBase}?level=${level}`);
        const data = await res.json();
        if (data.error || !data.questions || data.questions.length === 0) {
            alert("Bu seviye için soru bulunamadı!");
            levelSelection.style.display = "block";
            exerciseContainer.style.display = "none";
            return;
        }

        questions = data.questions;
        exerciseInfo = data.exercise;
        currentQuestionIndex = 0;
        score = 0;
        scoreDisplay.innerHTML = `<i class="fas fa-star"></i> Skor: ${score}`;
        loadQuestion();
    } catch (error) {
        console.error("Soru yüklenirken hata:", error);
        alert(`Hata: ${error.message}. Lütfen sayfayı yenileyin.`);
    }
}

// Mevcut soruyu seviyeye göre ekrana yükle
function loadQuestion() {
    if (currentQuestionIndex >= questions.length) {
        showResults();
        return;
    }

    const current = questions[currentQuestionIndex];
    const level = localStorage.getItem("level");

    questionText.textContent = current.question_text;
    imageOptionsGrid.innerHTML = "";

    const options = [
        current.option_a_image,
        current.option_b_image,
        current.option_c_image
    ].filter(Boolean).sort(() => Math.random() - 0.5);

    imageOptionsGrid.style.gridTemplateColumns = "repeat(3, 1fr)";

    options.forEach(optionValue => {
        const btn = document.createElement("button");
        btn.dataset.answerValue = optionValue;

        if (level === 'ilkokul') {
            btn.classList.add("option-image-button");
            const img = document.createElement("img");
            img.src = optionValue;
            img.alt = "Seçenek";
            btn.appendChild(img);
        } else { // 'ortaokul'
            btn.classList.add("option-text-button");
            btn.textContent = optionValue;
        }

        btn.onclick = () => handleAnswer(optionValue, current);
        imageOptionsGrid.appendChild(btn);
    });

    progressText.textContent = `Soru ${currentQuestionIndex + 1} / ${questions.length}`;
    progressBar.style.width = `${((currentQuestionIndex + 1) / questions.length) * 100}%`;
    startTime = Date.now();
}

// Kullanıcının cevabını işle
async function handleAnswer(selectedValue, question) {
    document.querySelectorAll('.option-image-button, .option-text-button').forEach(b => b.disabled = true);

    const reactionTime = Math.floor((Date.now() - startTime) / 1000);

    const payload = {
        question_id: question.id,
        selected_answer: selectedValue,
        exercise_id: exerciseInfo.id,
        reaction_time: reactionTime,
        level: localStorage.getItem("level"),
        repeat_count: 0
    };

    try {
        const res = await fetch(`${apiBase}/submit?user_id=${encodeURIComponent(userId)}`, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const result = await res.json();

        const allButtons = document.querySelectorAll('.option-image-button, .option-text-button');
        allButtons.forEach(button => {
            if (button.dataset.answerValue === result.correct_answer) {
                button.classList.add('correct');
            }
            if (button.dataset.answerValue === selectedValue && !result.correct) {
                button.classList.add('incorrect');
            }
        });

        if (result.correct) {
            score++;
            feedbackMessage.textContent = "✅ Harika, doğru cevap!";
            feedbackMessage.style.color = "green";
        } else {
            feedbackMessage.textContent = "❌ Doğru değil, ama denemeye devam!";
            feedbackMessage.style.color = "red";
        }

        scoreDisplay.innerHTML = `<i class="fas fa-star"></i> Skor: ${score}`;
        currentQuestionIndex++;

        setTimeout(() => {
            feedbackMessage.textContent = "";
            loadQuestion();
        }, 1500);

    } catch (error) {
        console.error("Cevap gönderilirken hata:", error);
        alert("Cevabınız işlenirken bir hata oluştu. Lütfen tekrar deneyin.");
        document.querySelectorAll('.option-image-button, .option-text-button').forEach(b => b.disabled = false);
    }
}


// ----- YENİ FONKSİYON -----
// Egzersiz tamamlandığında özet verilerini backend'e gönderir.
async function saveExerciseSummary(summaryData) {
    try {
        const res = await fetch(`${apiBase}/complete`, { // apiBase'e göre /complete endpoint'i
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(summaryData)
        });

        if (!res.ok) {
            console.error("Egzersiz özeti sunucuya kaydedilemedi. HTTP Status:", res.status);
        }

        const result = await res.json();
        console.log("Egzersiz özeti kaydetme sonucu:", result.message);

    } catch (error) {
        console.error("saveExerciseSummary fonksiyonunda hata:", error);
    }
}


// ----- GÜNCELLENMİŞ FONKSİYON -----
// Sonuçları gösterir ve egzersiz özetini kaydetmek için ilgili fonksiyonu çağırır.
function showResults() {
    exerciseContainer.style.display = "none";
    resultsScreen.style.display = "flex";
    document.getElementById("final-score-message").textContent = `Skorun: ${score} / ${questions.length}`;

    // --- YENİ EKLENEN KISIM ---
    // Backend'e gönderilecek özet verilerini hazırla
    const totalQuestions = questions.length;
    const correctAnswers = score;
    const wrongAnswers = totalQuestions - correctAnswers;

    const summaryPayload = {
        user_id: userId,
        exercise_id: exerciseInfo.id,
        total_questions: totalQuestions,
        correct_answers: correctAnswers,
        wrong_answers: wrongAnswers
    };

    // Gerekli bilgiler mevcutsa verileri backend'e gönder
    if (userId && exerciseInfo.id) {
        saveExerciseSummary(summaryPayload);
    } else {
        console.warn("Kullanıcı ID veya Egzersiz ID bulunamadığı için özet kaydedilemedi.");
    }
    // --- YENİ EKLENEN KISIM BİTTİ ---
}


// Egzersizi yeniden başlat
document.getElementById("restart-button").addEventListener("click", () => {
    resultsScreen.style.display = "none";
    levelSelection.style.display = "block";
    feedbackMessage.textContent = "";
    scoreDisplay.innerHTML = "";
    // Değişkenleri sıfırla
    currentQuestionIndex = 0;
    score = 0;
    questions = [];
    exerciseInfo = {};
});

// Sayfa yüklendiğinde başlangıç durumunu ayarla
window.onload = () => {
    levelSelection.style.display = "block";
    exerciseContainer.style.display = "none";
    resultsScreen.style.display = "none";
};