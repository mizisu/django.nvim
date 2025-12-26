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
}

M.current = vim.deepcopy(M.default)

function M.setup(opts)
	M.current = vim.tbl_deep_extend("force", M.default, opts or {})
end

return M
