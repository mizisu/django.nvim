local M = {}

local watcher = require("django.watcher")
local config = require("django.config")
local fetcher = require("django.fetcher")
local ModelData = require("django.completions.core.model_data")

local SCRIPT_NAME = "get_completion_data.py"
local CACHE_NAME = "completions"

function M.setup()
	local auto_refresh = config.current.completions.auto_refresh
	if auto_refresh and auto_refresh.file_watch_patterns then
		watcher.register("completions", auto_refresh.file_watch_patterns, function()
			M.refresh({ silent = true })
		end)
	end
end

function M.refresh(opts)
	fetcher.refresh_with_callback(SCRIPT_NAME, CACHE_NAME, opts, function(data)
		-- 성공 시에만 인스턴스 교체
		if data then
			ModelData.set_instance(data)
		end
	end)
end

return M
