local M = {}
local fetcher = require("django.fetcher")
local picker = require("django.pickers")
local config = require("django.config")
local watcher = require("django.watcher")

local SCRIPT_NAME = "get_views.py"
local CACHE_NAME = "DjangoViews"

function M.setup()
	local auto_refresh = config.current.views.auto_refresh
	if auto_refresh and auto_refresh.file_watch_patterns then
		watcher.register("views", auto_refresh.file_watch_patterns, function()
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
	prompt = "Django Views ",
	prepare_text = function(endpoint)
		local view_display = endpoint.view_display or endpoint.view_name or endpoint.view or ""
		return (endpoint.pattern or "") .. " " .. view_display
	end,
	format_item = function(item, _)
		local file_name = ""
		if item.file and item.file ~= "" then
			file_name = vim.fn.fnamemodify(item.file, ":t")
		end

		local view_display = item.view_display or item.view_name or item.view or ""

		return {
			{ string.format("%-50s", item.pattern or ""), "Normal" },
			{ " " },
			{ view_display, "Function" },
			{ " " },
			{ file_name, "Comment" },
		}
	end,
	refresh_desc = "Refresh views",
	on_picker_open = function()
		return config.current.views.auto_refresh.on_picker_open
	end,
})

return M
