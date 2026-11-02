// ==========================================
// ACCESSIBILITY (键盘流：抽认卡 / 图片 / 灯箱)
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
    // figure images open in the lightbox from the keyboard too
    document.querySelectorAll("#main-content figure img").forEach(img => {
        if (img.closest("a")) return;
        img.tabIndex = 0;
        img.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") { e.preventDefault(); img.click(); }
        });
    });
    const lbClose = document.querySelector("#lightbox-modal .lightbox-close");
    if (lbClose) {
        lbClose.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") { e.preventDefault(); closeLightbox(e); }
        });
    }
}
