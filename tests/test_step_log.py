import logging

import pytest

from autohub.services.WebFlow.step_log import run_step, run_steps

LOG = logging.getLogger("steplog-test")


def test_each_step_is_logged_with_its_outcome(caplog):
    caplog.set_level(logging.INFO, logger="steplog-test")
    assert run_step(LOG, "pick", lambda value: value == 1, 1) is True
    assert run_step(LOG, "bad", lambda: False) is False
    text = [(r.levelname, r.getMessage()) for r in caplog.records]
    assert ("INFO", "Step: pick") in text
    assert any(level == "INFO" and m.startswith("Step OK: pick") for level, m in text)
    assert any(level == "WARNING" and m.startswith("Step FAILED: bad") for level, m in text)


def test_run_steps_runs_all_and_names_the_failures():
    ran = []
    steps = [
        ("a", lambda: ran.append("a") or True),
        ("b", lambda: ran.append("b") or False),
        ("c", lambda value: ran.append(value) or True, "c"),
    ]
    assert run_steps(LOG, steps) == ["b"]
    assert ran == ["a", "b", "c"]


def test_an_exception_is_logged_and_reraised(caplog):
    def boom():
        raise ValueError("x")

    with pytest.raises(ValueError):
        run_step(LOG, "boom", boom)
    assert any(r.levelname == "ERROR" and "boom" in r.getMessage() for r in caplog.records)


def test_job_number_reads_the_id_at_the_end_of_the_url():
    from autohub.core.webflow_links import job_number

    assert job_number("https://h:8881/app/ShowJob/16406") == 16406
    assert job_number("https://h:8881/app/ShowJob/16406/") == 16406
    assert job_number("https://h:8881/app/newJob") is None
