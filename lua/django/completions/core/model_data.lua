---@class ChoiceValue
---@field value string|number
---@field label string

---@class ChoicesInfo
---@field values ChoiceValue[]
---@field class? string
---@field type? string

---@class FieldInfo
---@field type string
---@field definition string
---@field null boolean
---@field blank boolean
---@field max_length? number
---@field related_model? string
---@field related_app? string
---@field traversable? boolean
---@field choices? ChoicesInfo

---@class ModelInfo
---@field app_label string
---@field module string
---@field fields table<string, FieldInfo>

---@class LookupMetadata
---@field description string
---@field sql string

---@class LookupData
---@field base string[]
---@field by_type table<string, string[]>
---@field metadata table<string, LookupMetadata>

---@class ModelData
---@field models table<string, ModelInfo>
---@field lookups LookupData

local ModelData = {}
ModelData.__index = ModelData

local fetcher = require("django.fetcher")

local SCRIPT_NAME = "get_completion_data.py"
local CACHE_NAME = "completions"

local instance = nil

function ModelData.new(data)
	local self = setmetatable({}, ModelData)
	self.models = data.models or {}
	self.lookups = data.lookups or {}
	return self
end

--- Get singleton instance (loads data if needed)
--- Must be called within async.run()
---@return ModelData|nil
function ModelData.get_instance()
	if instance then
		return instance
	end

	local data = fetcher.get_or_fetch(SCRIPT_NAME, CACHE_NAME, { silent = true })
	if not data then
		return nil
	end

	instance = ModelData.new(data)
	return instance
end

--- Clear cached instance
function ModelData.clear()
	instance = nil
end

--- Set singleton instance (for refresh)
---@param data table
function ModelData.set_instance(data)
	if data then
		instance = ModelData.new(data)
	end
end

--- Get model by name
---@param model_name string
---@return ModelInfo|nil
function ModelData:get_model(model_name)
	return self.models[model_name]
end

--- Get field from model
---@param model_name string
---@param field_name string
---@return FieldInfo|nil
function ModelData:get_field(model_name, field_name)
	local model = self:get_model(model_name)
	if not model or not model.fields then
		return nil
	end
	return model.fields[field_name]
end

--- Get lookups for field type
---@param field_type string
---@return string[]
function ModelData:get_lookups_for_type(field_type)
	local result = {}

	for _, lookup in ipairs(self.lookups.base or {}) do
		table.insert(result, lookup)
	end

	local type_lookups = self.lookups.by_type and self.lookups.by_type[field_type]
	if type_lookups then
		for _, lookup in ipairs(type_lookups) do
			table.insert(result, lookup)
		end
	end

	return result
end

--- Get lookup metadata
---@param lookup_name string
---@return LookupMetadata|nil
function ModelData:get_lookup_metadata(lookup_name)
	if not self.lookups.metadata then
		return nil
	end
	return self.lookups.metadata[lookup_name]
end

return ModelData
