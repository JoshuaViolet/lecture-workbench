// Active Recall Subjective Toggle
function toggleQuiz(btn) {
    const answerDiv = btn.nextElementSibling;
    if (answerDiv.style.display === "block") {
        answerDiv.style.display = "none";
        btn.textContent = UI.quiz_show;
        btn.setAttribute("aria-expanded", "false");
    } else {
        answerDiv.style.display = "block";
        btn.textContent = UI.quiz_hide;
        btn.setAttribute("aria-expanded", "true");
    }
}
