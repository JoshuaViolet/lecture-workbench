"""Browser tests for the runtime engine, run against the built demo opened from file://."""


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


def test_init_raises_no_errors(page):
    assert page.locator(".mcq-card").count() == 6
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
