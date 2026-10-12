let userScore = 0;
let answeredQuestions = new Set();

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
    mcqData.forEach((item, qIdx) => {
        const card = document.createElement("div");
        card.className = "mcq-card";
        card.id = `mcq-card-${qIdx}`;

        const qTitle = document.createElement("div");
        qTitle.className = "mcq-q";
        qTitle.textContent = item.q;
        card.appendChild(qTitle);

        const optsDiv = document.createElement("div");
        optsDiv.className = "mcq-options";

        optionOrder(item).forEach(oIdx => {
            const optBtn = document.createElement("button");
            optBtn.className = "mcq-opt";
            optBtn.textContent = item.opts[oIdx];
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
