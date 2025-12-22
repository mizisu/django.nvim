#!/usr/bin/env python3
import json
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from django_utils import (  # pyright: ignore[reportMissingImports]  # noqa: E402
    get_source_location,
    setup_django,
)


def get_model_info(model):
    file_path, line_number = get_source_location(model)
    if not file_path:
        return None

    field_count = len(model._meta.get_fields())

    return {
        "name": model.__name__,
        "app_label": model._meta.app_label,
        "db_table": model._meta.db_table,
        "field_count": field_count,
        "file": file_path,
        "line": line_number,
        "pos": [line_number, 0],
        "module": model.__module__,
    }


def main():
    try:
        setup_django()

        from django.apps import apps  # pyright: ignore[reportMissingImports]

        models = []
        for model in apps.get_models():
            model_info = get_model_info(model)
            if model_info:
                models.append(model_info)

        models.sort(key=lambda x: (x["app_label"], x["name"]))

        print(json.dumps(models, indent=2))

    except Exception as e:
        error_data = {"error": str(e), "type": type(e).__name__}
        print(json.dumps(error_data), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
