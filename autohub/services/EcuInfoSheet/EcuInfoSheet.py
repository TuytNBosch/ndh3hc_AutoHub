from autohub.services.common.sheet_grid import normalize
from autohub.services.common.workbook import ExcelDocument
from autohub.services.EcuInfoSheet.parser import SHEET_NAME, parse_ecu_info


class EcuInfoSheet(ExcelDocument):
    document_name = "ECU Info Sheet"

    def __init__(self, file_path: str, password: str = "hondabosch", quit: bool = False):
        super().__init__(file_path, password, quit)
        self.ecu_info = {"GeneralInfo": [], "Ecu": [], "Container": [], "Main": [], "Boot": []}

    def load_data(self) -> bool:
        info = self._parse(lambda name: normalize(name) == SHEET_NAME, parse_ecu_info)
        if info is None:
            return False
        self.ecu_info = info
        return True