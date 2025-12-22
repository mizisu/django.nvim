import inspect
import os
import re
import sys


def find_settings_module() -> str:
    if os.path.exists("manage.py"):
        with open("manage.py", "r") as f:
            lines = f.readlines()
            for line in lines:
                if "DJANGO_SETTINGS_MODULE" in line:
                    matches = re.findall(r'["\']([^"\']+)["\']', line)
                    if len(matches) >= 2:
                        return str(matches[1])
                    elif len(matches) == 1 and matches[0] != "DJANGO_SETTINGS_MODULE":
                        return str(matches[0])

    raise Exception("Could not find Django settings module")


def setup_django():
    import django  # pyright: ignore[reportMissingImports]

    manage_py_dir = os.getcwd()
    sys.path.insert(0, manage_py_dir)

    settings_module = os.environ.get("DJANGO_SETTINGS_MODULE")
    if not settings_module:
        settings_module = find_settings_module()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    django.setup()


def get_source_location(obj):
    try:
        file_path = inspect.getfile(obj)
        line_number = inspect.getsourcelines(obj)[1]
        return file_path, line_number
    except (TypeError, OSError):
        return None, 0
