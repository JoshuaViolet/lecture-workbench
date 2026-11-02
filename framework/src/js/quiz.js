// Active recall: a button shows or hides the answer right after it. The button keeps the
// label its author gave it ("Check your reasoning", "Hint") and reads "Hide" only while its
// answer is open, so a card can have several steps (hint, worked answer, model answer) that
// stay told apart. A button without a label of its own gets the generic one.
function toggleQuiz(btn) {
    const answerDiv = btn.nextElementSibling;
    if (!("label" in btn.dataset)) btn.dataset.label = btn.textContent.trim() || UI.quiz_show;
    const open = answerDiv.style.display !== "block";
    answerDiv.style.display = open ? "block" : "none";
    btn.textContent = open ? UI.quiz_hide : btn.dataset.label;
    btn.setAttribute("aria-expanded", String(open));
}
