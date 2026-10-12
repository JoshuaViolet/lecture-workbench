let curFC = 0;
let fcFlipped = false;

function updateFC() {
    if (!flashcards.length) return;
    const typeEl = document.getElementById("fc-type");
    if (!typeEl) return;
    const card = flashcards[curFC];
    const fcTag = fcFlipped ? UI.fc_tag_back : UI.fc_tag_front;
    document.getElementById("fc-type").textContent = (card.type ? card.type + " · " : "") + fcTag + UI.fc_flip_hint;
    document.getElementById("fc-front").textContent = fcFlipped ? card.back : card.front;
    document.getElementById("fc-sub").textContent = fcFlipped ? UI.fc_sub_back : UI.fc_sub_front;
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
