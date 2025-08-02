// static/js/assistant.js

// Bütün kodun, sayfa tamamen yüklendikten sonra çalışmasını garantilemek için
// DOMContentLoaded olayını dinliyoruz.
document.addEventListener("DOMContentLoaded", () => {

    // --- GEREKLİ DEĞİŞKENLER VE ELEMENT REFERANSLARI ---
    let currentTextId = 1;
    let maxTextId = null;
    let mediaRecorder;
    let audioChunks = [];

    const startButton = document.getElementById("start-btn");
    const stopButton = document.getElementById("stop-btn");
    const sendButton = document.getElementById("send-btn");
    const resetButton = document.getElementById("reset-btn");
    const statusText = document.getElementById("status");
    const resultBox = document.getElementById("result-text");
    const paragraphTextElement = document.getElementById("paragraph-text");
    const prevButton = document.getElementById("prev-text");
    const nextButton = document.getElementById("next-text");

    // --- FONKSİYONLAR ---

    async function fetchParagraph(id) {
        try {
            const response = await fetch(`/reading-text/${id}`);
            if (!response.ok) throw new Error("Metin alınamadı");
            const data = await response.json();

            paragraphTextElement.textContent = data.paragraph;
            currentTextId = data.id;
        } catch (err) {
            console.error("Hata:", err);
            paragraphTextElement.textContent = "Metin yüklenemedi. Lütfen sayfayı yenileyin.";
        }
    }

    async function fetchMaxTextId() {
        try {
            const response = await fetch("/reading-text/max-id");
            if (response.ok) {
                const data = await response.json();
                maxTextId = data.max_id;
            } else {
                console.error("Max ID alınamadı, sunucu yanıtı:", response.status);
            }
        } catch (err) {
            console.warn("Max ID alınamadı, sınır kontrolü yapılamayacak.", err);
        }
    }

    function updateUIState(state) {
        startButton.hidden = true;
        stopButton.hidden = true;
        sendButton.hidden = true;
        resetButton.hidden = true;

        if (state === 'initial') {
            startButton.hidden = false;
            statusText.textContent = "Durum: Başlamak için butona basın.";
        } else if (state === 'recording') {
            stopButton.hidden = false;
            statusText.textContent = "Durum: Kaydediliyor... 🔴";
        } else if (state === 'stopped') {
            sendButton.hidden = false;
            resetButton.hidden = false;
            statusText.textContent = "Durum: Kayıt tamamlandı. Gönderilebilir.";
        } else if (state === 'sending') {
            statusText.textContent = "Durum: Ses gönderiliyor ve işleniyor...";
        }
    }

    // --- OLAY DİNLEYİCİLERİ (EVENT LISTENERS) ---

    prevButton.addEventListener("click", () => {
        if (currentTextId > 1) fetchParagraph(currentTextId - 1);
    });

    nextButton.addEventListener("click", () => {
        if (!maxTextId || currentTextId < maxTextId) fetchParagraph(currentTextId + 1);
    });

    startButton.addEventListener("click", async () => {
        audioChunks = [];
        resultBox.innerHTML = `<p>Okumayı tamamladıktan sonra sonucunuz burada görünecektir.</p>`;
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            mediaRecorder.ondataavailable = event => audioChunks.push(event.data);
            mediaRecorder.onstop = () => updateUIState('stopped');
            mediaRecorder.start();
            updateUIState('recording');
        } catch (err) {
            console.error("Mikrofon hatası:", err);
            statusText.textContent = "Hata: Mikrofon erişimi reddedildi veya bulunamadı.";
            updateUIState('initial');
        }
    });

    stopButton.addEventListener("click", () => {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
        }
    });

    sendButton.addEventListener("click", async () => {
        if (!currentTextId || typeof currentTextId !== 'number' || currentTextId < 1) {
            statusText.textContent = "Hata: Geçerli metin ID'si bulunamadı. Sayfayı yenileyin.";
            console.error("Gönderim iptal edildi. Geçersiz text_id:", currentTextId);
            return;
        }

        updateUIState('sending');
        const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("audio", audioBlob, "recording.webm");
        formData.append("original_text", paragraphTextElement.innerText);
        formData.append("text_id", currentTextId);

        try {
            const response = await fetch("/reading", {
                method: "POST",
                body: formData,
            });
            const data = await response.json();
            if (response.ok) {
                statusText.textContent = "Durum: Analiz Tamamlandı ✅";
                resultBox.innerHTML = `<strong>Okuma Doğruluğu:</strong> %${data.accuracy_percent}<br><hr><strong>Eksik Söylenen Kelimeler (${data.missing_words.length}):</strong><span class="missing-words">${data.missing_words.join(", ") || "Yok"}</span><br><strong>Fazladan Söylenen Kelimeler (${data.extra_words.length}):</strong><span class="extra-words">${data.extra_words.join(", ") || "Yok"}</span><br><hr><strong>Doğru Kelime Sayısı:</strong> ${data.matched_words.length} / ${data.original_word_count}`;
            } else {
                const errorDetail = data.detail && data.detail[0] ? data.detail[0].msg : "Bilinmeyen bir sunucu hatası";
                statusText.textContent = "Hata: " + errorDetail;
                resultBox.innerHTML = `<p>Analiz sırasında bir hata oluştu. Lütfen tekrar deneyin.</p>`;
            }
        } catch (err) {
            console.error("Gönderme Hatası:", err);
            statusText.textContent = "Hata: Sunucuya erişilemedi.";
            resultBox.innerHTML = `<p>Sunucuya bağlanılamadı. İnternet bağlantınızı kontrol edin.</p>`;
        } finally {
            updateUIState('initial');
        }
    });

    resetButton.addEventListener("click", () => {
        audioChunks = [];
        resultBox.innerHTML = `<p>Okumayı tamamladıktan sonra sonucunuz burada görünecektir.</p>`;
        updateUIState('initial');
    });

    // --- SAYFA İLK YÜKLENDİĞİNDE ÇALIŞACAK KOD ---
    async function initializePage() {
        await fetchMaxTextId();
        await fetchParagraph(currentTextId);
    }

    initializePage();
});