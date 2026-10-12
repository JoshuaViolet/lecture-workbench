let lexiconIndex = null;
let termCardPinned = false;
let termHoverTimer = null;
let termHideTimer = null;
let currentTermEntry = null;

function lexiNorm(t) {
    return (t || "").toLowerCase()
        .replace(/[–—]/g, "-")
        .replace(/[“”‘’"']/g, "")
        .replace(/[\u4e00-\u9fff]/g, "")
        .replace(/\s+/g, " ")
        .trim();
}

function buildLexiconIndex() {
    lexiconIndex = {};
    // normalize keys too, so "Broca's Area" matches text rendered with a straight apostrophe
    termLexicon.forEach(e => e.keys.forEach(k => { lexiconIndex[lexiNorm(k)] = e; }));
}

function lookupTerm(rawText) {
    if (!lexiconIndex) return null;
    const candidates = [];
    // candidate 1: full text with parentheticals removed (ASCII and full-width)
    candidates.push(lexiNorm(rawText.replace(/\(.*?\)/g, "").replace(/（.*?）/g, "")));
    // candidate 2..n: each parenthetical's inner content ("腺苷（Adenosine）" -> "adenosine")
    const parens = rawText.match(/[（(]([^）)]*)[）)]/g) || [];
    parens.forEach(p => candidates.push(lexiNorm(p.slice(1, -1))));
    for (let c of candidates) {
        if (!c) continue;
        c = c.replace(/^the\s+/, "").replace(/[,，].*$/, "").trim();
        if (!c) continue;
        if (lexiconIndex[c]) return lexiconIndex[c];
        // try "/" separated segments ("EEG / ERP" -> "eeg")
        for (const seg of c.split("/")) {
            const t2 = seg.trim();
            if (t2 && lexiconIndex[t2]) return lexiconIndex[t2];
        }
    }
    return null;
}

function showTermCard(entry, anchorEl) {
    currentTermEntry = entry;
    const card = document.getElementById("term-card");
    document.getElementById("tc-term").textContent = entry.term;
    document.getElementById("tc-ipa").textContent = entry.ipa;
    document.getElementById("tc-chunks").textContent = entry.chunks;
    document.getElementById("tc-parts").innerHTML = entry.parts;
    document.getElementById("tc-hook").textContent = entry.hook;
    card.style.display = "block";
    const rect = anchorEl.getBoundingClientRect();
    const cardH = card.offsetHeight;
    let top = window.scrollY + rect.bottom + 8;
    // flip above the term when there is no room below
    if (rect.bottom + 8 + cardH > window.innerHeight) {
        top = window.scrollY + rect.top - cardH - 8;
    }
    const left = window.scrollX + rect.left;
    const maxLeft = window.scrollX + document.documentElement.clientWidth - card.offsetWidth - 10;
    card.style.top = Math.max(10, top) + "px";
    card.style.left = Math.min(Math.max(10, left), Math.max(10, maxLeft)) + "px";
}

function hideTermCard() {
    termCardPinned = false;
    const card = document.getElementById("term-card");
    if (card) card.style.display = "none";
}
function scheduleHideTermCard() {
    clearTimeout(termHideTimer);
    termHideTimer = setTimeout(() => { if (!termCardPinned) hideTermCard(); }, 220);
}

function speakCurrentTerm() {
    if (!currentTermEntry) return;
    if (!("speechSynthesis" in window)) { showToast("⚠️ 当前浏览器不支持语音朗读"); return; }
    window.speechSynthesis.cancel();
    const sayText = currentTermEntry.term.split("(")[0].replace(/\//g, " ").trim();
    const u = new SpeechSynthesisUtterance(sayText);
    u.lang = "en-AU";
    u.rate = 0.92;
    window.speechSynthesis.speak(u);
}

function initTermCards() {
    buildLexiconIndex();
    const card = document.getElementById("term-card");
    document.querySelectorAll("#main-content span.en, #main-content strong").forEach(sp => {
        const entry = lookupTerm(sp.textContent);
        if (!entry) return;
        sp.classList.add("lexi");
        sp.addEventListener("mouseenter", () => {
            clearTimeout(termHideTimer);
            clearTimeout(termHoverTimer);
            termHoverTimer = setTimeout(() => { if (!termCardPinned) showTermCard(entry, sp); }, 350);
        });
        sp.addEventListener("mouseleave", () => {
            clearTimeout(termHoverTimer);
            if (!termCardPinned) scheduleHideTermCard();
        });
        sp.addEventListener("click", (e) => {
            e.stopPropagation();
            clearTimeout(termHoverTimer);
            termCardPinned = true;
            showTermCard(entry, sp);
        });
    });
    card.addEventListener("mouseenter", () => clearTimeout(termHideTimer));
    card.addEventListener("mouseleave", () => { if (!termCardPinned) scheduleHideTermCard(); });
    document.getElementById("tc-speak").addEventListener("click", (e) => {
        e.stopPropagation();
        speakCurrentTerm();
    });
}
