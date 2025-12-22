# Agent Guidelines for django.nvim

**Always response in Korean.**

## Project Overview

Neovim plugin for Django development written in Lua (plugin) with Python scripts for Django introspection.

## Build/Test Commands

- No formal test suite or build process - this is a Neovim plugin
- Test manually: Open Neovim in project root with `:DjangoViews` or `:DjangoModels`
- Python scripts: Run with `DJANGO_SETTINGS_MODULE=project.settings uv run python scripts/<script_name>.py`
  - Example: `DJANGO_SETTINGS_MODULE=project.settings uv run python scripts/get_model_field_relations.py`
- Django test project included in `project/` directory for testing

### Unit Tests

Unit tests can run without Neovim:

```bash
# Test parse_filter_context() function
nvim --headless --noplugin -u NONE -l test_parse.lua
```

### Manual Integration Testing

Integration testing in a real Django project:

#### 1. Project Setup

```bash
# Activate Python environment
source .venv/bin/activate

# Verify Django server can run
python manage.py check
```

#### 2. Neovim Configuration

Verify plugin is configured in `init.lua` or lazy.nvim setup:

```lua
{
  "mizisu/django.nvim",
  dependencies = {
    "folke/snacks.nvim",
    {
      "saghen/blink.cmp",
      opts = {
        sources = {
          default = { "django" },
          providers = {
            django = {
              name = "Django",
              module = "django.features.completions.blink",
              async = true,
            },
          },
        },
      },
    },
  },
}
```

#### 3. Test Scenarios

Open a Python file in the project (e.g., `project/blog/views.py`):

**Scenario 1: Basic Field Completion**
```python
from blog.models import Post

def test_view(request):
    # Place cursor after ( and trigger autocomplete
    posts = Post.objects.filter(
    #                           ^ Press Ctrl+Space here
```

**Expected Results:**
- `title` (CharField)
- `title__` (for lookup operators)
- `author__` (ForeignKey traversal)
- `published_date` (DateTimeField)
- Lookup operators for each field (`title__exact`, `title__icontains`, etc.)

**Scenario 2: Relationship Traversal**
```python
posts = Post.objects.filter(author__
#                                   ^ Autocomplete here
```

**Expected Results:**
- `username` (User model field)
- `email` (User model field)
- Related lookup operators

**Scenario 3: Lookup Operators**
```python
posts = Post.objects.filter(title__
#                                  ^ Autocomplete here
```

**Expected Results:**
- `exact` (exact match)
- `iexact` (case-insensitive match)
- `contains` (contains)
- `icontains` (case-insensitive contains)
- Documentation shows SQL templates for each item

**Scenario 4: Partial Typing**
```python
posts = Post.objects.filter(tit
#                              ^ Autocomplete here
```

**Expected Results:**
- Only completion items starting with `title` shown

**Scenario 5: Multiple Filter Arguments**
```python
posts = Post.objects.filter(status='published', 
#                                              ^ Autocomplete here
```

**Expected Results:**
- New field completions (same as first scenario)

#### 4. Debugging

If autocomplete doesn't work:

1. **Check LSP Type Information:**
```python
# Place cursor on Post.objects and hover (K)
Post.objects.filter()
#    ^ Should show QuerySet[Post] type
```

2. **Run Python Script Directly:**
```bash
cd /path/to/django.nvim
source .venv/bin/activate
DJANGO_SETTINGS_MODULE=project.settings python scripts/get_model_field_relations.py | python -m json.tool | head -n 100
```

3. **Check Neovim Logs:**
```vim
:messages
```

4. **Clear Cache:**
```vim
:DjangoClearAllCache
```

### Expected Output Structure

Python scripts should output JSON in this structure:

```json
{
  "models": {
    "Post": {
      "app_label": "blog",
      "fields": {
        "title": {
          "type": "CharField",
          "definition": "models.CharField(max_length=200)",
          "null": false,
          "blank": false,
          "max_length": 200
        },
        "author": {
          "type": "ForeignKey",
          "definition": "models.ForeignKey(User, on_delete=models.CASCADE)",
          "null": false,
          "blank": false,
          "related_model": "User",
          "related_app": "auth",
          "traversable": true,
          "related_query_name": "post_set"
        }
      }
    }
  },
  "lookup_map": {
    "CharField": ["exact", "iexact", "contains", "icontains", ...],
    "DateTimeField": ["exact", "gt", "gte", "lt", "lte", ...]
  },
  "base_lookups": ["exact", "isnull", "in"],
  "lookup_metadata": {
    "exact": {
      "description": "Exact match",
      "sql_template": "WHERE column = %s"
    },
    ...
  }
}
```

## Code Style

### Lua (Plugin Code)

- Use tabs for indentation
- Local module pattern: `local M = {}` and `return M`
- No trailing newlines in files
- Function naming: snake_case (e.g., `get_python_path()`, `is_django_project()`)
- Variable naming: snake_case (e.g., `cache_dir`, `manage_py`)
- Private methods: prefix with `__` and declare on `M` table (e.g., `function M.__internal_helper()`)
- Method order: public methods at top, private methods at bottom based on dependency order
- Use `vim.fn`, `vim.api`, `vim.bo` namespaces - no deprecated `vim.fn.*` calls
- Prefer `pcall()` for optional dependencies
- Comments: use `--` for single line

Example module structure:
```lua
local M = {}

-- Public method at top
function M.public_method()
	return M.__private_helper()
end

-- Private methods at bottom (prefixed with __)
function M.__private_helper()
	return "result"
end

return M
```

### Python (Django Scripts)

- Python 3.12+ required
- Type checking: Pyright in basic mode
- Use `# noqa: E402` for module-level imports after path manipulation
- Error handling: JSON output to stdout/stderr with structured error data
- Functions should return structured data (dicts/lists), not print directly

## Feature Specifications

### Filter Completions

**Purpose:** Implement autocomplete for Django QuerySet methods: `filter`, `select_related`, `prefetch_related`, `values`, `annotate`, etc.

**Implementation Approach:**

1. Collect all model field information using `get_model_field_relations.py`
2. Collect information to represent various field formats
3. Support autocomplete for both forward and reverse relations
4. Load completions dynamically based on current input (not all at once)
5. Prioritize reusable implementation patterns

**Blink Completion Item Examples:**

1. **Basic Field**
   Example: `Post.objects.filter(title=`
   ```lua
   {
     label = "title",
     detail = "CharField",
     documentation = {
       kind = "markdown",
       value = [[
   ```python
   class Post:
       title = models.CharField(max_length=200)
   ```
   ]]
     }
   }
   ```

2. **Lookup Operator**
   Example: `Post.objects.filter(title=`
   ```lua
   {
     label = "title__icontains",
     detail = "CharField",
     documentation = {
       kind = "markdown",
       value = [[
   ```python
   class Post:
       title = models.CharField(max_length=200)
   ```
   
   Lookup: icontains
   Case-insensitive containment test
   
   SQL equivalent:
   ```sql
   WHERE UPPER(title) LIKE UPPER('%value%')
   ```
   ]]
     }
   }
   ```

3. **Related Model Field**
   Example: `Post.objects.filter(author__username=`
   ```lua
   {
     label = "author__username",
     detail = "CharField",
     documentation = {
       kind = "markdown",
       value = [[
   ```python
   class User:
       username = models.CharField(max_length=150, unique=True)
   ```
   ]]
     }
   }
   ```

4. **Related Model Field Lookup**
   Example: `Post.objects.filter(author__username__iexact=`
   ```lua
   {
     label = "author__username__iexact",
     detail = "CharField",
     documentation = {
       kind = "markdown",
       value = [[
   ```python
   class User:
       username = models.CharField(max_length=150, unique=True)
   ```
   
   Lookup: iexact
   Case-insensitive exact match
   
   SQL equivalent:
   ```sql
   WHERE UPPER(user.username) = UPPER('value')
   ```
   ]]
     }
   }
   ```

5. **Choice Field**
   Example: `Post.objects.filter(status=`
   ```lua
   {
     label = "status",
     detail = "CharField",
     documentation = {
       kind = "markdown",
       value = [[
   ```python
   class Post:    
       status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
   ```
   
   Available choices:
   - 'draft' - Draft
   - 'published' - Published
   - 'archived' - Archived
   ]]
     }
   }
   ```

6. **Reverse Relation**
   Example: `Post.objects.filter(comments=`
   ```lua
   {
     label = "comments",
     detail = "ManyToOneRel",
     documentation = {
       kind = "markdown",
       value = [[
   ```python
   class Comment:
       field1 = models.SomeField(...)
       field2 = models.SomeField(...)
       field3 = models.SomeField(...)
       all fields...
   ```
   ]]
     }
   }
   ```

7. **Reverse Relation Field**
   Example: `Post.objects.filter(comments__content=`
   ```lua
   {
     label = "comments__content",
     detail = "TextField",
     documentation = {
       kind = "markdown",
       value = [[
   ```python
   class Comment:
       content = models.TextField(...)
   ```
   ]]
     }
   }
   ```

## Known Issues

- Autocomplete won't work if LSP doesn't provide `QuerySet[ModelName]` type
  - Solution: Install `django-types` package and restart LSP server

- Dynamically generated models may not be supported
  - Solution: Models must be registered when scripts load the app
