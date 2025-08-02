const apiBase = "/exercises/ilk-harfi-yakala";
let currentQuestionIndex = 0;
let score = 0;
let questions = [];
let startTime = Date.now();
let exerciseInfo = {};
let userId = null;

// DOM elemanları
const questionWord = document.getElementById("question-word");
const imageOptionsGrid = document.getElementById("image-options-grid");
const progressText = document.getElementById("progress-text");
const progressBar = document.getElementById("progress-bar");
const scoreDisplay = document.getElementById("score-display");
const feedbackMessage = document.getElementById("feedback-message");
const resultsScreen = document.getElementById("results-screen");
const questionImageContainer = document.getElementById("question-image-container");
const questionImage = document.getElementById("question-image");

// Kullanıcı ID'sini getir
async function fetchUserId() {
    try {
        const res = await fetch("/api/get", {
            method: "GET",
            credentials: "include"
        });
        if (!res.ok) {
            throw new Error("User ID alınamadı");
        }
        const data = await res.json();
        return data.user_id;
    } catch (error) {
        console.error("fetchUserId error:", error);
        alert("Kullanıcı bilgisi alınamadı, lütfen tekrar giriş yapınız.");
        return null;
    }
}

// Seviye seçimi
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
    document.getElementById("level-selection").style.display = "none";
    document.getElementById("exercise-container").style.display = "block";
    fetchQuestions(level);
}

// Soruları backend'den çek
async function fetchQuestions(level) {
    try {
        const res = await fetch(`${apiBase}?level=${level}`);
        const data = await res.json();

        if (data.error || !data.questions || data.questions.length === 0) {
            alert("Bu seviyede soru bulunamadı!");
            document.getElementById("level-selection").style.display = "block";
            document.getElementById("exercise-container").style.display = "none";
            return;
        }

        questions = data.questions;
        exerciseInfo = data.exercise;
        currentQuestionIndex = 0;
        score = 0;
        scoreDisplay.innerHTML = `<i class="fas fa-star"></i> Skor: ${score}`;
        loadQuestion();
    } catch(error) {
        console.error("Sorular getirilirken bir hata oluştu:", error);
        alert("Sorular yüklenirken bir sorun oluştu. Lütfen sayfayı yenileyin.");
    }
}

// Sıradaki soruyu yükle (görsel desteği ile)
function loadQuestion() {
    if (currentQuestionIndex >= questions.length) {
        showResults();
        return;
    }

    const current = questions[currentQuestionIndex];

    // Görsel yükleme mantığı
    if (current.question_image && current.question_image.trim() !== "") {
        questionImage.src = current.question_image;
        questionImageContainer.style.display = "block";
    } else {
        questionImageContainer.style.display = "none";
        questionImage.src = "";
    }

    questionWord.textContent = current.question_text;

    const options = [current.option_a, current.option_b, current.option_c].sort(() => Math.random() - 0.5);
    imageOptionsGrid.innerHTML = "";

    options.forEach(optionText => {
        const btn = document.createElement("button");
        btn.classList.add("option-button");
        btn.textContent = optionText;
        btn.onclick = () => handleAnswer(optionText, current);
        imageOptionsGrid.appendChild(btn);
    });

    progressText.textContent = `Soru ${currentQuestionIndex + 1} / ${questions.length}`;
    progressBar.style.width = `${((currentQuestionIndex + 1) / questions.length) * 100}%`;
    startTime = Date.now(); // Her yeni soru için zamanlayıcıyı başlat
}

// Cevabı işle
async function handleAnswer(selectedAnswer, question) {
    if (!userId) {
        alert("Kullanıcı bilgisi bulunamadı. Lütfen sayfayı yenileyip tekrar giriş yapınız.");
        return;
    }

    const reactionTime = Math.floor((Date.now() - startTime) / 1000);

    const payload = {
        question_id: question.id,
        selected_answer: selectedAnswer.trim().toLowerCase(),
        exercise_id: exerciseInfo.id,
        reaction_time: reactionTime,
        repeat_count: 0,
        level: localStorage.getItem("level") || "ilkokul"
    };

    const res = await fetch(`${apiBase}/submit?user_id=${encodeURIComponent(userId)}`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    const result = await res.json();

    if (result.correct) {
        score++;
        feedbackMessage.textContent = "✅ Doğru cevap!";
        feedbackMessage.style.color = "green";
    } else {
        feedbackMessage.textContent = `❌ Yanlış cevap! Doğru: ${result.correct_answer}`;
        feedbackMessage.style.color = "red";
    }

    scoreDisplay.innerHTML = `<i class="fas fa-star"></i> Skor: ${score}`;
    currentQuestionIndex++;

    setTimeout(() => {
        feedbackMessage.textContent = "";
        loadQuestion();
    }, 1200);
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
    document.getElementById("exercise-container").style.display = "none";
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


// Yeniden başlat butonu
document.getElementById("restart-button").addEventListener("click", () => {
    document.getElementById("results-screen").style.display = "none";
    document.getElementById("level-selection").style.display = "block";

    currentQuestionIndex = 0;
    score = 0;
    questions = [];
    exerciseInfo = {};
    feedbackMessage.textContent = "";
    scoreDisplay.innerHTML = "";
});


// Sayfa yüklendiğindeki başlangıç durumu
window.onload = () => {
    document.getElementById("level-selection").style.display = "block";
    document.getElementById("exercise-container").style.display = "none";
    document.getElementById("results-screen").style.display = "none";
};