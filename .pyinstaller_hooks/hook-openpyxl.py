# PyInstaller hook for openpyxl
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all openpyxl submodules
hiddenimports = collect_submodules('openpyxl')

# Collect data files (for templates, etc.)
datas = collect_data_files('openpyxl')
