#!/usr/bin/env python3
"""Extract Django model fields, relations, and lookup data for completions."""

import json
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from django_utils import setup_django  # noqa: E402

# =============================================================================
# Lookup data
# =============================================================================

_BASE_LOOKUPS = ["exact", "isnull", "in"]

_NUMERIC_LOOKUPS = ["gt", "gte", "lt", "lte", "range"]

_STRING_LOOKUPS = [
    "iexact",
    "contains",
    "icontains",
    "startswith",
    "istartswith",
    "endswith",
    "iendswith",
    "regex",
    "iregex",
]

_DATE_LOOKUPS = [
    "year",
    "month",
    "day",
    "week",
    "week_day",
    "quarter",
    "iso_year",
    "iso_week_day",
]

_TIME_LOOKUPS = ["hour", "minute", "second"]

_DATETIME_LOOKUPS = _DATE_LOOKUPS + _TIME_LOOKUPS

_LOOKUP_BY_TYPE = {
    # Numeric fields
    "AutoField": _NUMERIC_LOOKUPS,
    "BigAutoField": _NUMERIC_LOOKUPS,
    "SmallAutoField": _NUMERIC_LOOKUPS,
    "IntegerField": _NUMERIC_LOOKUPS,
    "BigIntegerField": _NUMERIC_LOOKUPS,
    "SmallIntegerField": _NUMERIC_LOOKUPS,
    "PositiveIntegerField": _NUMERIC_LOOKUPS,
    "PositiveSmallIntegerField": _NUMERIC_LOOKUPS,
    "PositiveBigIntegerField": _NUMERIC_LOOKUPS,
    "FloatField": _NUMERIC_LOOKUPS,
    "DecimalField": _NUMERIC_LOOKUPS,
    # String fields
    "CharField": _STRING_LOOKUPS,
    "TextField": _STRING_LOOKUPS,
    "SlugField": _STRING_LOOKUPS,
    "EmailField": _STRING_LOOKUPS,
    "URLField": _STRING_LOOKUPS,
    # Boolean
    "BooleanField": [],
    # Date/Time fields
    "DateField": _NUMERIC_LOOKUPS + _DATE_LOOKUPS + ["date"],
    "DateTimeField": _NUMERIC_LOOKUPS + _DATETIME_LOOKUPS + ["date", "time"],
    "TimeField": _NUMERIC_LOOKUPS + _TIME_LOOKUPS,
    "DurationField": _NUMERIC_LOOKUPS,
    # Special fields
    "JSONField": ["contains", "contained_by", "has_key", "has_keys", "has_any_keys"],
    "UUIDField": ["iexact"] + _NUMERIC_LOOKUPS,
    # File fields
    "FileField": _STRING_LOOKUPS,
    "ImageField": _STRING_LOOKUPS,
    "FilePathField": _STRING_LOOKUPS,
    # Binary
    "BinaryField": [],
    # IP fields
    "IPAddressField": _STRING_LOOKUPS,
    "GenericIPAddressField": _STRING_LOOKUPS,
    # Relation fields (traversal only)
    "ForeignKey": [],
    "OneToOneField": [],
    "ManyToManyField": [],
}

_LOOKUP_METADATA = {
    "exact": {"description": "Exact match", "sql": "WHERE {field} = {value}"},
    "iexact": {
        "description": "Case-insensitive exact match",
        "sql": "WHERE UPPER({field}) = UPPER({value})",
    },
    "contains": {
        "description": "Case-sensitive containment test",
        "sql": "WHERE {field} LIKE '%{value}%'",
    },
    "icontains": {
        "description": "Case-insensitive containment test",
        "sql": "WHERE UPPER({field}) LIKE UPPER('%{value}%')",
    },
    "startswith": {
        "description": "Case-sensitive starts-with",
        "sql": "WHERE {field} LIKE '{value}%'",
    },
    "istartswith": {
        "description": "Case-insensitive starts-with",
        "sql": "WHERE UPPER({field}) LIKE UPPER('{value}%')",
    },
    "endswith": {
        "description": "Case-sensitive ends-with",
        "sql": "WHERE {field} LIKE '%{value}'",
    },
    "iendswith": {
        "description": "Case-insensitive ends-with",
        "sql": "WHERE UPPER({field}) LIKE UPPER('%{value}')",
    },
    "gt": {"description": "Greater than", "sql": "WHERE {field} > {value}"},
    "gte": {
        "description": "Greater than or equal to",
        "sql": "WHERE {field} >= {value}",
    },
    "lt": {"description": "Less than", "sql": "WHERE {field} < {value}"},
    "lte": {
        "description": "Less than or equal to",
        "sql": "WHERE {field} <= {value}",
    },
    "isnull": {
        "description": "Check if field is NULL or not",
        "sql": "WHERE {field} IS NULL",
    },
    "range": {
        "description": "Range test (inclusive)",
        "sql": "WHERE {field} BETWEEN {start} AND {end}",
    },
    "in": {
        "description": "Check if value is in list",
        "sql": "WHERE {field} IN ({values})",
    },
    "regex": {
        "description": "Case-sensitive regular expression match",
        "sql": "WHERE {field} ~ '{pattern}'",
    },
    "iregex": {
        "description": "Case-insensitive regular expression match",
        "sql": "WHERE {field} ~* '{pattern}'",
    },
    # Date/Time transforms
    "year": {
        "description": "Extract year from date/datetime field",
        "sql": "WHERE EXTRACT(YEAR FROM {field}) = {value}",
    },
    "month": {
        "description": "Extract month from date/datetime field",
        "sql": "WHERE EXTRACT(MONTH FROM {field}) = {value}",
    },
    "day": {
        "description": "Extract day from date/datetime field",
        "sql": "WHERE EXTRACT(DAY FROM {field}) = {value}",
    },
    "week": {
        "description": "Extract ISO week number",
        "sql": "WHERE EXTRACT(WEEK FROM {field}) = {value}",
    },
    "week_day": {
        "description": "Day of week (1=Sunday, 7=Saturday)",
        "sql": "WHERE EXTRACT(DOW FROM {field}) = {value}",
    },
    "quarter": {
        "description": "Extract quarter (1-4)",
        "sql": "WHERE EXTRACT(QUARTER FROM {field}) = {value}",
    },
    "hour": {
        "description": "Extract hour from time/datetime field",
        "sql": "WHERE EXTRACT(HOUR FROM {field}) = {value}",
    },
    "minute": {
        "description": "Extract minute from time/datetime field",
        "sql": "WHERE EXTRACT(MINUTE FROM {field}) = {value}",
    },
    "second": {
        "description": "Extract second from time/datetime field",
        "sql": "WHERE EXTRACT(SECOND FROM {field}) = {value}",
    },
    "date": {
        "description": "Cast datetime to date",
        "sql": "WHERE DATE({field}) = {value}",
    },
    "time": {
        "description": "Extract time from datetime field",
        "sql": "WHERE TIME({field}) = {value}",
    },
    "iso_year": {
        "description": "Extract ISO year",
        "sql": "WHERE EXTRACT(ISOYEAR FROM {field}) = {value}",
    },
    "iso_week_day": {
        "description": "ISO day of week (1=Monday, 7=Sunday)",
        "sql": "WHERE EXTRACT(ISODOW FROM {field}) = {value}",
    },
    # JSON lookups
    "has_key": {
        "description": "Check if JSON has a specific key at top level",
        "sql": "WHERE {field} ? '{key}'",
    },
    "has_keys": {
        "description": "Check if JSON has all specified keys",
        "sql": "WHERE {field} ?& ARRAY['{keys}']",
    },
    "has_any_keys": {
        "description": "Check if JSON has any of the specified keys",
        "sql": "WHERE {field} ?| ARRAY['{keys}']",
    },
    "contained_by": {
        "description": "Check if JSON is contained by another JSON",
        "sql": "WHERE {field} <@ '{json}'",
    },
}

# =============================================================================
# Model metadata extraction
# =============================================================================


class DjangoJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles Django lazy objects."""

    def default(self, obj):
        try:
            from django.utils.functional import Promise

            if isinstance(obj, Promise):
                return str(obj)
        except ImportError:
            pass

        try:
            return str(obj)
        except Exception:
            return super().default(obj)


def _get_field_definition(field):
    """Return field definition as string. e.g. title = models.CharField(max_length=200)"""
    field_name = field.name
    field_class = field.__class__.__name__
    params = []

    name, path, args, kwargs = field.deconstruct()

    for arg in args:
        if hasattr(arg, "_meta"):
            params.append(arg.__name__)
        else:
            params.append(repr(arg))

    important_kwargs = [
        "max_length",
        "null",
        "blank",
        "default",
        "unique",
        "choices",
        "related_name",
        "on_delete",
        "db_index",
        "help_text",
        "verbose_name",
        "upload_to",
        "max_digits",
        "decimal_places",
        "auto_now",
        "auto_now_add",
        "primary_key",
    ]

    for key in important_kwargs:
        if key not in kwargs:
            continue

        value = kwargs[key]

        if key == "on_delete":
            params.append(f"on_delete=models.{value.__name__}")
        elif key == "default":
            if callable(value):
                params.append(f"default={value.__name__}")
            else:
                params.append(f"default={repr(value)}")
        elif key == "help_text":
            help_str = str(value)
            if len(help_str) > 60:
                help_str = help_str[:57] + "..."
            params.append(f"help_text={repr(help_str)}")
        elif key == "choices" and hasattr(field, "choices"):
            choices_class = _find_choices_class(field)
            if choices_class:
                params.append(f"choices={choices_class.__name__}.choices")
            else:
                params.append("choices=...")
        else:
            params.append(f"{key}={repr(value)}")

    return f"{field_name} = models.{field_class}({', '.join(params)})"


def _find_choices_class(field):
    """Find the Choices class used by a field."""
    if not hasattr(field, "choices") or not field.choices:
        return None

    model_class = field.model

    search_spaces = [
        model_class,
        sys.modules.get(model_class.__module__),
    ]

    for space in search_spaces:
        if space is None:
            continue

        for attr_name in dir(space):
            try:
                attr = getattr(space, attr_name, None)
                if attr is None:
                    continue

                from django.db import models

                if isinstance(attr, type) and issubclass(attr, models.Choices):
                    if hasattr(attr, "choices") and field.choices == attr.choices:
                        return attr
            except (TypeError, AttributeError):
                continue

    return None


def _get_choices_info(field):
    """Extract choices information from a field."""
    if not hasattr(field, "choices") or not field.choices:
        return None

    choices_info: dict = {"values": []}

    choices_class = _find_choices_class(field)
    if choices_class:
        choices_info["class"] = choices_class.__name__

        from django.db import models

        if issubclass(choices_class, models.TextChoices):
            choices_info["type"] = "TextChoices"
        elif issubclass(choices_class, models.IntegerChoices):
            choices_info["type"] = "IntegerChoices"

    for choice_value, choice_label in field.choices:
        choices_info["values"].append(
            {"value": choice_value, "label": str(choice_label)}
        )

    return choices_info


def _get_field_metadata(field):
    """Extract metadata for a regular field."""
    from django.db.models.fields.related import RelatedField

    field_type = field.__class__.__name__
    metadata = {
        "type": field_type,
        "definition": _get_field_definition(field),
    }

    if hasattr(field, "max_length") and field.max_length:
        metadata["max_length"] = field.max_length

    if hasattr(field, "null"):
        metadata["null"] = field.null

    if hasattr(field, "blank"):
        metadata["blank"] = field.blank

    choices_info = _get_choices_info(field)
    if choices_info:
        metadata["choices"] = choices_info

    if isinstance(field, RelatedField):
        related_model = field.related_model
        metadata["related_model"] = related_model.__name__
        metadata["related_app"] = related_model._meta.app_label
        metadata["traversable"] = True

        if hasattr(field, "related_query_name"):
            metadata["related_query_name"] = field.related_query_name()

    return metadata


def _get_reverse_relation_metadata(field):
    """Extract metadata for a reverse relation field."""
    from django.db.models.fields.reverse_related import OneToOneRel

    related_model = field.related_model
    related_field = field.field
    field_name = field.name

    reverse_name = field_name
    if hasattr(related_field, "remote_field") and related_field.remote_field:
        related_name_attr = related_field.remote_field.related_name
        if related_name_attr:
            reverse_name = related_name_attr
        else:
            if isinstance(field, OneToOneRel):
                reverse_name = related_model._meta.model_name
            else:
                reverse_name = f"{related_model._meta.model_name}_set"

    metadata = {
        "type": field.__class__.__name__,
        "related_model": related_model.__name__,
        "related_app": related_model._meta.app_label,
        "related_field": related_field.name,
        "reverse_name": reverse_name,
        "traversable": True,
    }

    try:
        metadata["definition"] = _get_field_definition(related_field)
    except Exception:
        metadata["definition"] = None

    return metadata


def get_completion_data():
    """Return all Django model fields and relations with lookup data."""
    from django.apps import apps
    from django.db.models.fields.related import (
        ForeignKey,
        ManyToManyField,
        OneToOneField,
    )
    from django.db.models.fields.reverse_related import (
        ManyToManyRel,
        ManyToOneRel,
        OneToOneRel,
    )

    models_data = {}

    for model in apps.get_models():
        app_label = model._meta.app_label
        model_name = model.__name__

        fields = {}

        for field in model._meta.get_fields():
            field_name = field.name

            is_concrete = getattr(field, "concrete", False)
            is_m2m = getattr(field, "many_to_many", False)
            is_relation_field = isinstance(
                field, (ForeignKey, OneToOneField, ManyToManyField)
            )

            if (is_concrete and not is_m2m) or is_relation_field:
                fields[field_name] = _get_field_metadata(field)

                # Add _id field for ForeignKey and OneToOneField
                if isinstance(field, (ForeignKey, OneToOneField)):
                    id_field_name = field_name + "_id"
                    # Get the actual column type from the target field's pk
                    related_pk = field.related_model._meta.pk
                    pk_type = (
                        related_pk.__class__.__name__ if related_pk else "IntegerField"
                    )
                    fields[id_field_name] = {
                        "type": pk_type,
                        "definition": f"{id_field_name} = models.{pk_type}()  # → {field.related_model.__name__}.pk",
                        "null": field.null,
                        "blank": field.blank,
                    }
            elif isinstance(field, (ManyToOneRel, ManyToManyRel, OneToOneRel)):
                fields[field_name] = _get_reverse_relation_metadata(field)

        models_data[model_name] = {
            "app_label": app_label,
            "module": model.__module__,
            "fields": fields,
        }

    return {
        "models": models_data,
        "lookups": {
            "base": _BASE_LOOKUPS,
            "by_type": _LOOKUP_BY_TYPE,
            "metadata": _LOOKUP_METADATA,
        },
    }


def main():
    try:
        setup_django()
        result = get_completion_data()
        print(json.dumps(result, indent=2, cls=DjangoJSONEncoder))

    except Exception as e:
        import traceback

        error_result = {
            "error": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc(),
        }
        print(json.dumps(error_result, cls=DjangoJSONEncoder), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
