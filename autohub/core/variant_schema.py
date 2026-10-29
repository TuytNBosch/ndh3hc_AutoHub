"""Master Sheet request-row columns shared by the UI table and the sheet reader/writer (no I/O, no Qt)."""
from __future__ import annotations

from openpyxl.utils import get_column_letter

# Part Number (J) and Project Purpose (H) identify a row, so they lead the table; "C" (created date)
# is stamped fresh at write time, not editable. The rest is the sheet's "0. Create new Job" group
# onward: columns Q through CZ.
_IDENTITY_FIELD_LABELS: dict[str, str] = {
    "J": "Part Number",
    "H": "Project Purpose",
}
_CREATE_NEW_FIELD_LABELS: dict[str, str] = {
    "Q": "ECU Generation",
    "R": "Brand",
    "S": "ECU Type",
    "T": "Delivery Type",
    "U": "Release Class",
    "V": "Release Scope",
    "W": "Limitations",
    "X": "Safety Monitoring SW by RB",
    "Y": "Safety Calibration Responsibility",
    "Z": "Cal Data Responsibility",
    "AA": "Data Integration Responsibility",
    "AB": "Vehicle Model",
    "AC": "Power (kW)",
    "AD": "Immobilizer & Type",
    "AE": "Displacement",
    "AF": "Model Year",
    "AG": "Engine Family",
    "AH": "Emission Norm",
    "AI": "Transmission Type",
    "AJ": "Market",
    "AK": "Num. of Cylinder",
    "AL": "Proj No. (1st part)",
    "AM": "Proj No. (2nd part)",
    "AN": "HW Part Number",
    "AO": "Development No.",
    "AP": "ECU HW Name",
    "AQ": "Cust. Order No.",
    "AR": "Cust. HW Part No.",
    "AS": "Cust. SW Part No.",
    "AT": "Car Info",
    "AU": "Customer Name",
    "AV": "Lead Plant",
    "AW": "SW ECR Number",
    "AX": "Bosch SW Part No./Container No.",
    "AY": "Program Version (PVER)",
    "AZ": "Data Version (Cal Hex)",
    "BC": "Indi Spec",
    "BD": "Family Name",
    "BE": "FSWID Project Version",
    "BF": "FSWID Program Version",
    "BG": "TP Level",
    "BH": "ECU Default ID",
    "BI": "ECU Program ID (ASCII)",
    "CL": "ECU Program ID (Hex)",
    "CM": "ECU ReWrite ID",
    "CN": "SecuAcs_CustTypeI",
    "CO": "SecuAcs_Authen",
    "CP": "SecuAcs_CustTypeX",
    "CQ": "SW Version",
#    "CR": "Component ID",
    "CS": "DWG NO.",
    "CT": "ECU ID.",
    "CU": "CALIB ID.",
    "CV": "PROG ID BOOT",
#    "CW": "REVISION NO.",
    "CX": "CUST PART NO.",
    "CY": "EC/EU-MARK",
    "CZ": "SS-ID",
}
VARIANT_FIELD_LABELS: dict[str, str] = {**_IDENTITY_FIELD_LABELS, **_CREATE_NEW_FIELD_LABELS}
VARIANT_FIELD_ORDER: list[str] = list(VARIANT_FIELD_LABELS.keys())
