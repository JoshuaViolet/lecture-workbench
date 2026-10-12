let toastTimer = null;
function showToast(msg) {
    const toast = document.getElementById("toast-msg");
    if (!toast) return;
    toast.textContent = msg;
    toast.style.display = "block";
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.style.display = "none";
    }, 2600);
}
