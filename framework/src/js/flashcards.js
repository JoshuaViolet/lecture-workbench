let curFC = 0;
let fcFlipped = false;

function updateFC() {
    if (!flashcards.length) return;
    const typeEl = document.getElementById("fc-type");
    if (!typeEl) return;
    const card = flashcards[curFC];
    const fcTag = fcFlipped ? "MECHANISM & ANSWER" : "CONCEPT PROMPT";
    document.getElementById("fc-type").textContent = (card.type ? card.type + " · " : "") + fcTag + " (点击翻转)";
    document.getElementById("fc-front").textContent = fcFlipped ? card.back : card.front;
    document.getElementById("fc-sub").textContent = fcFlipped ? "点击返回概念名称 ↺" : "点击翻面查看机制与考点 ➔";
    document.getElementById("fc-counter").textContent = (curFC + 1) + " / " + flashcards.length;
}

function flipCard() {
    fcFlipped = !fcFlipped;
    updateFC();
}

function nextCard() {
    fcFlipped = false;
    curFC = (curFC + 1) % flashcards.length;
    updateFC();
}

function prevCard() {
    fcFlipped = false;
    curFC = (curFC - 1 + flashcards.length) % flashcards.length;
    updateFC();
}

function shuffleCards() {
    fcFlipped = false;
    curFC = Math.floor(Math.random() * flashcards.length);
    updateFC();
}
