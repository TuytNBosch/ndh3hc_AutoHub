from autohub.services.common.workbook import ExcelDocument
from autohub.services.SystemMatrix.parser import is_system_matrix_sheet, parse_system_matrix


class SystemMatrix(ExcelDocument):
    document_name = "System Matrix"

    def __init__(self, file_path: str, password: str = "hondabosch", quit: bool = False):
        super().__init__(file_path, password, quit)
        self.system_info = {"GeneralInfo": [], "FormB": [], "Setting": []}

    def load_data(self) -> bool:
        info = self._parse(is_system_matrix_sheet, parse_system_matrix)
        if info is None:
            return False
        self.system_info = info
        return True
