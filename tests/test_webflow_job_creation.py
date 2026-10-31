from unittest.mock import Mock

import pytest
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException

from autohub.services.WebFlow import Constants
from autohub.services.WebFlow.JobCreation import JobCreation


@pytest.fixture
def driver():
    driver = Mock(current_url="https://webflow/app/ShowJob/16409")
    driver.find_element.return_value.is_displayed.return_value = True
    driver.find_element.return_value.is_enabled.return_value = True
    return driver


def test_confirm_relocates_button_after_stale_click(driver):
    stale = Mock()
    stale.is_displayed.return_value = True
    stale.click.side_effect = StaleElementReferenceException()
    fresh = Mock()
    fresh.is_displayed.return_value = True
    driver.find_element.side_effect = [stale, fresh]

    assert JobCreation(driver)._confirm_creation()
    assert driver.find_element.call_count == 2
    stale.click.assert_called_once()
    fresh.click.assert_called_once()


def test_successful_confirmation_is_not_repeated(driver):
    button = driver.find_element.return_value
    assert JobCreation(driver)._confirm_creation()
    button.click.assert_called_once()


def test_confirm_waits_for_enabled_button(driver):
    button = driver.find_element.return_value
    button.is_enabled.side_effect = [False, True]

    assert JobCreation(driver)._confirm_creation()
    assert driver.find_element.call_count == 2
    button.click.assert_called_once()


def test_uncertain_submission_is_not_retried(driver):
    button = driver.find_element.return_value
    button.click.side_effect = WebDriverException("connection lost")

    with pytest.raises(WebDriverException, match="connection lost"):
        JobCreation(driver)._confirm_creation()
    button.click.assert_called_once()


def test_permanently_stale_confirm_times_out(driver, monkeypatch):
    monkeypatch.setattr(Constants, "BODY_TIMEOUT", 0)
    driver.find_element.side_effect = StaleElementReferenceException()

    assert JobCreation(driver)._confirm_creation() is False


def test_completion_relocates_replaced_activity_indicator(driver):
    stale = Mock()
    stale.is_displayed.side_effect = StaleElementReferenceException()
    driver.find_elements.side_effect = [[stale], []]

    assert JobCreation(driver)._wait_until_jobs_created()
    assert driver.find_elements.call_count == 2


def test_completion_timeout_does_not_confirm_again(driver, monkeypatch):
    monkeypatch.setattr(Constants, "WEBFLOW_TIMEOUT", 0)
    driver.find_elements.return_value = [Mock()]

    assert JobCreation(driver)._wait_until_jobs_created() is False
    driver.find_element.assert_not_called()


def prepared_creation(driver):
    creation = JobCreation(driver)
    for name in (
        "select_ecu_generation", "select_brand", "select_ecu_type",
        "select_customer_group", "select_working_mode", "select_tool_version",
        "select_routing", "select_number_of_jobs", "_confirm_creation",
        "_wait_until_jobs_created",
    ):
        setattr(creation, name, Mock(return_value=True))
    return creation


def create_jobs(creation):
    return creation.jobs_creation("MG1", "MG1CS022", "Productive", "Honda", 2)


def test_failed_form_selection_does_not_submit_jobs(driver):
    creation = prepared_creation(driver)
    creation.select_routing.return_value = False

    assert create_jobs(creation) is False
    creation.select_number_of_jobs.assert_not_called()
    creation._confirm_creation.assert_not_called()
    creation._wait_until_jobs_created.assert_not_called()


def test_failed_confirm_does_not_wait_or_publish_job_ids(driver):
    creation = prepared_creation(driver)
    creation._confirm_creation.return_value = False

    assert create_jobs(creation) is False
    creation._wait_until_jobs_created.assert_not_called()
    assert creation.get_new_jobs_ids() == []


def test_repeated_creation_does_not_reuse_old_job_ids(driver):
    creation = prepared_creation(driver)
    assert create_jobs(creation)
    assert creation.get_new_jobs_ids() == ["16409", "16410"]

    driver.current_url = "https://webflow/app/ShowJob/16411"
    assert create_jobs(creation)
    assert creation.get_new_jobs_ids() == ["16411", "16412"]
    assert creation.get_number_of_jobs() == 2
    assert creation._confirm_creation.call_count == 2
