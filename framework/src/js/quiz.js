// Active Recall Subjective Toggle
function toggleQuiz(btn) {
    const answerDiv = btn.nextElementSibling;
    if (answerDiv.style.display === "block") {
        answerDiv.style.display = "none";
        btn.textContent = "显示答案与深度解析";
        btn.setAttribute("aria-expanded", "false");
    } else {
        answerDiv.style.display = "block";
        btn.textContent = "隐藏答案与解析";
        btn.setAttribute("aria-expanded", "true");
    }
}
