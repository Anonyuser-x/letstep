const apiBase = "/exercises/kod-kirici";
let currentQuestionIndex = 0;
let score = 0;
let questions = [];
let startTime = Date.now();
let exerciseInfo = {};
let userId = null;

// DOM ELEMANLARI
const questionWord = document.getElementById("question-word");
const progressText = document.getElementById("progress-text");
const progressBar = document.getElementById("progress-bar");
const scoreDisplay = document.getElementById("score-display");
const feedbackMessage = document.getElementById("feedback-message");
const resultsScreen = document.getElementById("results-screen");
const answerForm = document.getElementById("answer-form");
const answerInput = document.getElementById("answer-input");
const submitButton = document.getElementById("submit-answer-btn");

// Kullanıcı ID'sini backend'den cookie içindeki token ile çek
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

// Butonlara tıklama eventi: Seçilen seviyeyi al, sakla ve soruları getir
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

// Egzersizi başlat, seçilen seviyeye göre soruları getir
function startExercise(level) {
    document.getElementById("level-selection").style.display = "none";
    document.getElementById("exercise-container").style.display = "block";
    fetchQuestions(level);
}

// Soruları seçilen seviyeye göre getir
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
        alert("Sorular yüklenirken bir hata oluştu, lütfen sayfayı yenileyin.");
    }
}

// Sadece soruyu ve input alanını hazırlar
function loadQuestion() {
    if (currentQuestionIndex >= questions.length) {
        showResults();
        return;
    }

    const current = questions[currentQuestionIndex];
    questionWord.textContent = current.question_text;

    // Input alanını temizle, odakla ve butonu aktif et
    answerInput.value = "";
    answerInput.focus();
    submitButton.disabled = false;

    progressText.textContent = `Soru ${currentQuestionIndex + 1} / ${questions.length}`;
    progressBar.style.width = `${((currentQuestionIndex + 1) / questions.length) * 100}%`;
    startTime = Date.now(); // Zamanlayıcıyı her soru için yeniden başlat
}

// Form gönderimini dinleyen event listener
answerForm.addEventListener("submit", function(event) {
    event.preventDefault(); // Formun sayfayı yenilemesini engelle
    const userAnswer = answerInput.value;
    if (userAnswer.trim() === "") return; // Boş cevabı gönderme

    const currentQuestion = questions[currentQuestionIndex];
    handleAnswer(userAnswer, currentQuestion);
});

// Formdan gelen cevabı işler
async function handleAnswer(selectedAnswer, question) {
    if (!userId) {
        alert("Kullanıcı bilgisi bulunamadı. Lütfen sayfayı yenileyip tekrar giriş yapınız.");
        return;
    }

    // Cevap gönderilirken butonu devre dışı bırak
    submitButton.disabled = true;

    const reactionTime = Math.floor((Date.now() - startTime) / 1000);

    const payload = {
        question_id: question.id,
        selected_answer: selectedAnswer.trim(),
        exercise_id: exerciseInfo.id,
        reaction_time: reactionTime,
        repeat_count: 0,
        level: localStorage.getItem("level") || "ilkokul"
    };

    const res = await fetch(`${apiBase}/submit?user_id=${encodeURIComponent(userId)}`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const result = await res.json();

    if (result.correct) {
        score++;
        feedbackMessage.textContent = "✅ Doğru cevap!";
        feedbackMessage.style.color = "green";
    } else {
        feedbackMessage.textContent = `❌ Yanlış! Doğru cevap: ${result.correct_answer}`;
        feedbackMessage.style.color = "red";
    }

    scoreDisplay.innerHTML = `<i class="fas fa-star"></i> Skor: ${score}`;
    currentQuestionIndex++;

    setTimeout(() => {
        feedbackMessage.textContent = "";
        loadQuestion();
    }, 1500);
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


// Yeniden başlat
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

// Sayfa yüklendiğinde sadece seviye seçim görünür
window.onload = () => {
    document.getElementById("level-selection").style.display = "block";
    document.getElementById("exercise-container").style.display = "none";
    document.getElementById("results-screen").style.display = "none";
};