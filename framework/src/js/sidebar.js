// Sidebar Toggle Logic
function toggleSidebar(forceState) {
    const body = document.body;
    const isMobile = window.innerWidth <= 900;
    const pillIcon = document.getElementById("sidebar-pill-icon");
    const pillText = document.getElementById("sidebar-pill-text");

    if (isMobile) {
        if (typeof forceState === "boolean") {
            if (forceState) body.classList.add("sidebar-open");
            else body.classList.remove("sidebar-open");
        } else {
            body.classList.toggle("sidebar-open");
        }
        const isOpen = body.classList.contains("sidebar-open");
        if (pillIcon && pillText) {
            pillIcon.textContent = isOpen ? "◀" : "☰";
            pillText.textContent = isOpen ? UI.sidebar_collapse : UI.sidebar_short;
        }
    } else {
        let isCollapsed;
        if (typeof forceState === "boolean") {
            if (forceState) {
                body.classList.remove("sidebar-collapsed");
                isCollapsed = false;
            } else {
                body.classList.add("sidebar-collapsed");
                isCollapsed = true;
            }
        } else {
            isCollapsed = body.classList.toggle("sidebar-collapsed");
        }
        lsSet(LS.sidebar, isCollapsed ? "true" : "false");
        if (pillIcon && pillText) {
            pillIcon.textContent = isCollapsed ? "☰" : "◀";
            pillText.textContent = isCollapsed ? UI.sidebar_expand : UI.sidebar_collapse;
        }
    }
}

// Auto close sidebar on mobile when clicking nav items
document.querySelectorAll("#navList a").forEach(link => {
    link.addEventListener("click", () => {
        if (window.innerWidth <= 900) {
            toggleSidebar(false);
        }
    });
});

// Keyboard Shortcut '[' or ']' to toggle sidebar
document.addEventListener("keydown", function(e) {
    if ((e.key === "[" || e.key === "]") && e.target.tagName !== "INPUT" && e.target.tagName !== "TEXTAREA") {
        toggleSidebar();
    }
});

// Restore sidebar state from localStorage
if (window.innerWidth > 900 && lsGet(LS.sidebar) === "true") {
    document.body.classList.add("sidebar-collapsed");
    const pillIcon = document.getElementById("sidebar-pill-icon");
    const pillText = document.getElementById("sidebar-pill-text");
    if (pillIcon && pillText) {
        pillIcon.textContent = "☰";
        pillText.textContent = UI.sidebar_expand;
    }
}
