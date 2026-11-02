// Progress Bar
window.onscroll = function() {
    let winScroll = document.body.scrollTop || document.documentElement.scrollTop;
    let height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    let scrolled = (winScroll / height) * 100;
    document.getElementById("progress-bar").style.width = scrolled + "%";
};

// Theme Toggle
function toggleTheme() {
    const html = document.documentElement;
    const btn = document.getElementById("theme-toggle-btn");
    if (html.getAttribute("data-theme") === "dark") {
        html.setAttribute("data-theme", "light");
        btn.textContent = UI.theme_dark;
        lsSet(LS.theme, "light");
    } else {
        html.setAttribute("data-theme", "dark");
        btn.textContent = UI.theme_light;
        lsSet(LS.theme, "dark");
    }
}
if (lsGet(LS.theme) === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
    document.getElementById("theme-toggle-btn").textContent = UI.theme_light;
}

// Lightbox: clicking an image in a <figure> shows it full size, with its caption
function openLightbox(src, caption) {
    const modal = document.getElementById("lightbox-modal");
    const img = document.getElementById("lightbox-img");
    img.src = src;
    // a vector image can be shown larger than its natural size without blurring
    img.classList.toggle("is-vector", /^data:image\/svg|\.svg([?#]|$)/i.test(src));
    document.getElementById("lightbox-caption").textContent = caption || "";
    modal.style.display = "flex";
    modal.querySelector(".lightbox-close").focus();
}
function closeLightbox(e) {
    if (e.target.id === "lightbox-modal" || e.target.className === "lightbox-close") {
        document.getElementById("lightbox-modal").style.display = "none";
    }
}
document.getElementById("main-content").addEventListener("click", function(e) {
    const img = e.target.closest("figure img");
    if (!img || e.target.closest("a")) return;
    const caption = img.closest("figure").querySelector("figcaption");
    openLightbox(img.currentSrc || img.src, caption ? caption.textContent.trim() : img.alt);
});
document.addEventListener("keydown", function(e) {
    if (e.key === "Escape") {
        document.getElementById("lightbox-modal").style.display = "none";
        closeNoteEditor();
        hideTermCard();
    }
});

// Search Filter
function filterContent() {
    let input = document.getElementById("searchInput").value.toLowerCase();
    let links = document.querySelectorAll("#navList li");
    links.forEach(li => {
        let text = li.textContent.toLowerCase();
        if (text.includes(input)) {
            li.style.display = "";
        } else {
            li.style.display = input === "" ? "" : "none";
        }
    });
}
