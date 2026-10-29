<<<<<<< HEAD
# ndh3hc_AutoHub
Ngo Huu Dat
=======
# AutoHub

Windows desktop app (PySide6) that automates the ECU variant workflow: it reads
the Master Sheet, ECU Info Sheet and System Matrix Excel files, manages variant
rows in the Master Sheet, and creates and fills WebFlow jobs through browser
automation. Each feature is a module plugged into the main window sidebar.

## Features

### Main window

- Fixed-size window (1024x700) with a dark theme and dark title bar.
- Collapsible sidebar (220px to 56px icon-only) with the logo and Home / Creation / Comparison navigation.
- The window title shows the active module.
- Cross-module wiring: variants loaded on Home are passed to Creation automatically.
- On close, pages that hold resources (the WebFlow browser session) are shut down.
- Logging to `logs/autohub.log` and the console.
- User settings are persisted to `%APPDATA%/AutoHub/settings.json`: file paths, WebFlow config and selected variants.

### Home module

- Browse and remember the Master Sheet (`.xlsx`).
- **New variant**:
  - Prompts for the ECU Info Sheet CR and System Matrix CR.
  - Hover tooltip: "Create new variant by reading ECU Info Sheet CR and System Matrix CR."
  - Reads all three files through Excel COM automation on a background thread.
  - Computes variants that are not yet in the Master Sheet. Nothing is written at this step.
  - Fails with a clear message if the files are inconsistent, for example Main/Container/Boot counts that don't match, or a part number missing from the System Matrix.
- **Load variants**: reads the existing variant rows from the Master Sheet.
- **Editable variant table**:
  - Shows the Master Sheet request columns.
  - Cells can be edited in place.
  - "Update Master Sheet" is enabled only after a user edit.
- **Update Master Sheet**:
  - Rows loaded from the sheet are updated in place.
  - New rows are inserted from the variant template and stamped with the created date.
  - The table is then reloaded from the sheet.
- After Create/Load/Update, the WebFlow-ready variant list is sent to the Creation page.
- Results and errors are shown in message boxes. Button text shows progress.

### Creation module

- Variant checklist:
  - Fed from Home.
  - Filter by event, select all or clear.
  - The selection is persisted.
- WebFlow config form: Base URL, Edge driver path (browse), Tool version and Routing. Each field is saved on edit.
- **Create WebFlow jobs**:
  - Validation: at least one variant is selected, tool version and routing are filled, and all selected variants share the same ECU type.
  - Selenium (Edge) opens the WebFlow dashboard and creates one job per selected variant.
  - It then fills the General, ECU and Customer tabs and saves each job.
  - A summary of part number and job ID is shown on success.
  - The browser session is closed on error or app exit.

### Comparison module

- Placeholder page ("Coming soon").

## Project structure

Dependency rule: `modules` -> `core` <- `services`. Feature modules never import `services/`, and `services/`
never import Qt or `modules/`. `bootstrap.py` is the only place that names concrete classes. The rules are
enforced by `tests/test_architecture.py`; the design requirements are in
[docs/SOLID_REQUIREMENTS.md](docs/SOLID_REQUIREMENTS.md).

```
AutoHub/
├── main.py                       # entry point
├── requirements.txt
├── autohub/
│   ├── bootstrap.py              # composition root: builds services and the module list
│   ├── config.py                 # app name/version, paths
│   ├── core/                     # interfaces and shared, I/O-free code
│   │   ├── module_base.py        # AutoHubModule interface
│   │   ├── capabilities.py       # VariantSource / VariantSink / Closable protocols
│   │   ├── ports.py, records.py  # narrow service interfaces and typed data shapes
│   │   ├── variant_schema.py     # Master Sheet columns shown in the table
│   │   ├── normalizers.py        # pure text normalisers
│   │   ├── webflow_defaults.py   # fixed WebFlow job values
│   │   ├── dialogs.py            # file/message dialog port + Qt implementation
│   │   ├── com.py, workers.py    # COM session per thread, background tasks
│   │   └── settings.py           # SettingsStore protocol + JSON implementation
│   ├── ui/                       # main_window, sidebar, theme
│   ├── modules/
│   │   ├── home/                 # ui (layout), presenter (workflows), service, variant_table
│   │   │                         #   + table_clipboard / table_search / table_actions / frozen_columns
│   │   ├── creation/             # service, ui, variant_checklist, config_form
│   │   └── comparison/           # placeholder
│   ├── services/                 # I/O adapters (Excel COM, email/xlsx, Selenium)
│   │   ├── common/               # sheet_grid, header_rules, workbook
│   │   ├── MasterSheet/          # session | row_reader | row_writer | variant_builder | webflow_variants
│   │   ├── EcuInfoSheet/         # reader + header-rule parser
│   │   ├── SystemMatrix/         # reader + label-driven parser
│   │   ├── HWInfo/               # reader, parser and per-file-type sources (.xlsx/.eml/.msg)
│   │   └── WebFlow/              # legacy Selenium page objects (not refactored, see the requirements doc)
│   └── resources/                # icons, logo, banner
├── docs/SOLID_REQUIREMENTS.md
├── logs/
└── tests/                        # fakes.py holds the test doubles for Excel, Selenium and dialogs
```

## Requirements

- Windows with Microsoft Excel installed (COM automation through `pywin32`).
- Microsoft Edge and a matching Edge WebDriver (for WebFlow).
- Python packages: `PySide6`, `openpyxl`, `msoffcrypto-tool`, `pywin32`, `selenium`, `olefile`, `pytest`.

## Extending

- **New module:** create `autohub/modules/<name>/` with a Qt-free `service.py`, a `ui.py`, and a `module.py`
  (an `AutoHubModule` subclass whose constructor takes its factories). Add it to
  `autohub/bootstrap.py::build_modules()`.
- **New HW info file type:** write a class with `read(path, password) -> list[dict]` and register it in
  `autohub/services/HWInfo/sources.py::default_registry()`.
- **New ECU Info Sheet column:** add one `HeaderRule` to `HEADER_RULES` in
  `autohub/services/EcuInfoSheet/parser.py`.

## Run

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Test

```powershell
pytest
```
>>>>>>> b82647e (Initial commit)
