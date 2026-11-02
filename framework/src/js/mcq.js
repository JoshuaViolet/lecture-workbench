let userScore = 0;
let answeredQuestions = new Set();
let mcqOnlyWrong = false;    // practising only the questions answered wrongly last time
let mcqWrongSet = [];        // their keys, fixed when that mode was turned on

// ---------- remembered results ----------
// Each question's last result is kept in this browser, keyed by its stem, code and figure, so
// adding or reordering questions keeps the records and editing a stem starts that question afresh.
function mcqKey(item) {
    const s = item.q + "\u0000" + (item.code || "") + (item.fig ? "\u0000" + item.fig : "");
    let h = 0x811c9dc5;   // FNV-1a
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193); }
    return "q" + (h >>> 0).toString(36);
}
function mcqResults() {
    try {
        const v = JSON.parse(lsGet(LS.mcq) || "{}");
        return v && typeof v === "object" && !Array.isArray(v) ? v : {};
    } catch (e) { return {}; }
}
function recordMcqResult(item, ok) {
    const results = mcqResults();
    results[mcqKey(item)] = { ok: ok, ts: Date.now() };
    lsSet(LS.mcq, JSON.stringify(results));   // a convenience: if storage is unavailable, practice goes on
}
function wrongLastTime() {
    const results = mcqResults();
    return mcqData.map(mcqKey).filter(k => results[k] && results[k].ok === false);
}

function mcqToolbar() {
    const wrong = wrongLastTime();
    const bar = document.createElement("div");
    bar.className = "mcq-toolbar";
    if (!mcqOnlyWrong && !wrong.length) return bar;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.id = "mcq-only-wrong";
    btn.className = "fc-btn fc-btn-sec";
    btn.setAttribute("aria-pressed", String(mcqOnlyWrong));
    btn.textContent = mcqOnlyWrong ? t("mcq_show_all", { n: mcqData.length }) : t("mcq_only_wrong", { n: wrong.length });
    btn.onclick = toggleWrongOnly;
    bar.appendChild(btn);
    return bar;
}
function refreshMcqToolbar() {
    const old = document.querySelector("#mcq-app > .mcq-toolbar");
    if (old) old.replaceWith(mcqToolbar());
}
function toggleWrongOnly() {
    mcqOnlyWrong = !mcqOnlyWrong;
    mcqWrongSet = mcqOnlyWrong ? wrongLastTime() : [];
    resetMCQ();
}

// Options are shuffled on every render, so neither the authored position of the
// answer nor any habit of the author (e.g. "it's usually B") can be learned
// instead of the material. A question can opt out with "shuffle": false.
function optionOrder(item) {
    const order = item.opts.map((_, i) => i);
    if (item.shuffle === false) return order;
    for (let i = order.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [order[i], order[j]] = [order[j], order[i]];
    }
    return order;
}

function initMCQ() {
    const container = document.getElementById("mcq-app");
    if (!container) return;   // practice widgets are optional
    container.innerHTML = "";
    container.appendChild(mcqToolbar());
    const results = mcqResults();
    mcqData.forEach((item, qIdx) => {
        const key = mcqKey(item);
        if (mcqOnlyWrong && !mcqWrongSet.includes(key)) return;
        const card = document.createElement("div");
        card.className = "mcq-card";
        card.id = `mcq-card-${qIdx}`;

        if (results[key] && results[key].ok === false) {
            const badge = document.createElement("div");
            badge.className = "mcq-badge";
            badge.textContent = UI.mcq_last_wrong;
            card.appendChild(badge);
        }

        const qTitle = document.createElement("div");
        qTitle.className = "mcq-q";
        qTitle.textContent = item.q;
        card.appendChild(qTitle);

        // optional figure the question is about (a diagram to read); click or Enter shows it full size
        if (item.fig) card.appendChild(mcqFigure(item));

        // optional code the question is about, shown as written (whitespace kept)
        if (item.code) {
            const pre = document.createElement("pre");
            pre.className = "mcq-code";
            const code = document.createElement("code");
            code.textContent = item.code;
            pre.appendChild(code);
            card.appendChild(pre);
        }

        const optsDiv = document.createElement("div");
        optsDiv.className = "mcq-options";

        optionOrder(item).forEach(oIdx => {
            const opt = item.opts[oIdx];
            const optBtn = document.createElement("button");
            optBtn.className = "mcq-opt" + (opt.includes("\n") ? " is-code" : "");   // a multi-line option is code
            optBtn.textContent = opt;
            optBtn.dataset.opt = oIdx;   // index in the authored order
            optBtn.onclick = () => selectOption(qIdx, oIdx, optBtn);
            optsDiv.appendChild(optBtn);
        });

        card.appendChild(optsDiv);

        const expDiv = document.createElement("div");
        expDiv.className = "mcq-explain";
        expDiv.id = `mcq-exp-${qIdx}`;
        expDiv.innerHTML = `<strong>${escapeHtml(UI.mcq_explain)}</strong>: ${item.exp}`;
        card.appendChild(expDiv);

        container.appendChild(card);
    });
}

function mcqFigure(item) {
    const fig = document.createElement("figure");
    fig.className = "mcq-fig";
    const img = document.createElement("img");
    img.src = item.fig;
    img.alt = item.fig_alt || "";
    // questions are redrawn on every reset, so their figures get keyboard access here
    img.tabIndex = 0;
    img.addEventListener("keydown", e => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); img.click(); }
    });
    fig.appendChild(img);
    return fig;
}

function selectOption(qIdx, selectedIdx, btn) {
    const correctIdx = mcqData[qIdx].ans;
    if (answeredQuestions.has(qIdx)) return;
    answeredQuestions.add(qIdx);

    const card = document.getElementById(`mcq-card-${qIdx}`);
    const allOpts = card.querySelectorAll(".mcq-opt");
    allOpts.forEach(b => b.classList.add("locked"));

    if (selectedIdx === correctIdx) {
        btn.classList.add("correct");
        userScore++;
    } else {
        btn.classList.add("incorrect");
        card.querySelector(`.mcq-opt[data-opt="${correctIdx}"]`).classList.add("correct");
    }
    recordMcqResult(mcqData[qIdx], selectedIdx === correctIdx);
    refreshMcqToolbar();

    setText("mcq-score", userScore);
    setText("mcq-done", answeredQuestions.size);
    document.getElementById(`mcq-exp-${qIdx}`).style.display = "block";
}

function resetMCQ() {
    userScore = 0;
    answeredQuestions.clear();
    setText("mcq-score", 0);
    setText("mcq-done", 0);
    initMCQ();
}

function escapeHtml(str) {
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}
