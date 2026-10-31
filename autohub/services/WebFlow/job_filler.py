"""Execute a job-fill plan, enforcing existing failure and allocation policies."""
from __future__ import annotations

import logging
from typing import Any
from .job_plan import JobPlan, StepPlan, describe_values
from .job_plan import ECU_FIELDS as ECU_FIELDS, CUSTOMER_FIELDS as CUSTOMER_FIELDS, GENERAL_FIELDS as GENERAL_FIELDS
from .job_plan import display_value as display_value
from .step_log import Step, run_step, run_steps

_logger = logging.getLogger(__name__)

class JobFiller:
    """Depends only on the page objects it is given (``side_menu_bar`` and ``body``)."""

    def __init__(self, side_menu_bar: Any, body: Any, plan: StepPlan | None = None):
        self.side_menu_bar = side_menu_bar
        self.body = body
        self.plan = plan if plan is not None else JobPlan(side_menu_bar, body)

    def steps(self, variant: dict) -> list[Step]:
        """The steps that fill the General, ECU and Customer tabs of the open job and save it."""
        return self.plan.steps(variant)

    def fill(self, variant: dict) -> list[str]:
        """Fills and saves the open job; returns warnings for requested values not applied.

        Raises RuntimeError naming every failed step."""
        part_number = variant["part_number"]
        variant.pop("imported_software_part_number", None)
        variant.pop("imported_ecr_number", None)
        general = self.body.tab.generaltab
        general.skipped_fields.clear()
        _logger.info("[%s] Values to fill: %s", part_number, describe_values(variant))
        if not run_step(_logger, f"[{part_number}] Select the General tab", general.select_general_tab):
            raise RuntimeError("Could not select the General tab.")

        steps = self.steps(variant)
        if variant.get("ecr"):
            for step in steps:
                if not run_step(_logger, f"[{part_number}] {step[0]}", step[1], *step[2:]):
                    raise RuntimeError(f"Could not fill {part_number}: {step[0]}.")
                if step[0] == "General: ECR Import":
                    variant["imported_ecr_number"] = general.imported_ecr_number
                if step[0] == "General: Import software part number from pool":
                    variant["imported_software_part_number"] = general.imported_software_part_number
            return list(general.skipped_fields)
        picker_index = next(
            (index for index, step in enumerate(steps) if step[0].startswith("General: Pick PST_Lib")),
            None,
        )
        if picker_index is None:
            failed = run_steps(
                _logger, [(f"[{part_number}] {step[0]}", *step[1:]) for step in steps]
            )
        else:
            failed = run_steps(
                _logger,
                [(f"[{part_number}] {step[0]}", *step[1:]) for step in steps[:picker_index]],
            )
            picker = steps[picker_index]
            if not run_step(_logger, f"[{part_number}] {picker[0]}", picker[1], *picker[2:]):
                raise RuntimeError(
                    f"Could not select a PST_Lib entry matching PVER {picker[2]!r} for {part_number}."
                )
            failed += run_steps(
                _logger,
                [(f"[{part_number}] {step[0]}", *step[1:]) for step in steps[picker_index + 1:]],
            )
        if variant.get("hardware", {}).get("lead_plant") and general.imported_software_part_number:
            variant["imported_software_part_number"] = general.imported_software_part_number
        if failed:
            raise RuntimeError(f"Could not fill all values for {part_number}. Failed: {'; '.join(failed)}")
        return list(general.skipped_fields)
