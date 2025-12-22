local M = {}

--- Get cache directory path
--- @return string
function M.__get_cache_dir()
	local cache_dir = vim.fn.stdpath("cache") .. "/django.nvim"
	vim.fn.mkdir(cache_dir, "p")
	return cache_dir
end

--- Get project hash based on current working directory
--- @return string
function M.__get_project_hash()
	local cwd = vim.fn.getcwd()
	return vim.fn.sha256(cwd):sub(1, 8)
end

--- Get cache file path for a cache name
--- @param cache_name string
--- @return string
function M.__get_path(cache_name)
	local cache_dir = M.__get_cache_dir()
	local hash = M.__get_project_hash()
	return cache_dir .. "/" .. cache_name .. "." .. hash .. ".json"
end

--- Get temporary file path for a cache name
--- @param cache_name string
--- @return string
function M.__get_temp_path(cache_name)
	return M.__get_path(cache_name) .. ".tmp"
end

--- Read cached data from file
--- @param cache_name string
--- @return table data Empty table if not found or invalid
function M.read(cache_name)
	local path = M.__get_path(cache_name)

	if vim.fn.filereadable(path) == 1 then
		local content = vim.fn.readfile(path)
		local ok, data = pcall(vim.json.decode, table.concat(content, "\n"))
		if ok and data then
			return data
		end
	end

	return {}
end

--- Move temp file to permanent cache file
--- @param cache_name string
function M.commit(cache_name)
	local temp_path = M.__get_temp_path(cache_name)
	local path = M.__get_path(cache_name)
	vim.fn.rename(temp_path, path)
end

--- Delete temp file
--- @param cache_name string
function M.discard(cache_name)
	local temp_path = M.__get_temp_path(cache_name)
	vim.fn.delete(temp_path)
end

--- Read temp file content as lines
--- @param cache_name string
--- @return string[] lines
function M.read_temp_lines(cache_name)
	local temp_path = M.__get_temp_path(cache_name)
	return vim.fn.readfile(temp_path)
end

--- Build command with temp file output path
--- @param cache_name string
--- @param cmd_builder function Function that receives output_path and returns command string
--- @return string command
function M.build_output_command(cache_name, cmd_builder)
	local output_path = M.__get_temp_path(cache_name)
	return cmd_builder(output_path)
end

return M
