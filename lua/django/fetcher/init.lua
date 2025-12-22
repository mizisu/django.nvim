local M = {}

local cache = require("django.fetcher.cache")
local executor = require("django.fetcher.executor")
local state = require("django.fetcher.state")

--- Refresh data from script (async, must be called within async.run())
--- @param script_name string Script filename
--- @param cache_name string Cache identifier
--- @param opts table|nil Options: { delay = number, silent = boolean }
--- @return table|nil data
function M.refresh(script_name, cache_name, opts)
	return M.__fetch(script_name, cache_name, opts)
end

--- Refresh data from script with callback
--- @param script_name string Script filename
--- @param cache_name string Cache identifier
--- @param opts table|nil Options: { delay = number, silent = boolean }
--- @param callback function|nil Callback that receives data
function M.refresh_with_callback(script_name, cache_name, opts, callback)
	local async = require("django.async")
	async.run(function()
		local data = M.__fetch(script_name, cache_name, opts)
		if callback then
			callback(data)
		end
	end)
end

--- Get cached data or fetch from script (async, must be called within async.run())
--- @param script_name string Script filename
--- @param cache_name string Cache identifier
--- @param opts table|nil Options: { delay = number, silent = boolean }
--- @return table|nil data
function M.get_or_fetch(script_name, cache_name, opts)
	local data = M.get_cached_data(cache_name)

	if data and not vim.tbl_isempty(data) then
		return data
	end

	return M.__fetch(script_name, cache_name, opts)
end

--- Get cached data (synchronous)
--- @param cache_name string Cache identifier
--- @return table data
function M.get_cached_data(cache_name)
	return cache.read(cache_name)
end

--- Internal fetch function (async)
--- @param script_name string Script filename
--- @param cache_name string Cache identifier
--- @param opts table|nil Options
--- @return table|nil data
function M.__fetch(script_name, cache_name, opts)
	local async = require("django.async")

	opts = opts or {}
	local delay = opts.delay or 0
	local silent = opts.silent or false

	-- Cancel pending timer if exists
	state.cancel_pending_timer(cache_name)

	-- Wait if delay specified
	if delay > 0 then
		async.wait(delay)
	end

	-- Check if already fetching
	if state.is_fetching(cache_name) then
		if not silent then
			vim.notify("Django " .. cache_name .. " refresh already in progress", vim.log.levels.DEBUG)
		end
		return cache.read(cache_name)
	end

	state.set_fetching(cache_name, true)

	if not silent then
		vim.notify("Fetching Django " .. cache_name .. "...", vim.log.levels.INFO)
	end

	-- Execute script
	local result = executor.run(script_name, cache_name)

	state.set_fetching(cache_name, false)

	-- Process result
	local result_obj
	if result.code ~= 0 then
		result_obj = executor.parse_error(cache_name)
	else
		result_obj = executor.parse_result(cache_name)
	end

	-- Handle success/failure
	if result_obj.success then
		cache.commit(cache_name)
		vim.api.nvim_exec_autocmds("User", {
			pattern = "DjangoDataRefreshed",
			data = { cache_name = cache_name },
		})
	else
		cache.discard(cache_name)
	end

	if not silent then
		vim.notify(result_obj.message, result_obj.level)
	end

	return result_obj.data
end

return M
