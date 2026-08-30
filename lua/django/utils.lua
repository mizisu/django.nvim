local M = {}

function M.is_django_project()
	local manage_py = vim.fn.findfile("manage.py", ".;")
	return manage_py ~= ""
end

function M.get_python_path()
	-- 1. Try venv-selector plugin
	local ok, venv_selector = pcall(require, "venv-selector")
	if ok then
		local venv_path = venv_selector.venv()
		if venv_path and venv_path ~= "" then
			return venv_path .. "/bin/python"
		end
	end

	-- 2. Try vim.g.python3_host_prog
	if vim.g.python3_host_prog then
		return vim.g.python3_host_prog
	end

	-- 3. Try local .venv directory
	local cwd = vim.fn.getcwd()
	local venv_python = cwd .. "/.venv/bin/python"
	if vim.fn.executable(venv_python) == 1 then
		return venv_python
	end

	-- 4. Fallback to system python3
	return "python3"
end

--- Strip matching surrounding quotes from a value
--- @param value string
--- @return string
local function strip_quotes(value)
	local quoted = value:match('^"(.*)"$') or value:match("^'(.*)'$")
	return quoted or value
end

--- Parse a .env file into a table of environment variables
--- @param path string Path to the dotenv file
--- @return table<string, string>
function M.parse_dotenv(path)
	local env = {}

	if vim.fn.filereadable(path) ~= 1 then
		return env
	end

	for _, line in ipairs(vim.fn.readfile(path)) do
		local trimmed = vim.trim(line)

		if trimmed ~= "" and not trimmed:match("^#") then
			trimmed = trimmed:gsub("^export%s+", "")

			local key, value = trimmed:match("^([%w_][%w%d_]*)%s*=%s*(.*)$")
			if key then
				env[key] = strip_quotes(vim.trim(value))
			end
		end
	end

	return env
end

--- Resolve the dotenv file path from config (relative paths are resolved against cwd)
--- @param dotenv_path string
--- @return string
local function resolve_dotenv_path(dotenv_path)
	if vim.fn.fnamemodify(dotenv_path, ":p") == dotenv_path then
		return dotenv_path
	end
	return vim.fn.getcwd() .. "/" .. dotenv_path
end

--- Get the merged environment variables for running Django commands
--- Precedence (highest last): .env file < config.shell.env
--- @return table<string, string>
function M.get_env()
	local config = require("django.config").current
	local env_cfg = config.env or {}
	local shell_cfg = config.shell or {}

	local env = {}

	if env_cfg.dotenv then
		local path = resolve_dotenv_path(env_cfg.dotenv_path or ".env")
		env = M.parse_dotenv(path)
	end

	if shell_cfg.env and next(shell_cfg.env) then
		env = vim.tbl_extend("force", env, shell_cfg.env)
	end

	return env
end

return M
