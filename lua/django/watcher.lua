local M = {}

local utils = require("django.utils")

local registry = {}

--- @param feature_name string
--- @param patterns string[]
--- @param callback function
function M.register(feature_name, patterns, callback)
	registry[feature_name] = {
		patterns = patterns,
		callback = callback,
	}
end

function M.setup()
	for feature_name, feature in pairs(registry) do
		local augroup = vim.api.nvim_create_augroup("DjangoAutoRefresh_" .. feature_name, { clear = true })

		vim.api.nvim_create_autocmd("BufWritePost", {
			group = augroup,
			pattern = feature.patterns,
			callback = function()
				if not utils.is_django_project() then
					return
				end
				feature.callback()
			end,
		})
	end
end

return M
