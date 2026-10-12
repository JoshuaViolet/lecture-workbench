// ---------- storage: never let a bad or unavailable localStorage stop the page ----------
function lsGet(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
}
function lsSet(key, value) {
    try { localStorage.setItem(key, value); return true; } catch (e) { return false; }
}
function readList(key) {
    const raw = lsGet(key);
    if (!raw) return [];
    try {
        const value = JSON.parse(raw);
        if (Array.isArray(value)) return value;
    } catch (e) { /* fall through */ }
    // keep the unreadable value instead of overwriting it on the next save
    if (lsGet(key + "_unreadable") === null) lsSet(key + "_unreadable", raw);
    return [];
}
function writeList(key, list) {
    if (!lsSet(key, JSON.stringify(list))) {
        showToast(UI.toast_storage_failed);
        return false;
    }
    return true;
}
function newId(prefix) {
    return prefix + "_" + Date.now() + "_" + Math.random().toString(36).slice(2, 7);
}
function byId(attr, id) {
    return `[${attr}="${CSS.escape(String(id))}"]`;
}
