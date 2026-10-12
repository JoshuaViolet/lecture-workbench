// ==========================================
// PRINT SHEET (beforeprint 生成自测清单 + 强制图片加载)
// ==========================================
function buildPrintSheet() {
    document.querySelectorAll("#print-sheet").forEach(el => el.remove());
    let html = '<h2>附录：自测清单（打印专用）</h2>';
    html += '<h3>抽认卡 Q→A（共 ' + flashcards.length + ' 张）</h3><ol>';
    flashcards.forEach(c => {
        html += '<li style="margin-bottom:8px;"><strong>Q:</strong> ' + escapeHtml(c.front) + '<br><strong>A:</strong> ' + escapeHtml(c.back) + '</li>';
    });
    html += '</ol><h3>MCQ 答案速查（共 ' + mcqData.length + ' 题）</h3><ol>';
    mcqData.forEach(m => {
        // options are shuffled on screen, so print the answer text rather than a letter
        html += '<li style="margin-bottom:8px;">' + escapeHtml(m.q) + '<br><strong>✓</strong> ' + escapeHtml(m.opts[m.ans]) + '<br><span style="color:#444;">' + m.exp + '</span></li>';
    });
    html += '</ol>';
    const sheet = document.createElement("div");
    sheet.id = "print-sheet";
    sheet.className = "print-only";
    sheet.innerHTML = html;
    document.getElementById("main-content").appendChild(sheet);
}

window.addEventListener("beforeprint", () => {
    buildPrintSheet();
    // 懒加载图片在打印前全部强制加载，否则未滚动到的幻灯片会打印空白
    document.querySelectorAll('img[loading="lazy"]').forEach(img => { img.loading = "eager"; });
});
window.addEventListener("afterprint", () => {
    const el = document.getElementById("print-sheet");
    if (el) el.remove();
});
