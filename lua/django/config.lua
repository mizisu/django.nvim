local M = {}

M.default = {
	views = {
		auto_refresh = {
			on_picker_open = true,
			file_watch_patterns = {
				"**/urls.py",
				"**/views.py",
				"**/view.py",
				"**/*views.py",
				"**/*view.py",
				"**/*viewset.py",
				"**/*view_set.py",
				"**/*api.py",
			},
		},
	},
	models = {
		auto_refresh = {
			on_picker_open = true,
			file_watch_patterns = { "**/models.py", "**/models/*.py" },
		},
	},
	completions = {
		auto_refresh = {
			file_watch_patterns = { "**/models.py", "**/models/*.py" },
		},
	},
	shell = {
		command = "shell", -- "shell", "shell_plus", "shell_plus --ipython", etc.
		position = "right", -- "bottom", "top", "left", "right", "float"
		env = {}, -- explicit environment variables (e.g. { DJANGO_SETTINGS_MODULE = "myproject.settings" }), always wins over dotenv
	},
	env = {
		dotenv = false, -- set true to load env vars from a .env file at the project root
		dotenv_path = ".env", -- path to the dotenv file, relative to the project root (cwd) or absolute
	},
}

M.current = vim.deepcopy(M.default)

function M.setup(opts)
	M.current = vim.tbl_deep_extend("force", M.default, opts or {})
end

return M
