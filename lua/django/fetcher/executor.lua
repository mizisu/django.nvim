local M = {}

local cache = require("django.fetcher.cache")

--- Get plugin's script directory path
--- @param script_name string
--- @return string
function M.__get_script_path(script_name)
	local source = debug.getinfo(1, "S").source:sub(2)
	local plugin_root = vim.fn.fnamemodify(source, ":h:h:h:h")
	return plugin_root .. "/scripts/" .. script_name
end

--- Build shell command to execute Python script
--- @param script_name string
--- @param output_path string
--- @return string
function M.__build_command(script_name, output_path)
	local script_path = M.__get_script_path(script_name)
	local python_path = require("django.utils").get_python_path()
	local cwd = vim.fn.getcwd()

	return string.format(
		"cd %s && %s %s > %s 2>&1",
		vim.fn.shellescape(cwd),
		vim.fn.shellescape(python_path),
		vim.fn.shellescape(script_path),
		vim.fn.shellescape(output_path)
	)
end

--- Execute Python script asynchronously
--- Must be called within async.run()
--- @param script_name string
--- @param cache_name string
--- @return table result { code: number }
function M.run(script_name, cache_name)
	local async = require("django.async")
	local cmd = cache.build_output_command(cache_name, function(output_path)
		return M.__build_command(script_name, output_path)
	end)

	return async.system({ "sh", "-c", cmd }, { text = true })
end

--- Count items in data (handles both arrays and dictionaries)
--- @param data table
--- @return number
function M.__count_items(data)
	if vim.islist(data) then
		return #data
	end
	return vim.tbl_count(data)
end

--- Parse result from temp file
--- @param cache_name string
--- @return table result { success: boolean, message: string, level: number, data: table|nil }
function M.parse_result(cache_name)
	local content = cache.read_temp_lines(cache_name)
	local ok, data = pcall(vim.json.decode, table.concat(content, "\n"))

	if not ok then
		return {
			success = false,
			message = "Failed to parse Django " .. cache_name,
			level = vim.log.levels.ERROR,
			data = nil,
		}
	end

	local item_count = M.__count_items(data)

	if item_count == 0 then
		return {
			success = false,
			message = "No Django " .. cache_name .. " found",
			level = vim.log.levels.WARN,
			data = nil,
		}
	end

	return {
		success = true,
		message = string.format("Django %s refreshed successfully (%d items)", cache_name, item_count),
		level = vim.log.levels.INFO,
		data = data,
	}
end

--- Parse error from temp file
--- @param cache_name string
--- @return table result { success: boolean, message: string, level: number, data: nil }
function M.parse_error(cache_name)
	local error_output = cache.read_temp_lines(cache_name)

	return {
		success = false,
		message = "Failed to get Django " .. cache_name .. ":\n" .. table.concat(error_output, "\n"),
		level = vim.log.levels.ERROR,
		data = nil,
	}
end

return M
