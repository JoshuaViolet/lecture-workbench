// ---------- storage: never let a bad or unavailable localStorage stop the page ----------
function lsGet(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
}
function lsSet(key, value) {
    try { localStorage.setItem(key, value); return true; } catch (e) { return false; }
}
function lsRemove(key) {
    try { localStorage.removeItem(key); return true; } catch (e) { return false; }
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

// ---------- annotation lists ----------
// Every change re-reads the stored list, because another tab of the same guide may have
// saved since this page loaded; writing back an old copy would erase that tab's work.
// The page also keeps its own copy, so an annotation whose write failed (storage full or
// blocked) still shows up in an exported backup, as the failure message promises.
const pageLists = {};

function loadList(key) {
    pageLists[key] = readList(key);
    return pageLists[key];
}
function pageList(key) {
    return pageLists[key] || [];
}
// `change` maps a list to the changed list without mutating it; it is applied to both copies.
function changeList(key, change) {
    pageLists[key] = change(pageList(key));
    return writeList(key, change(readList(key)));
}
// What a backup should hold: the stored list plus anything only this page has.
function exportableList(key) {
    return mergeById(readList(key), pageList(key)).list;
}

function sameAnchor(a, b) {
    return a.text === b.text && (a.prefix || "") === (b.prefix || "") && (a.suffix || "") === (b.suffix || "");
}
// Merge annotations by id. Nothing in `base` is dropped; for an id in both lists the more
// recently edited record (by `ts`) wins. With `dedupe`, an incoming record that anchors the
// same text as an existing one is skipped even if its id differs.
function mergeById(base, incoming, dedupe) {
    const list = base.slice();
    const at = new Map();
    list.forEach((x, i) => { if (x && x.id) at.set(x.id, i); });
    let added = 0, updated = 0;
    incoming.forEach(x => {
        if (!x || !x.id) return;
        if (at.has(x.id)) {
            const i = at.get(x.id);
            if ((x.ts || 0) > (list[i].ts || 0)) { list[i] = x; updated++; }
        } else if (!(dedupe && list.some(y => y && sameAnchor(y, x)))) {
            at.set(x.id, list.length);
            list.push(x);
            added++;
        }
    });
    return { list: list, added: added, updated: updated };
}

function newId(prefix) {
    return prefix + "_" + Date.now() + "_" + Math.random().toString(36).slice(2, 7);
}
function byId(attr, id) {
    return `[${attr}="${CSS.escape(String(id))}"]`;
}
