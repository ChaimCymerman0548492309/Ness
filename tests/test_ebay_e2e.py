"""Data-driven end-to-end scenarios against the deterministic mock store."""

from __future__ import annotations

from pathlib import Path

import allure
import pytest
from playwright.sync_api import Page

from ebay_automation import (
    EbayAutomation,
    assertCartTotalNotExceeds,
    addItemsToCart,
    authenticate,
    searchItemsByNameUnderPrice,
)
from services.auth_service import AuthService
from services.cart_assertion_service import CartAssertionService
from services.search_service import SearchService
from utils.config_loader import ConfigLoader
from utils.data_loader import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent
YAML_DATA_FILE = PROJECT_ROOT / "data" / "test_scenarios.yaml"
CSV_DATA_FILE = PROJECT_ROOT / "data" / "test_scenarios.csv"


def _enabled_scenarios() -> list[dict]:
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
    # Full brief scenario: searchItemsByNameUnderPrice → addItemsToCart → assertCartTotalNotExceeds.
    allure.dynamic.title(scenario["name"])
    allure.dynamic.description(
        f"Query={scenario['query']}, maxPrice={scenario['maxPrice']}, "
        f"limit={scenario['limit']}"
    )

    automation = EbayAutomation(page, app_config)
    automation.authenticate()

    urls = automation.searchItemsByNameUnderPrice(
        query=scenario["query"],
        maxPrice=scenario["maxPrice"],
        limit=scenario["limit"],
    )

    assert len(urls) == scenario["limit"], (
        f"Expected {scenario['limit']} URLs for '{scenario['id']}', got {len(urls)}"
    )

    automation.addItemsToCart(urls)
    automation.assertCartTotalNotExceeds(
        budgetPerItem=scenario["budgetPerItem"],
        itemsCount=len(urls),
    )


@pytest.mark.e2e
@pytest.mark.data_driven
@pytest.mark.mock_store
def test_full_e2e_from_yaml(
    page: Page,
    app_config: ConfigLoader,
    mock_ebay_store: None,
) -> None:
    scenario = DataLoader(data_file=YAML_DATA_FILE).get_scenario("shoes_under_budget")

    authenticate(page, config=app_config)
    urls = searchItemsByNameUnderPrice(
        page,
        query=scenario["query"],
        maxPrice=scenario["maxPrice"],
        limit=scenario["limit"],
        config=app_config,
    )

    assert len(urls) == scenario["limit"]
    assert all(url.startswith("https://www.ebay.com/itm/") for url in urls)


@pytest.mark.e2e
@pytest.mark.data_driven
@pytest.mark.mock_store
def test_full_e2e_from_csv(
    page: Page,
    app_config: ConfigLoader,
    mock_ebay_store: None,
) -> None:
    scenario = DataLoader(data_file=CSV_DATA_FILE).get_scenario("shoes_under_budget")

    authenticate(page, config=app_config)
    urls = searchItemsByNameUnderPrice(
        page,
        query=scenario["query"],
        maxPrice=scenario["maxPrice"],
        limit=scenario["limit"],
        config=app_config,
    )

    assert len(urls) == scenario["limit"]
    addItemsToCart(page, urls, config=app_config)
    assertCartTotalNotExceeds(
        page,
        budgetPerItem=scenario["budgetPerItem"],
        itemsCount=len(urls),
        config=app_config,
    )


@pytest.mark.smoke
@pytest.mark.mock_store
def test_search_returns_urls_under_price(
    page: Page,
    app_config: ConfigLoader,
    mock_ebay_store: None,
) -> None:
    auth_service = AuthService(page, app_config)
    search_service = SearchService(page, app_config)

    auth_service.authenticate()
    urls = search_service.searchItemsByNameUnderPrice("shoes", 220, 5)

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
    cart_assertion_service = CartAssertionService(page, app_config)
    assert callable(cart_assertion_service.assertCartTotalNotExceeds)
    cart_assertion_service.assertCartTotalNotExceeds(budgetPerItem=220, itemsCount=0)
