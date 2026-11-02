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

// ipa, chunks, parts and hook are optional: a row without a value is hidden, not shown empty
function setTermField(id, value, asHtml) {
    const el = document.getElementById(id);
    if (asHtml) el.innerHTML = value || "";
    else el.textContent = value || "";
    (el.closest(".tc-row") || el).style.display = value ? "" : "none";
}

// keepAbove: room to leave free above the term, where the highlight toolbar shows
function showTermCard(entry, anchorEl, keepAbove) {
    currentTermEntry = entry;
    const card = document.getElementById("term-card");
    document.getElementById("tc-term").textContent = entry.term;
    setTermField("tc-ipa", entry.ipa);
    setTermField("tc-chunks", entry.chunks);
    setTermField("tc-parts", entry.parts, true);
    setTermField("tc-hook", entry.hook);
    card.style.display = "block";
    const rect = anchorEl.getBoundingClientRect();
    const cardH = card.offsetHeight;
    let top = window.scrollY + rect.bottom + 8;
    // flip above the term when there is no room below
    if (rect.bottom + 8 + cardH > window.innerHeight) {
        top = window.scrollY + rect.top - cardH - 8 - (keepAbove || 0);
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
    if (!("speechSynthesis" in window)) { showToast(UI.toast_no_speech); return; }
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(termToSay(currentTermEntry));
    const voice = englishVoice();
    if (voice) u.voice = voice;
    u.lang = voice ? voice.lang : "en-AU";
    u.rate = 0.92;
    window.speechSynthesis.speak(u);
}

// The English words of a term: "Binary search 二分查找" and "Invariant（不变式）" are read as
// "Binary search" and "Invariant", since an English voice cannot read the Chinese.
function termToSay(entry) {
    const english = entry.term.split(/[(（]/)[0]
        .replace(/[\u2e80-\u9fff\uf900-\ufaff\uff00-\uffef]/g, " ")   // CJK and full-width forms
        .replace(/\//g, " ").replace(/\s+/g, " ").trim();
    return english || entry.keys[0];
}

// An installed English voice, Australian first as before, then British, American, any English.
// Without one, a browser falls back to its default voice, which may not speak English at all.
function englishVoice() {
    const voices = window.speechSynthesis.getVoices();
    const lang = v => (v.lang || "").replace("_", "-").toLowerCase();
    for (const want of ["en-au", "en-gb", "en-us"]) {
        const v = voices.find(x => lang(x) === want);
        if (v) return v;
    }
    return voices.find(x => lang(x).startsWith("en")) || null;
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
        // The click also reaches the document's handler, so a reader's own marks inside a term
        // still work: a highlight shows its toolbar above the term as well as the card, and a
        // note's text or 💬 flag opens the note instead of the card.
        sp.addEventListener("click", (e) => {
            clearTimeout(termHoverTimer);
            if (e.target.closest(".note-flag, .note-anchor")) {
                hideTermCard();
                return;
            }
            termCardPinned = true;
            showTermCard(entry, sp, e.target.closest(".user-hl") ? TOOLBAR_ROOM : 0);
        });
    });
    card.addEventListener("mouseenter", () => clearTimeout(termHideTimer));
    card.addEventListener("mouseleave", () => { if (!termCardPinned) scheduleHideTermCard(); });
    document.getElementById("tc-speak").addEventListener("click", (e) => {
        e.stopPropagation();
        speakCurrentTerm();
    });
}
