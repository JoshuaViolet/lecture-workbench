// ---------- text model ----------
// Text nodes that count toward offsets: everything except the 💬 flags this engine adds.
function anchorTextNodes(block) {
    const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT, {
        acceptNode: n => (n.parentElement && n.parentElement.closest(".note-flag"))
            ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    return nodes;
}

function blockText(block) {
    return anchorTextNodes(block).map(n => n.nodeValue).join("");
}

// Character offset, within block's text, of the DOM boundary point (node, offset).
function offsetInBlock(block, node, offset) {
    const point = document.createRange();
    point.setStart(node, offset);
    let pos = 0;
    for (const t of anchorTextNodes(block)) {
        if (t === node) return pos + offset;
        if (point.comparePoint(t, t.nodeValue.length) > 0) break;   // t ends after the point
        pos += t.nodeValue.length;
    }
    return pos;
}

// Turn a selection range into an anchor inside one block, or say why it cannot be.
function anchorFromRange(range) {
    const startEl = range.startContainer.nodeType === 3 ? range.startContainer.parentElement : range.startContainer;
    const block = startEl && startEl.closest(BLOCK_SELECTOR);
    if (!block || !document.getElementById("main-content").contains(block)) return { error: "unsupported" };
    const text = blockText(block);
    const endsInside = block.contains(range.endContainer);
    let start = offsetInBlock(block, range.startContainer, range.startOffset);
    let end = endsInside ? offsetInBlock(block, range.endContainer, range.endOffset) : text.length;
    while (start < end && /\s/.test(text[start])) start++;
    while (end > start && /\s/.test(text[end - 1])) end--;
    if (start >= end) return { error: "empty" };
    const kept = text.slice(start, end);
    // a selection running into the next paragraph keeps only the part in this block
    const clipped = !endsInside && range.toString().replace(/\s+/g, "").length > kept.replace(/\s+/g, "").length;
    return {
        block: block,
        clipped: clipped,
        anchor: {
            cIdx: getAllTextContainers().indexOf(block),
            start: start,
            end: end,
            text: kept,
            prefix: text.slice(Math.max(0, start - CONTEXT_CHARS), start),
            suffix: text.slice(end, end + CONTEXT_CHARS)
        }
    };
}

// Find where a stored anchor is now. `texts` caches blockText for each block.
function locateAnchor(item, blocks, texts) {
    if (!item || typeof item.text !== "string" || !item.text) return null;
    const home = Number.isInteger(item.cIdx) ? item.cIdx : -1;
    if (blocks[home] && Number.isInteger(item.start) && Number.isInteger(item.end)
        && texts[home].slice(item.start, item.end) === item.text) {
        return { block: blocks[home], start: item.start, end: item.end };
    }
    let best = null;
    for (let b = 0; b < blocks.length; b++) {
        const t = texts[b];
        for (let i = t.indexOf(item.text); i !== -1; i = t.indexOf(item.text, i + 1)) {
            const after = i + item.text.length;
            let score = b === home ? 1 : 0;
            if (item.prefix && t.slice(Math.max(0, i - item.prefix.length), i) === item.prefix) score += 2;
            if (item.suffix && t.slice(after, after + item.suffix.length) === item.suffix) score += 2;
            if (!best || score > best.score) best = { block: blocks[b], start: i, end: after, score: score };
        }
    }
    return best;
}

// Wrap block text [start, end) using makeWrapper(); returns the wrapper elements.
function wrapTextRange(block, start, end, makeWrapper) {
    const wrappers = [];
    let pos = 0;
    for (const node of anchorTextNodes(block)) {
        const nodeStart = pos;
        const len = node.nodeValue.length;
        pos += len;
        if (pos <= start) continue;
        if (nodeStart >= end) break;
        let piece = node;
        const from = Math.max(start - nodeStart, 0);
        const to = Math.min(end - nodeStart, len);
        if (from > 0) piece = piece.splitText(from);
        if (to - from < piece.nodeValue.length) piece.splitText(to - from);
        if (!piece.nodeValue.trim()) continue;   // whitespace between inline elements
        const wrapper = makeWrapper();
        piece.parentNode.insertBefore(wrapper, piece);
        wrapper.appendChild(piece);
        wrappers.push(wrapper);
    }
    return wrappers;
}

function unwrapAll(selector) {
    document.querySelectorAll(selector).forEach(el => {
        const parent = el.parentNode;
        while (el.firstChild) parent.insertBefore(el.firstChild, el);
        parent.removeChild(el);
        parent.normalize();
    });
}

function restoreAnnotations(items, attr, wrap) {
    const valid = items.filter(item => item && item.id && !document.querySelector(byId(attr, item.id)));
    if (!valid.length) return;
    const blocks = getAllTextContainers();
    const texts = blocks.map(blockText);   // wrapping never changes the text, so this stays valid
    valid.forEach(item => {
        const at = locateAnchor(item, blocks, texts);
        if (at) wrap(at.block, at.start, at.end, item.id);
    });
}
