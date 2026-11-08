local M = {}

--- Check if the current buffer belongs to a Django project
--- @return boolean
function M.is_django_project()
	return M.get_project_root() ~= nil
end

--- Find the Django project root (nearest ancestor directory with manage.py)
--- @return string|nil
function M.get_project_root()
	local buf_name = vim.api.nvim_buf_get_name(0)
	if buf_name ~= "" then
		local root = vim.fs.root(buf_name, "manage.py")
		if root then
			return root
		end
	end

	return vim.fs.root(vim.fn.getcwd(), "manage.py")
end

--- Check if the project is managed by uv (detected from project files)
--- @param root string|nil Project root
--- @return boolean
function M.is_uv_project(root)
	if not root or vim.fn.executable("uv") == 0 then
		return false
	end

	local lock_files = vim.fs.find("uv.lock", { upward = true, path = root, type = "file" })
	if #lock_files > 0 then
		return true
	end

	local pyprojects = vim.fs.find("pyproject.toml", { upward = true, path = root, type = "file" })
	if #pyprojects == 0 then
		return false
	end

	local ok, lines = pcall(vim.fn.readfile, pyprojects[1])
	if not ok then
		return false
	end

	for _, line in ipairs(lines) do
		if line:match("^%s*%[tool%.uv[%].]") then
			return true
		end
	end

	return false
end

--- Resolve the python command used for Django scripts and manage.py
--- @return string[] Command argv
function M.get_python_command()
	-- 1. Explicit user configuration
	local configured = require("django.config").current.python
	if configured then
		return type(configured) == "table" and configured or { configured }
	end

	local root = M.get_project_root()

	-- 2. uv projects always run through uv
	if M.is_uv_project(root) then
		return { "uv", "run", "--quiet", "python" }
	end

	-- 3. venv-selector selection
	local ok, venv_selector = pcall(require, "venv-selector")
	if ok and type(venv_selector.venv) == "function" then
		local selected_ok, venv_path = pcall(venv_selector.venv)
		if selected_ok and venv_path and venv_path ~= "" then
			local python = M.__find_venv_python(venv_path)
			if python then
				return { python }
			end
		end
	end

	-- 4. Activated virtualenv
	local virtual_env_python = M.__find_venv_python(vim.env.VIRTUAL_ENV)
	if virtual_env_python then
		return { virtual_env_python }
	end

	-- 5. Activated conda environment
	local conda_python = M.__find_venv_python(vim.env.CONDA_PREFIX)
	if conda_python then
		return { conda_python }
	end

	-- 6. Project virtualenv
	if root then
		local venv_python = M.__find_venv_python(root .. "/.venv")
			or M.__find_venv_python(root .. "/venv")
		if venv_python then
			return { venv_python }
		end
	end

	-- 7. Neovim provider interpreter
	if vim.g.python3_host_prog and vim.g.python3_host_prog ~= "" then
		return { vim.g.python3_host_prog }
	end

	-- 8. System python
	return { "python3" }
end

--- Get the python command as a shell-escaped string
--- @return string
function M.get_python_command_string()
	local escaped = {}
	for _, arg in ipairs(M.get_python_command()) do
		table.insert(escaped, vim.fn.shellescape(arg))
	end
	return table.concat(escaped, " ")
end

--- Get the python executable path (deprecated, use get_python_command)
--- @return string
function M.get_python_path()
	return table.concat(M.get_python_command(), " ")
end

--- Find the python executable inside a virtual environment directory
--- @param venv_dir string|nil
--- @return string|nil
function M.__find_venv_python(venv_dir)
	if not venv_dir or venv_dir == "" then
		return nil
	end

	local candidates = {
		venv_dir .. "/bin/python",
		venv_dir .. "/Scripts/python.exe",
	}

	for _, path in ipairs(candidates) do
		if vim.fn.executable(path) == 1 then
			return path
		end
	end

	return nil
end

return M
