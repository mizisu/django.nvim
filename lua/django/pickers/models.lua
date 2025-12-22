local M = {}
local fetcher = require("django.fetcher")
local picker = require("django.pickers")
local config = require("django.config")
local watcher = require("django.watcher")

local SCRIPT_NAME = "get_models.py"
local CACHE_NAME = "DjangoModels"

function M.setup()
	local auto_refresh = config.current.models.auto_refresh
	if auto_refresh and auto_refresh.file_watch_patterns then
		watcher.register("models", auto_refresh.file_watch_patterns, function()
			M.refresh({ silent = true })
		end)
	end
end

function M.refresh(opts)
	fetcher.refresh_with_callback(SCRIPT_NAME, CACHE_NAME, opts)
end

M.show = picker.create_picker({
	script_name = SCRIPT_NAME,
	cache_name = CACHE_NAME,
	prompt = "Django Models ",
	prepare_text = function(model)
		return model.name .. " " .. model.name .. " " .. model.app_label
	end,
	format_item = function(item, _)
		local file_name = ""
		if item.file and item.file ~= "" then
			file_name = vim.fn.fnamemodify(item.file, ":t")
		end

		local field_info = string.format("(%d fields)", item.field_count)

		return {
			{ string.format("%-40s", item.name), "Type" },
			{ " " },
			{ field_info, "Number" },
			{ " " },
			{ item.app_label, "Function" },
			{ " " },
			{ file_name, "Comment" },
		}
	end,
	refresh_desc = "Refresh models",
	on_picker_open = function()
		return config.current.models.auto_refresh.on_picker_open
	end,
})

return M
