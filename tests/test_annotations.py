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
    assert page.locator(".mcq-card").count() == 7
    assert page.locator("#main-content .lexi").count() == 7
    assert page.page_errors == []
    # the unreadable value is kept aside instead of being overwritten by the next save
    add_highlight(page)
    assert page.evaluate("localStorage.getItem(LS.highlights + '_unreadable')") == "{not json"
    assert len(stored(page, "highlights")) == 1


def export_backup(page, tmp_path, name="backup.json"):
    with page.expect_download() as dl:
        page.click("button:has-text('导出高亮')")
    backup = tmp_path / name
    dl.value.save_as(backup)
    return backup


def test_export_then_import_round_trip(page, browser, demo_guide, tmp_path):
    text = add_highlight(page)
    add_note(page, "备份里的批注", "可以复述", "判断")
    backup = export_backup(page, tmp_path)
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


# Another paragraph of the demo, in the limitation block of 1.2:
#   <p>表里只算「比较次数」，没有算排序成本。……</p>
OTHER_START, OTHER_END = "表里只算", "排序成本"


IMPORT_BUTTON = {"merge": "#import-dialog .fc-btn:has-text('合并')",
                 "replace": "#import-dialog .fc-btn:has-text('覆盖')",
                 "cancel": "#import-dialog .fc-btn:has-text('取消')"}


def choose_file(page, backup):
    """Pick a backup to import and return the dialog that asks what to do with it."""
    page.set_input_files("#import-file-input", str(backup))
    dialog = page.locator("#import-dialog")
    dialog.wait_for(state="visible")
    return dialog


def import_backup(page, backup, choice):
    choose_file(page, backup)
    with page.expect_navigation():
        page.click(IMPORT_BUTTON[choice])


def device_with_own_annotations(browser, demo_guide):
    """Another browser that already has a highlight and a note of its own."""
    other = browser.new_context().new_page()
    other.goto("file://" + demo_guide)
    mine = add_highlight(other, "n 翻倍", "比较")
    add_note(other, "设备 B 的批注", OTHER_START, OTHER_END)
    return other, mine


def test_import_merges_with_annotations_already_here(page, browser, demo_guide, tmp_path):
    theirs = add_highlight(page)
    add_note(page, "设备 A 的批注", "可以复述", "判断")
    backup = export_backup(page, tmp_path)

    other, mine = device_with_own_annotations(browser, demo_guide)
    dialog = choose_file(other, backup)
    assert "备份里有 1 条高亮、1 条批注；本机现在有 1 条高亮、1 条批注" in dialog.inner_text()
    assert other.locator("#import-dialog-warning").is_hidden()
    with other.expect_navigation():
        other.click(IMPORT_BUTTON["merge"])
    assert sorted(h["text"] for h in stored(other, "highlights")) == sorted([theirs, mine])
    assert sorted(n["note"] for n in stored(other, "notes")) == ["设备 A 的批注", "设备 B 的批注"]
    assert other.locator(".note-flag").count() == 2

    # the same backup again brings nothing new, so nothing is duplicated and the page stays
    choose_file(other, backup)
    other.click(IMPORT_BUTTON["merge"])
    other.locator("#toast-msg").wait_for(state="visible")
    assert "都已经有了" in other.locator("#toast-msg").inner_text()
    assert len(stored(other, "highlights")) == 2 and len(stored(other, "notes")) == 2
    other.context.close()


def test_import_can_replace_what_is_here(page, browser, demo_guide, tmp_path):
    theirs = add_highlight(page)
    add_note(page, "设备 A 的批注", "可以复述", "判断")
    backup = export_backup(page, tmp_path)

    other, mine = device_with_own_annotations(browser, demo_guide)
    before = stored(other, "highlights")
    import_backup(other, backup, "replace")
    assert [h["text"] for h in stored(other, "highlights")] == [theirs]
    assert [n["note"] for n in stored(other, "notes")] == ["设备 A 的批注"]
    assert pieces(other, "mark.user-hl") == theirs and other.locator(".note-flag").count() == 1
    # what was replaced is kept aside once, so a mistaken choice can still be undone
    assert other.evaluate("JSON.parse(localStorage.getItem(LS.highlights + '_before_import'))") == before
    other.context.close()


def test_import_can_be_cancelled(page, browser, demo_guide, tmp_path):
    add_highlight(page)
    backup = export_backup(page, tmp_path)
    other, mine = device_with_own_annotations(browser, demo_guide)
    choose_file(other, backup)
    other.click(IMPORT_BUTTON["cancel"])
    assert other.locator("#import-dialog").is_hidden()
    assert [h["text"] for h in stored(other, "highlights")] == [mine]
    # Escape closes the dialog the same way
    choose_file(other, backup)
    other.keyboard.press("Escape")
    assert other.locator("#import-dialog").is_hidden() and len(stored(other, "highlights")) == 1
    other.context.close()


def test_a_backup_from_another_guide_is_flagged_before_importing(page, tmp_path):
    backup = tmp_path / "other-guide.json"
    backup.write_text(json.dumps({"app": "some-other-guide", "highlights": [], "notes": [
        {"id": "note_x", "text": "可以复述", "note": "别处的批注"}]}), encoding="utf-8")
    choose_file(page, backup)   # asked even though this browser has nothing yet
    assert "另一份讲义（some-other-guide）" in page.locator("#import-dialog-warning").inner_text()
    with page.expect_navigation():
        page.click(IMPORT_BUTTON["merge"])
    assert [n["note"] for n in stored(page, "notes")] == ["别处的批注"]


def test_merge_keeps_everything_and_prefers_the_newer_edit(page):
    result = page.evaluate("""() => mergeById(
        [{id: 'a', text: 'x', note: 'old', ts: 1}, {id: 'b', text: 'y', note: 'kept', ts: 5}],
        [{id: 'a', text: 'x', note: 'new', ts: 2}, {id: 'b', text: 'y', note: 'stale', ts: 3}, {id: 'c', text: 'z'}])""")
    assert result == {"list": [{"id": "a", "text": "x", "note": "new", "ts": 2},
                               {"id": "b", "text": "y", "note": "kept", "ts": 5},
                               {"id": "c", "text": "z"}], "added": 1, "updated": 1}
    # highlights are also matched by the text they anchor, so one passage is not highlighted twice
    deduped = page.evaluate("""() => mergeById([{id: 'a', text: 'x', prefix: 'p'}],
        [{id: 'b', text: 'x', prefix: 'p'}, {id: 'c', text: 'x', prefix: 'q'}], true)""")
    assert [h["id"] for h in deduped["list"]] == ["a", "c"]


def test_notes_saved_in_two_tabs_are_both_kept(page):
    other = page.context.new_page()
    other.goto(page.url)
    add_note(page, "第一个标签页")
    add_note(other, "第二个标签页", OTHER_START, OTHER_END)
    assert sorted(n["note"] for n in stored(page, "notes")) == ["第一个标签页", "第二个标签页"]
    page.click(".note-flag")
    page.click("#note-delete-btn")
    assert [n["note"] for n in stored(page, "notes")] == ["第二个标签页"]


def test_clicking_elsewhere_keeps_a_typed_note(page):
    text = select(page, SPAN_START, SPAN_END)
    page.click("#add-note-btn")
    page.fill("#note-editor-text", "差点丢掉的想法")
    page.click("#bs-overview h2")
    assert page.locator("#note-editor").is_hidden()
    assert [n["note"] for n in stored(page, "notes")] == ["差点丢掉的想法"]
    assert pieces(page, ".note-anchor") == text

    # Cancel still discards on purpose; Ctrl+Enter saves
    select(page, OTHER_START, OTHER_END)
    page.click("#add-note-btn")
    page.fill("#note-editor-text", "不要了")
    page.click("#note-editor button:has-text('取消')")
    assert len(stored(page, "notes")) == 1
    select(page, OTHER_START, OTHER_END)
    page.click("#add-note-btn")
    page.fill("#note-editor-text", "用快捷键保存")
    page.press("#note-editor-text", "Control+Enter")
    assert sorted(n["note"] for n in stored(page, "notes")) == sorted(["差点丢掉的想法", "用快捷键保存"])


def test_backup_holds_annotations_even_when_storage_writes_fail(browser, demo_guide, tmp_path):
    context = browser.new_context(accept_downloads=True)
    context.add_init_script("Storage.prototype.setItem = function () {"
                            " throw new DOMException('full', 'QuotaExceededError'); };")
    page = context.new_page()
    page.goto("file://" + demo_guide)
    text = add_highlight(page)
    assert "存储不可用" in page.locator("#toast-msg").inner_text()
    data = json.loads(export_backup(page, tmp_path).read_text(encoding="utf-8"))
    assert [h["text"] for h in data["highlights"]] == [text]
    context.close()


def test_a_highlight_inside_a_note_can_still_be_removed(page):
    add_note(page, "n")
    add_highlight(page, "因为数组有序", "整体丢掉")
    page.locator("mark.user-hl").first.click()
    assert page.locator("#remove-hl-btn").is_visible() and page.locator("#note-editor").is_hidden()
    page.click("#remove-hl-btn")
    assert page.locator("mark.user-hl").count() == 0 and stored(page, "highlights") == []
    page.click(".note-flag")
    assert page.input_value("#note-editor-text") == "n"


def test_note_button_on_a_highlight_notes_that_highlight(page):
    select(page, OTHER_START, OTHER_END)   # a selection that is then abandoned
    page.click("#bs-overview h2")
    text = add_highlight(page)
    page.locator("mark.user-hl").first.click()
    page.click("#add-note-btn")
    page.fill("#note-editor-text", "给高亮加批注")
    page.click("#note-editor button:has-text('保存批注')")
    assert pieces(page, ".note-anchor") == text
    assert stored(page, "notes")[0]["text"] == text
