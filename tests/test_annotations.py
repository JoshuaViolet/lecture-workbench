"""Highlights and margin notes: creation, persistence across reloads, removal, backups."""
import json

# A paragraph in the demo whose middle is wrapped in <strong>:
#   <p>可以复述的判断：<strong>因为数组有序，……整体丢掉。</strong>这一步是二分查找的全部力量来源。</p>
SPAN_START, SPAN_END = "判断：", "这一步"

SELECT_JS = """([startText, endText, occurrence]) => {
    const p = [...document.querySelectorAll('#main-content p')]
        .find(p => p.textContent.includes(startText) && p.textContent.includes(endText));
    const nodes = [];
    const walker = document.createTreeWalker(p, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) nodes.push(walker.currentNode);
    const hits = (text) => nodes.flatMap(n => {
        const out = [];
        for (let i = n.nodeValue.indexOf(text); i !== -1; i = n.nodeValue.indexOf(text, i + 1)) out.push([n, i]);
        return out;
    });
    const [sNode, sOff] = hits(startText)[occurrence];
    const [eNode, eOff] = hits(endText).filter(([n, i]) => n !== sNode || i >= sOff)[0];
    const r = document.createRange();
    r.setStart(sNode, sOff);
    r.setEnd(eNode, eOff + endText.length);
    getSelection().removeAllRanges();
    getSelection().addRange(r);
    return r.toString();
}"""


def select(page, start, end, occurrence=0):
    text = page.evaluate(SELECT_JS, [start, end, occurrence])
    page.locator("#text-selection-toolbar").wait_for(state="visible")
    return text.strip()


def pieces(page, selector):
    """Text covered by the matching wrappers, without the 💬 note flags placed inside them."""
    return page.eval_on_selector_all(selector, """els => els.map(e => {
        const copy = e.cloneNode(true);
        copy.querySelectorAll('.note-flag').forEach(f => f.remove());
        return copy.textContent;
    }).join('')""")


def stored(page, key):
    return page.evaluate(f"JSON.parse(localStorage.getItem(LS.{key}) || '[]')")


def add_highlight(page, start=SPAN_START, end=SPAN_END, occurrence=0):
    text = select(page, start, end, occurrence)
    page.click("#add-hl-btn")
    return text


def add_note(page, note, start=SPAN_START, end=SPAN_END):
    text = select(page, start, end)
    page.click("#add-note-btn")
    page.fill("#note-editor-text", note)
    page.click("#note-editor button:has-text('保存批注')")
    return text


def test_highlight_across_inline_markup_survives_reload(page):
    text = add_highlight(page)
    assert page.locator("mark.user-hl").count() >= 3        # before, inside and after <strong>
    assert pieces(page, "mark.user-hl") == text
    assert len({m for m in page.eval_on_selector_all("mark.user-hl", "els => els.map(e => e.dataset.hlId)")}) == 1

    page.reload()
    assert pieces(page, "mark.user-hl") == text
    assert page.locator("#main-content strong mark.user-hl").count() == 1
    assert page.page_errors == []


def test_removing_a_highlight_removes_every_piece(page):
    add_highlight(page)
    page.locator("mark.user-hl").first.click()
    page.click("#remove-hl-btn")
    assert page.locator("mark.user-hl").count() == 0
    assert stored(page, "highlights") == []
    page.reload()
    assert page.locator("mark.user-hl").count() == 0


def test_repeated_text_keeps_the_occurrence_that_was_selected(page):
    # "翻倍" appears twice in one paragraph: "n 翻倍，二分查找只多 1 次比较；线性查找的次数也跟着翻倍。"
    add_highlight(page, "翻倍", "翻倍", occurrence=1)
    page.reload()
    before = page.eval_on_selector("mark.user-hl", "m => m.previousSibling.nodeValue")
    assert before.endswith("跟着")


def test_restore_falls_back_to_context_when_offsets_are_stale(page):
    text = add_highlight(page)
    record = stored(page, "highlights")[0]
    # pretend the page structure changed: wrong block index and wrong offsets
    record.update(cIdx=0, start=0, end=len(text))
    page.evaluate("r => localStorage.setItem(LS.highlights, JSON.stringify([r]))", record)
    page.reload()
    assert pieces(page, "mark.user-hl") == text
    assert "可以复述的判断" in page.eval_on_selector("mark.user-hl", "m => m.closest('p').textContent")


def test_legacy_record_without_offsets_restores_across_markup(page):
    text = page.evaluate(SELECT_JS, [SPAN_START, SPAN_END, 0]).strip()
    c_idx = page.evaluate("getAllTextContainers().indexOf(getSelection().getRangeAt(0).startContainer.parentElement.closest('p'))")
    legacy = [{"id": "hl_legacy", "cIdx": c_idx, "text": text}]
    page.evaluate("r => localStorage.setItem(LS.highlights, JSON.stringify(r))", legacy)
    page.reload()
    assert pieces(page, "mark.user-hl") == text


def test_note_across_inline_markup_survives_reload_and_delete(page):
    text = add_note(page, "考试会问为什么要有序")
    assert pieces(page, ".note-anchor") == text
    assert page.locator(".note-flag").count() == 1
    assert page.locator("#note-count").inner_text() == "1"

    page.reload()
    assert pieces(page, ".note-anchor") == text
    page.click(".note-flag")
    assert page.input_value("#note-editor-text") == "考试会问为什么要有序"
    page.click("#note-delete-btn")
    assert page.locator(".note-anchor, .note-flag").count() == 0
    assert stored(page, "notes") == []
    assert page.locator("#note-count").inner_text() == "0"


def test_highlight_and_note_on_overlapping_text_both_restore(page):
    note_text = add_note(page, "n")
    hl_text = add_highlight(page, "因为数组有序", "整体丢掉")
    page.reload()
    assert pieces(page, ".note-anchor") == note_text
    assert pieces(page, "mark.user-hl") == hl_text


def test_unreadable_storage_does_not_break_the_page(page):
    page.evaluate("localStorage.setItem(LS.highlights, '{not json'); localStorage.setItem(LS.notes, '[1,')")
    page.reload()
    assert page.locator(".mcq-card").count() == 6
    assert page.locator("#main-content .lexi").count() == 7
    assert page.page_errors == []
    # the unreadable value is kept aside instead of being overwritten by the next save
    add_highlight(page)
    assert page.evaluate("localStorage.getItem(LS.highlights + '_unreadable')") == "{not json"
    assert len(stored(page, "highlights")) == 1


def test_export_then_import_round_trip(page, browser, demo_guide, tmp_path):
    text = add_highlight(page)
    add_note(page, "备份里的批注", "可以复述", "判断")
    with page.expect_download() as dl:
        page.click("button:has-text('导出高亮')")
    backup = tmp_path / "backup.json"
    dl.value.save_as(backup)
    data = json.loads(backup.read_text(encoding="utf-8"))
    assert data["version"] == 2 and data["app"] == page.evaluate("APP_ID")
    assert len(data["highlights"]) == 1 and len(data["notes"]) == 1

    fresh = browser.new_context().new_page()
    fresh.goto("file://" + demo_guide)
    with fresh.expect_navigation():
        fresh.set_input_files("#import-file-input", str(backup))
    assert pieces(fresh, "mark.user-hl") == text
    assert fresh.locator(".note-flag").count() == 1
    fresh.context.close()
