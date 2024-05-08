from contextlib import contextmanager
from time import sleep

import pytest
from playwright.sync_api import Page, expect

LOCAL_TEST = False

PORT = "8503" if LOCAL_TEST else "8699"

@pytest.fixture(scope="module", autouse=True)
def before_module():
    # Run the streamlit app before each module
    with run_streamlit():
        yield


@pytest.fixture(scope="function", autouse=True)
def before_test(page: Page):
    page.goto(f"localhost:{PORT}")
    page.set_viewport_size({"width": 200, "height": 200})


# Take screenshot of each page if there are failures for this session
@pytest.fixture(scope="function", autouse=True)
def after_test(page: Page, request):
    yield
    if request.node.rep_call.failed:
        page.screenshot(path=f"tests/data/screenshot-{request.node.name}.png", full_page=True)


@contextmanager
def run_streamlit():
    """Run the streamlit app at examples/streamlit_app.py on port 8599"""
    import subprocess

    if LOCAL_TEST:
        try:
            yield 1
        finally:
            pass
    else:
        p = subprocess.Popen(
            [
                "streamlit",
                "run",
                "src/main.py",
                "--server.port",
                PORT,
                "--server.headless",
                "true",
            ],
        )

        sleep(5)

        try:
            yield 1
        finally:
            p.kill()


def test_page(page: Page):
    # Check page loads
    # huge timeout here as local testing is slow
    page.set_default_timeout(100000)
    expect(page).to_have_title("Satellite Image Viewer")
