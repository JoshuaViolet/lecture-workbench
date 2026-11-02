"""Browser tests for the runtime engine, run against the built demo opened from file://."""
import shutil


def mcq_rows(page):
    """For each rendered question: the authored option index shown at each on-screen position."""
    return page.eval_on_selector_all(
        ".mcq-card", "cards => cards.map(c => [...c.querySelectorAll('.mcq-opt')].map(b => +b.dataset.opt))")


def test_page_makes_no_network_requests(browser, demo_guide):
    context = browser.new_context()
    page = context.new_page()
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    page.goto("file://" + demo_guide)
    page.wait_for_load_state("load")
    assert [u for u in requests if not u.startswith(("file://", "data:"))] == []
    context.close()


def test_the_guide_works_as_a_single_copied_file(browser, demo_guide, tmp_path):
    alone = tmp_path / "Downloads" / "guide.html"   # no assets/ folder next to it
    alone.parent.mkdir()
    shutil.copy(demo_guide, alone)
    context = browser.new_context()
    page = context.new_page()
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    page.goto(alone.as_uri())
    img = page.locator("figure img")
    img.scroll_into_view_if_needed()
    page.wait_for_function("document.querySelector('figure img').complete")
    assert img.evaluate("i => i.naturalWidth") > 0
    assert requests == [alone.as_uri()]
    context.close()


def test_figure_images_open_in_the_lightbox(page):
    page.click("figure img")
    modal = page.locator("#lightbox-modal")
    assert modal.is_visible()
    assert page.locator("#lightbox-img").get_attribute("src").startswith("data:image/svg+xml;base64,")
    assert page.locator("#lightbox-caption").inner_text().startswith("图 1")
    assert page.evaluate("document.activeElement.className") == "lightbox-close"
    page.keyboard.press("Escape")
    assert modal.is_hidden()
    page.focus("figure img")
    page.keyboard.press("Enter")
    assert modal.is_visible()


def test_init_raises_no_errors(page):
    assert page.locator(".mcq-card").count() == 7
    assert page.locator("#fc-counter").inner_text() == "1 / 6"
    assert page.locator("#main-content .lexi").count() == 7
    assert page.page_errors == []


def test_mcq_options_are_shuffled_between_renders(page):
    orders = {tuple(map(tuple, mcq_rows(page)))}
    for _ in range(5):
        page.evaluate("resetMCQ()")
        orders.add(tuple(map(tuple, mcq_rows(page))))
    assert len(orders) > 1
    for row in next(iter(orders)):
        assert sorted(row) == list(range(len(row)))


def test_shuffle_false_keeps_authored_order(page):
    page.evaluate("mcqData.forEach(m => m.shuffle = false); resetMCQ()")
    for _ in range(3):
        assert all(row == sorted(row) for row in mcq_rows(page))
        page.evaluate("resetMCQ()")


def test_scoring_follows_the_answer_not_the_position(page):
    answers = page.evaluate("mcqData.map(m => m.ans)")
    cards = page.locator(".mcq-card")
    # answer the first question correctly and the second one wrongly
    cards.nth(0).locator(f'.mcq-opt[data-opt="{answers[0]}"]').click()
    wrong = (answers[1] + 1) % 4
    cards.nth(1).locator(f'.mcq-opt[data-opt="{wrong}"]').click()
    assert page.locator("#mcq-done").inner_text() == "2"
    assert page.locator("#mcq-score").inner_text() == "1"
    assert "correct" in cards.nth(0).locator(f'.mcq-opt[data-opt="{answers[0]}"]').get_attribute("class")
    second = cards.nth(1)
    assert "incorrect" in second.locator(f'.mcq-opt[data-opt="{wrong}"]').get_attribute("class")
    assert "correct" in second.locator(f'.mcq-opt[data-opt="{answers[1]}"]').get_attribute("class")
    assert second.locator(".mcq-explain").is_visible()


def test_print_sheet_lists_answer_text(page):
    page.evaluate("mcqData.push({q: 'five options', opts: ['a', 'b', 'c', 'd', 'e<b>'], ans: 4, exp: 'x'});"
                  "buildPrintSheet()")
    sheet = page.locator("#print-sheet").inner_text()
    first = page.evaluate("mcqData[0].opts[mcqData[0].ans]")
    assert first in sheet
    assert "e<b>" in sheet and "undefined" not in sheet


def test_the_self_test_sheet_leaves_out_what_the_guide_does_not_have(page):
    page.evaluate("mcqData.length = 0; buildPrintSheet()")
    assert page.locator("#print-sheet h3").count() == 1 and "Q:" in page.locator("#print-sheet").inner_text()
    page.evaluate("flashcards.length = 0; buildPrintSheet()")
    assert page.locator("#print-sheet").count() == 0   # no empty "0 cards, 0 questions" page


def test_collapsed_details_print_open_and_close_again(page):
    page.evaluate("""document.getElementById('bs-transfer').insertAdjacentHTML('beforeend',
        '<details id="reading"><summary>Reading</summary><p>Chapter 3</p></details>'
        + '<details id="open-one" open><summary>Open</summary><p>x</p></details>')""")
    is_open = "['reading', 'open-one'].map(id => document.getElementById(id).open)"
    page.evaluate("dispatchEvent(new Event('beforeprint'))")
    assert page.evaluate(is_open) == [True, True]
    page.evaluate("dispatchEvent(new Event('afterprint'))")
    assert page.evaluate(is_open) == [False, True]


def test_code_field_and_multiline_options_keep_their_layout(page):
    page.evaluate("mcqData.length = 1;"
                  "mcqData[0] = {q: 'What prints?', code: 'for i in range(2):\\n    print(i <b>)',"
                  " opts: ['0\\n1', '1\\n2', 'one line'], ans: 0, exp: 'x'}; resetMCQ()")
    card = page.locator(".mcq-card").first
    assert card.locator("pre.mcq-code code").inner_text() == "for i in range(2):\n    print(i <b>)"
    assert card.locator(".mcq-code").evaluate("el => getComputedStyle(el).whiteSpace") == "pre"
    multi = card.locator('.mcq-opt[data-opt="0"]')
    assert "is-code" in multi.get_attribute("class") and multi.inner_text() == "0\n1"
    assert "is-code" not in card.locator('.mcq-opt[data-opt="2"]').get_attribute("class")
    page.evaluate("buildPrintSheet()")
    assert "print(i <b>)" in page.locator("#print-sheet .mcq-code").inner_text()


def test_demo_questions_without_code_have_no_code_block(page):
    without = page.evaluate("mcqData.filter(m => !m.code).length")
    assert page.locator(".mcq-card:not(:has(.mcq-code))").count() == without


def test_term_card_hides_fields_a_term_does_not_have(page):
    page.evaluate("termLexicon[0] = {keys: ['binary search'], term: 'Binary search'}; buildLexiconIndex();"
                  "showTermCard(termLexicon[0], document.querySelector('#main-content .lexi'))")
    card = page.locator("#term-card")
    assert card.is_visible() and "undefined" not in card.inner_text()
    assert card.locator(".tc-row:visible, #tc-hook:visible").count() == 0
    page.evaluate("showTermCard({term: 'T', ipa: '/t/', parts: 'from <b>x</b>', hook: 'h'},"
                  " document.querySelector('#main-content .lexi'))")
    assert card.locator(".tc-row:visible").count() == 2 and card.locator("#tc-parts b").inner_text() == "x"


def test_reading_aloud_picks_an_installed_english_voice(page):
    pick = """voices => { speechSynthesis.getVoices = () => voices; const v = englishVoice(); return v && v.name; }"""
    assert page.evaluate(pick, [{"lang": "zh-CN", "name": "Tingting"}, {"lang": "en_US", "name": "Samantha"},
                                {"lang": "en-GB", "name": "Daniel"}]) == "Daniel"
    assert page.evaluate(pick, [{"lang": "zh-CN", "name": "Tingting"}, {"lang": "en-IN", "name": "Rishi"}]) == "Rishi"
    assert page.evaluate(pick, [{"lang": "zh-CN", "name": "Tingting"}]) is None


def test_reading_aloud_says_the_english_words_only(page):
    said = page.evaluate("""() => {
        let said = null;
        speechSynthesis.speak = u => { said = u.text; };
        currentTermEntry = termLexicon[0];   // "Binary search 二分查找"
        speakCurrentTerm();
        return said;
    }""")
    assert said == "Binary search"
    say = "entry => termToSay(entry)"
    assert page.evaluate(say, {"term": "Invariant（不变式）", "keys": ["invariant"]}) == "Invariant"
    assert page.evaluate(say, {"term": "EEG / ERP (脑电)", "keys": ["eeg"]}) == "EEG ERP"
    assert page.evaluate(say, {"term": "二分查找", "keys": ["binary search"]}) == "binary search"


def test_where_scripts_do_not_run_the_page_says_so_and_shows_the_answers(browser, demo_guide, page):
    assert page.locator(".noscript-note").count() == 0   # scripts running: no notice
    context = browser.new_context(java_script_enabled=False)
    still = context.new_page()
    still.goto("file://" + demo_guide)
    assert "浏览器" in still.locator(".noscript-note").inner_text()
    assert still.locator(".quiz-a").first.is_visible()
    assert still.locator(".quiz-toggle").first.is_hidden() and still.locator("#sidebar-toggle-pill").is_hidden()
    context.close()


def test_sidebar_shortcut_leaves_browser_shortcuts_and_typing_alone(page):
    collapsed = "document.body.classList.contains('sidebar-collapsed')"
    for key in ("Control+BracketLeft", "Meta+BracketLeft", "Alt+BracketRight"):
        page.keyboard.press(key)
        assert page.evaluate(collapsed) is False, key
    page.focus("#searchInput")
    page.keyboard.press("BracketLeft")
    assert page.evaluate(collapsed) is False
    page.locator("#bs-overview h2").click()
    page.keyboard.press("BracketLeft")
    assert page.evaluate(collapsed) is True


def test_contents_filter_follows_any_input(page):
    page.fill("#searchInput", "抽认")   # no key events, as when pasting
    visible = page.locator("#navList li:visible")
    assert visible.count() == 1 and "抽认卡" in visible.inner_text()
    page.fill("#searchInput", "")
    assert page.locator("#navList li:visible").count() == page.locator("#navList li").count()


def test_highlights_print_as_underlines_in_both_themes(page):
    page.evaluate("""() => {
        const p = [...document.querySelectorAll('#main-content p')].find(p => p.textContent.includes('判断：'));
        const r = document.createRange(); r.selectNodeContents(p.querySelector('strong'));
        getSelection().removeAllRanges(); getSelection().addRange(r);
    }""")
    page.locator("#text-selection-toolbar").wait_for(state="visible")
    page.click("#add-hl-btn")
    page.emulate_media(media="print")
    background = "document.querySelector('mark.user-hl') && getComputedStyle(document.querySelector('mark.user-hl')).backgroundColor"
    assert page.evaluate(background) == "rgba(0, 0, 0, 0)"
    page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
    assert page.evaluate(background) == "rgba(0, 0, 0, 0)"


def test_wrong_answers_are_remembered_for_a_retry(page):
    answers = page.evaluate("mcqData.map(m => m.ans)")
    cards = page.locator(".mcq-card")
    cards.nth(0).locator(f'.mcq-opt[data-opt="{(answers[0] + 1) % 4}"]').click()   # wrong
    cards.nth(1).locator(f'.mcq-opt[data-opt="{answers[1]}"]').click()             # right
    assert page.locator("#mcq-only-wrong").inner_text() == "🔁 只练上次答错的 1 题"

    page.reload()
    assert page.locator(".mcq-badge").count() == 1
    assert page.locator("#mcq-card-0 .mcq-badge").inner_text() == "上次答错"
    page.click("#mcq-only-wrong")
    assert page.locator(".mcq-card").count() == 1 and page.locator("#mcq-card-0").count() == 1
    assert page.locator("#mcq-only-wrong").get_attribute("aria-pressed") == "true"
    page.locator(f'#mcq-card-0 .mcq-opt[data-opt="{answers[0]}"]').click()    # right this time
    assert page.locator(".mcq-card").count() == 1                              # the set stays while practising
    page.click("#mcq-only-wrong")
    assert page.locator(".mcq-card").count() == 7 and page.locator("#mcq-only-wrong").count() == 0
    page.reload()
    assert page.locator(".mcq-badge").count() == 0


def test_remembered_results_follow_the_question_not_its_position(page):
    answers = page.evaluate("mcqData.map(m => m.ans)")
    page.locator(f'#mcq-card-0 .mcq-opt[data-opt="{(answers[0] + 1) % 4}"]').click()
    stem = page.evaluate("mcqData[0].q")
    page.evaluate("mcqData.reverse(); resetMCQ()")
    assert page.locator(".mcq-card:has(.mcq-badge) .mcq-q").inner_text() == stem
    assert page.evaluate("mcqKey({q: 'a'}) !== mcqKey({q: 'a', code: 'x'})")


def test_tables_scroll_inside_their_box_on_a_phone(browser, demo_guide):
    context = browser.new_context(viewport={"width": 360, "height": 740})
    page = context.new_page()
    page.goto("file://" + demo_guide)
    assert page.locator(".table-scroll > table").count() == page.locator("#main-content table").count() == 2
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    # a header cell is never narrower than one line of its text
    assert page.evaluate("[...document.querySelectorAll('#main-content th')].every("
                         "th => th.getBoundingClientRect().height < 2 * parseFloat(getComputedStyle(th).lineHeight)"
                         " + 2 * parseFloat(getComputedStyle(th).paddingTop))")
    context.close()


def test_the_contents_mark_the_section_being_read(page):
    page.evaluate("document.documentElement.style.scrollBehavior = 'auto';"
                  "document.getElementById('bs-pitfalls').scrollIntoView()")
    page.wait_for_function("document.querySelector('#navList a.active')")
    active = page.locator("#navList a.active")
    assert active.count() == 1 and active.inner_text() == "1.3 前提与边界"
    assert active.get_attribute("aria-current") == "location"
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_function("document.querySelector('#navList a.active').textContent.includes('1.6')")


def test_theme_follows_the_system_unless_the_reader_picks_one(browser, demo_guide):
    context = browser.new_context(color_scheme="dark")
    page = context.new_page()
    page.goto("file://" + demo_guide)
    theme = "document.documentElement.getAttribute('data-theme')"
    picker = page.locator("#theme-select")
    assert page.evaluate(theme) == "dark" and picker.input_value() == "system"
    page.emulate_media(color_scheme="light")          # the system switches while the page is open
    page.wait_for_function(theme + " === 'light'")

    picker.select_option("dark")                      # the reader's own choice wins over the system
    page.reload()
    assert page.evaluate(theme) == "dark" and picker.input_value() == "dark"
    page.emulate_media(color_scheme="dark")
    page.emulate_media(color_scheme="light")
    assert page.evaluate(theme) == "dark"

    picker.select_option("system")                    # and following the system can be chosen again
    assert page.evaluate(theme) == "light"
    assert page.evaluate("localStorage.getItem(LS.theme)") is None
    page.reload()
    assert page.evaluate(theme) == "light" and picker.input_value() == "system"
    context.close()
