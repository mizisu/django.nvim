local utils = require("django.utils")
local async = require("django.async")
local context_parser = require("django.completions.core.context_parser")
local completion_builder = require("django.completions.core.completion_builder")

local Source = {}

-- Flag to ensure highlight is set only once
local highlight_initialized = false

--- Setup highlight group for blink.cmp completion kind (called once)
local function setup_highlight()
	if highlight_initialized then
		return
	end
	highlight_initialized = true

	local hl_group = completion_builder.KIND_HL
	if vim.fn.hlexists(hl_group) == 0 or vim.tbl_isempty(vim.api.nvim_get_hl(0, { name = hl_group })) then
		vim.api.nvim_set_hl(0, hl_group, { fg = "#44b78b" }) -- Django green
	end
end

function Source.new(name)
	local self = setmetatable({}, { __index = Source })
	self.name = name

	-- Setup highlight on first source creation
	setup_highlight()

	return self
end

function Source:enabled()
	if vim.bo.filetype ~= "python" then
		return false
	end

	if not utils.is_django_project() then
		return false
	end

	return true
end

function Source:get_completions(ctx, resolve)
	async.run(function()
		local parsed = context_parser.parse(ctx.bufnr, ctx.cursor[1] - 1, ctx.cursor[2])

		if not parsed then
			resolve()
			return
		end

		local items = completion_builder.build(parsed.model_name, parsed.method, parsed.prefix)

		if #items == 0 then
			resolve()
			return
		end

		resolve({
			items = items,
			is_incomplete_forward = true,
			is_incomplete_backward = true,
		})
	end)
end

return Source
