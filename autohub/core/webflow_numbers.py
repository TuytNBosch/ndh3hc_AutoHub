"""Allocated WebFlow numbers and their existing Home/MG1 column keys."""

NUMBER_FIELDS = {
    "SoftwarePartNumber": ("AX", "software_part_number"),
    "ECRNumber": ("AW", "ecr_number"),
}


def number_updates(results: list[dict]) -> dict[str, dict[str, str]]:
    return {
        item["PartNumber"]: {
            column: str(item[name])
            for name, (column, _key) in NUMBER_FIELDS.items() if item.get(name)
        }
        for item in results if any(item.get(name) for name in NUMBER_FIELDS)
    }
