// ==========================================
// ACCESSIBILITY (键盘流：抽认卡 / 灯箱)
// ==========================================
function initA11y() {
    const fc = document.getElementById("flashcard-element");
    if (fc) {
        fc.addEventListener("keydown", (e) => {
            if (e.key === " " || e.key === "Enter") { e.preventDefault(); flipCard(); }
            else if (e.key === "ArrowRight") { e.preventDefault(); nextCard(); }
            else if (e.key === "ArrowLeft") { e.preventDefault(); prevCard(); }
        });
    }
    const lbClose = document.querySelector("#lightbox-modal .lightbox-close");
    if (lbClose) {
        lbClose.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") { e.preventDefault(); closeLightbox(e); }
        });
    }
}
