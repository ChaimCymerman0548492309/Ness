"""Screenshot and trace helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import allure
from playwright.sync_api import Page

from utils.config_loader import ConfigLoader, PROJECT_ROOT


class ScreenshotHelper:
    """Captures screenshots and attaches them to Allure."""

    def __init__(self, config: ConfigLoader | None = None) -> None:
        # Creates the screenshot output directory based on config settings.
        self._config = config or ConfigLoader()
        screenshot_dir = self._config.get("screenshot_dir", "reports/screenshots")
        self._screenshot_dir = PROJECT_ROOT / screenshot_dir
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)

    def capture(self, page: Page, name: str) -> Path:
        # Takes a full-page screenshot, saves it to disk, and attaches it to the Allure report.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = name.replace(" ", "_").replace("/", "_")
        file_path = self._screenshot_dir / f"{safe_name}_{timestamp}.png"
        page.screenshot(path=str(file_path), full_page=True)
        allure.attach.file(
            str(file_path),
            name=name,
            attachment_type=allure.attachment_type.PNG,
        )
        return file_path

    def attach_trace(self, trace_path: Path, name: str = "Playwright Trace") -> None:
        # Attaches a Playwright trace ZIP file to the Allure report if it exists.
        if trace_path.exists():
            allure.attach.file(
                str(trace_path),
                name=name,
                attachment_type=allure.attachment_type.ZIP,
            )
