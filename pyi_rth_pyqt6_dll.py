"""
PyInstaller runtime hook to fix PyQt6 DLL loading in frozen apps.
This hook runs BEFORE any application code, ensuring Qt6 DLLs
are findable by the Windows DLL loader.
"""
import os
import sys

if sys.platform == 'win32' and hasattr(sys, '_MEIPASS'):
    _meipass = sys._MEIPASS

    # Add _MEIPASS itself as a DLL directory
    try:
        os.add_dll_directory(_meipass)
    except (OSError, AttributeError):
        pass

    # Add PyQt6/Qt6/bin which contains all Qt6*.dll files
    _qt_bin = os.path.join(_meipass, 'PyQt6', 'Qt6', 'bin')
    if os.path.isdir(_qt_bin):
        try:
            os.add_dll_directory(_qt_bin)
        except (OSError, AttributeError):
            pass

    # Also prepend to PATH as fallback for older Windows / edge cases
    _path = os.environ.get('PATH', '')
    _new_dirs = _meipass
    if os.path.isdir(_qt_bin):
        _new_dirs = _qt_bin + os.pathsep + _new_dirs
    os.environ['PATH'] = _new_dirs + os.pathsep + _path

    # Set QT_PLUGIN_PATH so Qt can find platform plugins
    _qt_plugins = os.path.join(_meipass, 'PyQt6', 'Qt6', 'plugins')
    if os.path.isdir(_qt_plugins):
        os.environ['QT_PLUGIN_PATH'] = _qt_plugins
