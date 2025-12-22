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

return M
