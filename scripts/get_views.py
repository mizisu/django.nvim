#!/usr/bin/env python3
import inspect
import json
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from django_utils import (  # pyright: ignore[reportMissingImports]  # noqa: E402
    get_source_location,
    setup_django,
)


def get_method_line_numbers(view_class):
    method_lines = {}
    try:
        source_lines, source_start_line = inspect.getsourcelines(view_class)

        http_methods = ["get", "post", "put", "patch", "delete", "head", "options"]

        for line_idx, line in enumerate(source_lines):
            stripped = line.strip()
            if stripped.startswith("def ") and "(" in stripped:
                method_name = stripped.split("(")[0].replace("def ", "")

                if method_name in http_methods:
                    method_lines[method_name] = source_start_line + line_idx

    except Exception:
        pass

    return method_lines


def get_action_line_numbers(view_class):
    action_lines = {}
    try:
        source_lines, source_start_line = inspect.getsourcelines(view_class)

        standard_actions = [
            "list",
            "create",
            "retrieve",
            "update",
            "partial_update",
            "destroy",
        ]

        for line_idx, line in enumerate(source_lines):
            stripped = line.strip()
            if stripped.startswith("def ") and "(" in stripped:
                method_name = stripped.split("(")[0].replace("def ", "")

                is_standard_action = method_name in standard_actions
                has_action_decorator = any(
                    "@action" in source_lines[i]
                    for i in range(max(0, line_idx - 3), line_idx)
                )

                if is_standard_action or has_action_decorator:
                    action_lines[method_name] = source_start_line + line_idx

    except Exception:
        pass

    return action_lines


def handle_viewset(url_pattern, full_pattern, view_class, callback):
    endpoints = []

    file_path, class_line = get_source_location(view_class)
    if not file_path:
        return endpoints

    actions = getattr(callback, "actions", {})

    for http_method, action_name in actions.items():
        line_number = class_line

        if hasattr(view_class, action_name):
            action_method = getattr(view_class, action_name)
            # Unwrap decorators to get the original function
            unwrapped_method = inspect.unwrap(action_method)
            try:
                method_file = inspect.getfile(unwrapped_method)
                source_lines, start_line = inspect.getsourcelines(unwrapped_method)
                # Find actual def line (skip decorators)
                method_line = start_line
                for i, line in enumerate(source_lines):
                    if line.strip().startswith("def "):
                        method_line = start_line + i
                        break
                # Only use method line if it's defined in the same file (not inherited)
                if method_line and method_file == file_path:
                    line_number = method_line
            except (TypeError, OSError):
                pass

        endpoints.append(
            {
                "pattern": full_pattern,
                "name": url_pattern.name or "",
                "view": f"{view_class.__module__}.{view_class.__name__}",
                "view_name": view_class.__name__,
                "view_display": f"{view_class.__name__}.{action_name}",
                "file": file_path,
                "line": line_number,
                "pos": [line_number, 0],
                "method": http_method,
                "action": action_name,
            }
        )

    return endpoints


def handle_apiview(url_pattern, full_pattern, view_class):
    endpoints = []

    file_path, class_line = get_source_location(view_class)
    if not file_path:
        return endpoints

    method_line_numbers = get_method_line_numbers(view_class)

    if method_line_numbers:
        for method_name, line_number in method_line_numbers.items():
            endpoints.append(
                {
                    "pattern": full_pattern,
                    "name": url_pattern.name or "",
                    "view": f"{view_class.__module__}.{view_class.__name__}",
                    "view_name": view_class.__name__,
                    "view_display": f"{view_class.__name__}.{method_name.upper()}",
                    "file": file_path,
                    "line": line_number,
                    "pos": [line_number, 0],
                    "method": method_name,
                }
            )
    else:
        endpoints.append(
            {
                "pattern": full_pattern,
                "name": url_pattern.name or "",
                "view": f"{view_class.__module__}.{view_class.__name__}",
                "view_name": view_class.__name__,
                "view_display": view_class.__name__,
                "file": file_path,
                "line": class_line,
                "pos": [class_line, 0],
            }
        )

    return endpoints


def handle_django_view(url_pattern, full_pattern, view_class):
    """Handle Django's built-in Class-Based Views (View, ListView, DetailView, etc.)"""
    endpoints = []

    file_path, class_line = get_source_location(view_class)
    if not file_path:
        return endpoints

    method_line_numbers = get_method_line_numbers(view_class)

    if method_line_numbers:
        for method_name, line_number in method_line_numbers.items():
            endpoints.append(
                {
                    "pattern": full_pattern,
                    "name": url_pattern.name or "",
                    "view": f"{view_class.__module__}.{view_class.__name__}",
                    "view_name": view_class.__name__,
                    "view_display": f"{view_class.__name__}.{method_name.upper()}",
                    "file": file_path,
                    "line": line_number,
                    "pos": [line_number, 0],
                    "method": method_name,
                }
            )
    else:
        endpoints.append(
            {
                "pattern": full_pattern,
                "name": url_pattern.name or "",
                "view": f"{view_class.__module__}.{view_class.__name__}",
                "view_name": view_class.__name__,
                "view_display": view_class.__name__,
                "file": file_path,
                "line": class_line,
                "pos": [class_line, 0],
            }
        )

    return endpoints


def handle_function_view(url_pattern, full_pattern, callback):
    file_path, line_number = get_source_location(callback)
    if not file_path:
        return []

    return [
        {
            "pattern": full_pattern,
            "name": url_pattern.name or "",
            "view": f"{callback.__module__}.{callback.__name__}",
            "view_name": callback.__name__,
            "view_display": callback.__name__,
            "file": file_path,
            "line": line_number,
            "pos": [line_number, 0],
        }
    ]


def extract_api_info(url_pattern, prefix):
    try:
        from rest_framework.viewsets import (  # pyright: ignore[reportMissingImports]
            ViewSetMixin,  # pyright: ignore[reportUnknownVariableType]
        )
    except ImportError:
        ViewSetMixin = None

    callback = url_pattern.callback
    if not callback:
        return []

    full_pattern = prefix + str(url_pattern.pattern)

    if hasattr(callback, "cls"):
        # DRF APIView, ViewSet
        view_class = callback.cls

        if ViewSetMixin and issubclass(view_class, ViewSetMixin):
            return handle_viewset(url_pattern, full_pattern, view_class, callback)
        else:
            return handle_apiview(url_pattern, full_pattern, view_class)
    elif hasattr(callback, "view_class"):
        # Django built-in CBV (View, ListView, DetailView, etc.)
        view_class = callback.view_class
        return handle_django_view(url_pattern, full_pattern, view_class)
    else:
        unwrapped_callback = inspect.unwrap(callback)
        return handle_function_view(url_pattern, full_pattern, unwrapped_callback)


def scan_urls(url_patterns, prefix=""):
    endpoints = []

    from django.urls.resolvers import (  # pyright: ignore[reportMissingImports, reportUnknownVariableType]
        URLPattern,  # pyright: ignore[reportUnknownVariableType]
        URLResolver,  # pyright: ignore[reportUnknownVariableType]
    )

    for pattern in url_patterns:
        if isinstance(pattern, URLResolver):
            new_prefix = prefix + str(pattern.pattern)
            endpoints.extend(scan_urls(pattern.url_patterns, new_prefix))
        elif isinstance(pattern, URLPattern):
            try:
                api_endpoints = extract_api_info(pattern, prefix)
                endpoints.extend(api_endpoints)
            except Exception:
                pass

    return endpoints


def main():
    try:
        setup_django()

        from django.urls import (  # pyright: ignore[reportMissingImports]
            get_resolver,  # pyright: ignore[reportMissingImports, reportUnknownVariableType]
        )

        resolver = get_resolver()
        endpoints = scan_urls(resolver.url_patterns)

        print(json.dumps(endpoints, indent=2))

    except Exception as e:
        error_data = {"error": str(e), "type": type(e).__name__}
        print(json.dumps(error_data), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
