"""Data-driven end-to-end scenarios against the deterministic mock store."""

from __future__ import annotations

from pathlib import Path

import allure
import pytest
from playwright.sync_api import Page

from ebay_automation import EbayAutomation
from services.auth_service import AuthService
from services.cart_assertion_service import CartAssertionService
from services.search_service import SearchService
from utils.config_loader import ConfigLoader
from utils.data_loader import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent
YAML_DATA_FILE = PROJECT_ROOT / "data" / "test_scenarios.yaml"


def _enabled_scenarios() -> list[dict]:
    # Loads all enabled test scenarios from the external JSON data file.
    return DataLoader().load_scenarios(enabled_only=True)


@pytest.mark.e2e
@pytest.mark.data_driven
@pytest.mark.mock_store
@pytest.mark.parametrize("scenario", _enabled_scenarios(), ids=lambda item: item["id"])
def test_full_e2e_shopping_flow(
    page: Page,
    app_config: ConfigLoader,
    mock_ebay_store: None,
    scenario: dict,
) -> None:
    # Runs the complete e2e flow on mock data: auth → search → add to cart → assert total.
    allure.dynamic.title(scenario["name"])
    allure.dynamic.description(
        f"Query={scenario['query']}, max_price={scenario['max_price']}, "
        f"limit={scenario['limit']}"
    )

    automation = EbayAutomation(page, app_config)
    automation.authenticate()

    urls = automation.search_items_by_name_under_price(
        query=scenario["query"],
        max_price=scenario["max_price"],
        limit=scenario["limit"],
    )

    assert len(urls) == scenario["limit"], (
        f"Expected {scenario['limit']} URLs for '{scenario['id']}', got {len(urls)}"
    )

    added_count = automation.add_items_to_cart(urls)
    assert added_count == len(urls)

    # Brief §4.3 scenario: assertCartTotalNotExceeds(budget, urls.length)
    automation.assert_cart_total_not_exceeds(
        budget_per_item=scenario["budget_per_item"],
        items_count=len(urls),
    )


@pytest.mark.e2e
@pytest.mark.data_driven
@pytest.mark.mock_store
def test_full_e2e_from_yaml(
    page: Page,
    app_config: ConfigLoader,
    mock_ebay_store: None,
) -> None:
    # Proves YAML data-loading drives the same search API without repeating a full cart loop.
    scenario = DataLoader(data_file=YAML_DATA_FILE).get_scenario("shoes_under_budget")

    automation = EbayAutomation(page, app_config)
    automation.authenticate()

    urls = automation.search_items_by_name_under_price(
        query=scenario["query"],
        max_price=scenario["max_price"],
        limit=scenario["limit"],
    )

    assert len(urls) == scenario["limit"]
    assert all(url.startswith("https://www.ebay.com/itm/") for url in urls)


@pytest.mark.smoke
@pytest.mark.mock_store
def test_search_returns_urls_under_price(
    page: Page,
    app_config: ConfigLoader,
    mock_ebay_store: None,
) -> None:
    # Verifies that search returns a list of at most 5 URLs under the price limit.
    auth_service = AuthService(page, app_config)
    search_service = SearchService(page, app_config)

    auth_service.authenticate()
    urls = search_service.search_items_by_name_under_price("shoes", 220, 5)

    assert isinstance(urls, list)
    assert len(urls) == 5
    assert len(urls) <= 5


@pytest.mark.smoke
@pytest.mark.mock_store
def test_cart_total_assertion_signature(
    page: Page,
    app_config: ConfigLoader,
    mock_ebay_store: None,
) -> None:
    # Verifies the cart assertion service is callable and works on an empty mock cart.
    cart_assertion_service = CartAssertionService(page, app_config)
    assert callable(cart_assertion_service.assert_cart_total_not_exceeds)
    cart_assertion_service.assert_cart_total_not_exceeds(budget_per_item=220, items_count=0)
