local ModelData = require("django.completions.core.model_data")

local M = {}

-- =============================================================================
-- Completion item appearance
-- =============================================================================

-- blink.cmp uses: kind_name (string), kind_icon (string), kind_hl (highlight group name)
M.KIND_NAME = "Django"
M.KIND_ICON = ""
M.KIND_HL = "BlinkCmpKindDjango" -- Highlight group (set in init.lua with Django green #44b78b)

-- =============================================================================
-- Relation type groups for different QuerySet methods
-- =============================================================================

-- select_related: FK, O2O only (M2M not supported)
local RELATIONS_SELECT = {
	ForeignKey = true,
	OneToOneField = true,
	OneToOneRel = true,
}

-- prefetch_related: All relation types
local RELATIONS_PREFETCH = {
	ForeignKey = true,
	OneToOneField = true,
	ManyToManyField = true,
	ManyToOneRel = true,
	OneToOneRel = true,
	ManyToManyRel = true,
}

-- filter, values, order_by, etc: All relation types for traversal
local RELATIONS_ALL = {
	ForeignKey = true,
	OneToOneField = true,
	ManyToManyField = true,
	ManyToOneRel = true,
	OneToOneRel = true,
	ManyToManyRel = true,
}

-- =============================================================================
-- Method configuration
-- =============================================================================

local METHOD_CONFIG = {
	-- Filter-style: fields + lookups + all relations
	filter = { fields = true, lookups = true, relations = RELATIONS_ALL },
	exclude = { fields = true, lookups = true, relations = RELATIONS_ALL },
	get = { fields = true, lookups = true, relations = RELATIONS_ALL },
	get_or_create = { fields = true, lookups = true, relations = RELATIONS_ALL },
	update_or_create = { fields = true, lookups = true, relations = RELATIONS_ALL },

	-- Create/Update: fields only (no traversal)
	create = { fields = true, lookups = false, relations = nil },
	update = { fields = true, lookups = false, relations = nil },

	-- Field-only: fields + traversal (no lookups)
	values = { fields = true, lookups = false, relations = RELATIONS_ALL },
	values_list = { fields = true, lookups = false, relations = RELATIONS_ALL },
	only = { fields = true, lookups = false, relations = RELATIONS_SELECT },
	defer = { fields = true, lookups = false, relations = RELATIONS_SELECT },

	-- Relations-only
	select_related = { fields = false, lookups = false, relations = RELATIONS_SELECT },
	prefetch_related = { fields = false, lookups = false, relations = RELATIONS_PREFETCH },

	-- Order-style
	order_by = { fields = true, lookups = false, relations = RELATIONS_ALL },

	-- Annotation: field references for F() expressions
	annotate = { fields = true, lookups = false, relations = RELATIONS_ALL },
	aggregate = { fields = true, lookups = false, relations = RELATIONS_ALL },
}

--- Split prefix by "__" and return path + label_prefix
--- e.g., "author__profile__" → {"author", "profile"}, "author__profile__"
--- e.g., "author__na" → {"author"}, "author__"
--- e.g., "tit" → {}, ""
---@param prefix string
---@return string[] path
---@return string label_prefix
local function split_prefix(prefix)
	if not prefix or prefix == "" then
		return {}, ""
	end

	local parts = {}
	local remaining = prefix

	while true do
		local pos = remaining:find("__", 1, true)
		if not pos then
			break
		end
		table.insert(parts, remaining:sub(1, pos - 1))
		remaining = remaining:sub(pos + 2)
	end

	local label_prefix = ""
	if #parts > 0 then
		label_prefix = table.concat(parts, "__") .. "__"
	end

	return parts, label_prefix
end

---@class ResolveResult
---@field model string|nil Current model name
---@field label_prefix string Prefix for labels
---@field field FieldInfo|nil Terminal field (for lookups)
---@field field_name string|nil Terminal field name
---@field field_model string|nil Model containing the terminal field

--- Follow path to find current model or terminal field
---@param model_name string Starting model
---@param prefix string User input prefix
---@param model_data ModelData
---@return ResolveResult
local function resolve_path(model_name, prefix, model_data)
	local path, label_prefix = split_prefix(prefix)

	if #path == 0 then
		return { model = model_name, label_prefix = "" }
	end

	local current_model = model_name
	for i, segment in ipairs(path) do
		local field = model_data:get_field(current_model, segment)
		if not field then
			return { model = nil, label_prefix = label_prefix }
		end

		if field.related_model then
			-- Follow relation
			current_model = field.related_model
		else
			-- Terminal field (non-relation) - return for lookup completion
			if i == #path then
				return {
					model = nil,
					label_prefix = label_prefix,
					field = field,
					field_name = segment,
					field_model = current_model,
				}
			else
				-- Invalid path: non-relation field in middle
				return { model = nil, label_prefix = label_prefix }
			end
		end
	end

	return { model = current_model, label_prefix = label_prefix }
end

--- Build documentation for a field
---@param field FieldInfo
---@param model_name string
---@param model_data ModelData|nil
---@return table
local function build_documentation(field, model_name, model_data)
	local lines = {}

	-- For relation fields, show the related model's fields (compact format)
	if field.related_model and model_data then
		local related = model_data:get_model(field.related_model)
		if related and related.fields then
			table.insert(lines, "```python")
			table.insert(lines, "class " .. field.related_model .. ":")
			for field_name, field_info in pairs(related.fields) do
				-- Skip reverse relations and auto-generated _id fields
				if not field_name:match("_id$") and not field_info.type:match("Rel$") then
					if field_info.related_model then
						table.insert(
							lines,
							"    " .. field_name .. ": " .. field_info.type .. " → " .. field_info.related_model
						)
					else
						table.insert(lines, "    " .. field_name .. ": " .. field_info.type)
					end
				end
			end
			table.insert(lines, "```")
		end
	else
		-- For non-relation fields, show the field definition
		table.insert(lines, "```python")
		table.insert(lines, "class " .. model_name .. ":")
		table.insert(lines, "    " .. (field.definition or "# unknown"))
		table.insert(lines, "```")

		if field.choices and field.choices.values then
			table.insert(lines, "")
			table.insert(lines, "**Choices:**")
			for _, c in ipairs(field.choices.values) do
				table.insert(lines, string.format("- `%s` - %s", c.value, c.label))
			end
		end
	end

	return { kind = "markdown", value = table.concat(lines, "\n") }
end

--- Build documentation for a lookup
---@param field_name string
---@param field FieldInfo
---@param model_name string
---@param lookup string
---@param model_data ModelData
---@return table
local function build_lookup_documentation(field_name, field, model_name, lookup, model_data)
	local meta = model_data:get_lookup_metadata(lookup)
	local lines = {}

	-- Show field definition in class format
	table.insert(lines, "```python")
	table.insert(lines, "class " .. model_name .. ":")
	table.insert(lines, "    " .. (field.definition or field_name .. " = " .. field.type .. "(...)"))
	table.insert(lines, "```")

	if meta then
		table.insert(lines, "")
		table.insert(lines, "**Lookup:** `" .. lookup .. "`")
		table.insert(lines, meta.description)
		table.insert(lines, "")
		table.insert(lines, "```sql")
		table.insert(lines, meta.sql)
		table.insert(lines, "```")
	end

	return { kind = "markdown", value = table.concat(lines, "\n") }
end

--- Create a field completion item
---@param name string
---@param field FieldInfo
---@param label_prefix string
---@param model_name string
---@param model_data ModelData
---@return table
local function make_field_item(name, field, label_prefix, model_name, model_data)
	local detail = field.type
	if field.related_model then
		detail = field.type .. " → " .. field.related_model
	end
	return {
		label = label_prefix .. name,
		kind_name = M.KIND_NAME,
		kind_icon = M.KIND_ICON,
		kind_hl = M.KIND_HL,
		detail = detail,
		documentation = build_documentation(field, model_name, model_data),
	}
end

--- Create a lookup completion item
---@param name string
---@param field FieldInfo
---@param lookup string
---@param label_prefix string
---@param model_name string
---@param model_data ModelData
---@return table
local function make_lookup_item(name, field, lookup, label_prefix, model_name, model_data)
	return {
		label = label_prefix .. name .. "__" .. lookup,
		kind_name = M.KIND_NAME,
		kind_icon = M.KIND_ICON,
		kind_hl = M.KIND_HL,
		detail = field.type,
		documentation = build_lookup_documentation(name, field, model_name, lookup, model_data),
	}
end

--- Check if field type is allowed by the relation config
---@param field_type string
---@param allowed_relations table|nil
---@return boolean
local function is_allowed_relation(field_type, allowed_relations)
	if not allowed_relations then
		return false
	end
	return allowed_relations[field_type] == true
end

-- =============================================================================
-- Public API
-- =============================================================================

--- Build completion items for Django QuerySet methods
---@param model_name string Model name (e.g., "Post")
---@param method string QuerySet method (e.g., "filter")
---@param prefix string User input prefix (e.g., "author__")
---@return table[] items Blink completion items
function M.build(model_name, method, prefix)
	local model_data = ModelData.get_instance()
	if not model_data then
		return {}
	end

	local config = METHOD_CONFIG[method]
	if not config then
		return {}
	end

	local resolved = resolve_path(model_name, prefix, model_data)

	-- Terminal field case: show lookups only
	if resolved.field then
		return M.__build_lookup_items(resolved, config, model_data)
	end

	-- Model case: show fields
	if resolved.model then
		return M.__build_field_items(resolved, config, model_data)
	end

	return {}
end

-- =============================================================================
-- Private helpers
-- =============================================================================

--- Build lookup completion items for a terminal field
---@param resolved ResolveResult
---@param config table Method configuration
---@param model_data ModelData
---@return table[]
function M.__build_lookup_items(resolved, config, model_data)
	if not config.lookups then
		return {}
	end

	local items = {}
	for _, lookup in ipairs(model_data:get_lookups_for_type(resolved.field.type)) do
		table.insert(items, {
			label = resolved.label_prefix .. lookup,
			kind_name = M.KIND_NAME,
			kind_icon = M.KIND_ICON,
			kind_hl = M.KIND_HL,
			detail = resolved.field.type,
			documentation = build_lookup_documentation(
				resolved.field_name,
				resolved.field,
				resolved.field_model,
				lookup,
				model_data
			),
		})
	end
	return items
end

--- Build field completion items for a model
---@param resolved ResolveResult
---@param config table Method configuration
---@param model_data ModelData
---@return table[]
function M.__build_field_items(resolved, config, model_data)
	local model = model_data:get_model(resolved.model)
	if not model or not model.fields then
		return {}
	end

	local items = {}
	for name, field in pairs(model.fields) do
		local is_relation = field.related_model ~= nil

		-- Filter by relation type
		if is_relation then
			if not is_allowed_relation(field.type, config.relations) then
				goto continue
			end
		else
			-- Non-relation field: skip if relations-only mode
			if not config.fields then
				goto continue
			end
		end

		-- Add field item
		table.insert(items, make_field_item(name, field, resolved.label_prefix, resolved.model, model_data))

		-- Add lookup items (non-relation fields only)
		if config.lookups and not is_relation then
			for _, lookup in ipairs(model_data:get_lookups_for_type(field.type)) do
				table.insert(
					items,
					make_lookup_item(name, field, lookup, resolved.label_prefix, resolved.model, model_data)
				)
			end
		end

		::continue::
	end

	return items
end

return M
