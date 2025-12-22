local M = {}

local config = require("django.config")

function M.setup(opts)
	config.setup(opts)

	require("django.pickers.views").setup()
	require("django.pickers.models").setup()

	require("django.watcher").setup()
end

function M.refresh_all()
	require("django.pickers.views").refresh()
	require("django.pickers.models").refresh()
end

function M.clear_all_cache()
	local cache_dir = vim.fn.stdpath("cache") .. "/django.nvim"
	if vim.fn.isdirectory(cache_dir) == 1 then
		vim.fn.delete(cache_dir, "rf")
		vim.fn.mkdir(cache_dir, "p")
		vim.notify("Django cache cleared successfully", vim.log.levels.INFO)
	end
end

return M
