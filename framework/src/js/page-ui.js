// Progress Bar
window.onscroll = function() {
    let winScroll = document.body.scrollTop || document.documentElement.scrollTop;
    let height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    let scrolled = height > 0 ? Math.min(100, (winScroll / height) * 100) : 0;
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
// the theme itself was set in <head>; the button offers the other one
if (document.documentElement.getAttribute("data-theme") === "dark") {
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

// Tables keep their columns readable on a phone: they scroll sideways inside their own box
// instead of squeezing every column or running out of the page.
function wrapTables() {
    document.querySelectorAll("#main-content table").forEach(table => {
        if (table.parentElement.classList.contains("table-scroll")) return;
        const box = document.createElement("div");
        box.className = "table-scroll";
        table.parentNode.insertBefore(box, table);
        box.appendChild(table);
    });
}

// Contents: mark the entry of the section being read (the last target whose top has passed
// the upper third of the window), and keep it in view in a long sidebar.
let navTargets = [];
function initScrollSpy() {
    navTargets = [];
    document.querySelectorAll('#navList a[href^="#"]').forEach(a => {
        let id = a.getAttribute("href").slice(1);
        try { id = decodeURIComponent(id); } catch (e) { /* use it as written */ }
        const target = id && document.getElementById(id);
        if (target) navTargets.push({ target: target, link: a });
    });
    navTargets.sort((x, y) => (x.target.compareDocumentPosition(y.target) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1));
    if (!navTargets.length) return;
    let queued = false;
    window.addEventListener("scroll", () => {
        if (queued) return;
        queued = true;
        requestAnimationFrame(() => { queued = false; updateActiveNav(); });
    }, { passive: true });
    updateActiveNav();
}
function updateActiveNav() {
    const line = window.innerHeight / 3;
    let current = null;
    for (const nt of navTargets) {
        if (nt.target.getBoundingClientRect().top <= line) current = nt.link;
        else break;
    }
    // at the very bottom of a long page, the last section is the one being read even if it is short
    const docHeight = document.documentElement.scrollHeight;
    if (docHeight > window.innerHeight + 2 && window.innerHeight + window.scrollY >= docHeight - 2) {
        current = navTargets[navTargets.length - 1].link;
    }
    navTargets.forEach(nt => {
        const on = nt.link === current;
        if (on === nt.link.classList.contains("active")) return;
        nt.link.classList.toggle("active", on);
        if (on) {
            nt.link.setAttribute("aria-current", "location");
            const sb = document.getElementById("sidebar");
            const r = nt.link.getBoundingClientRect(), s = sb.getBoundingClientRect();
            if (r.top < s.top || r.bottom > s.bottom) sb.scrollTop += r.top - s.top - s.height / 3;
        } else {
            nt.link.removeAttribute("aria-current");
        }
    });
}

// Search Filter
function filterContent() {
    let input = document.getElementById("searchInput").value.trim().toLowerCase();
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
