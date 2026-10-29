"""Fixed WebFlow job values for Honda MG1 variants, in one place so a change touches one file."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WebFlowDefaults:
    ecu_generation: str = "MG1"
    delivery_type: str = "Plant Introduction"
    release_class: str = "Production"
    release_scope: str = "Program and Data"
    limitations: str = "NO"
    safety_monitoring: bool = True
    safety_calibration: bool = False
    calibration: bool = True
    data_integration: bool = True
    tp_level: str = "3"
    ecu_default_id: str = "FFFFEFFFFFEE00000000"
    ecu_rewriting_id: str = "00000000"
    security_coefficient: str = "FFFFFFFFFFFF"
    sw_version: str = "01"
    component_id: str = "-"
    indi_spec_template: str = "Honda_{hardware}{type}_IndiSpec_01"

    def general(self) -> dict:
        return {
            "delivery_type": self.delivery_type,
            "release_class": self.release_class,
            "release_scope": self.release_scope,
            "limitations": self.limitations,
            "safety_monitoring": self.safety_monitoring,
            "safety_calibration": self.safety_calibration,
            "calibration": self.calibration,
            "data_integration": self.data_integration,
        }

    def indi_spec(self, hardware: str) -> str:
        ecu_type = "_CS" if hardware.find("CS") != -1 else ""
        return self.indi_spec_template.format(hardware=hardware, type=ecu_type) if hardware else ""


WEBFLOW_DEFAULTS = WebFlowDefaults()
