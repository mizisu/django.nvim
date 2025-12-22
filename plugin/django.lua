if vim.g.loaded_django_nvim then
	return
end
vim.g.loaded_django_nvim = true

vim.api.nvim_create_user_command("DjangoViews", function()
	require("django.pickers.views").show()
end, {})

vim.api.nvim_create_user_command("DjangoViewsRefresh", function()
	require("django.pickers.views").refresh()
end, {})

vim.api.nvim_create_user_command("DjangoModels", function()
	require("django.pickers.models").show()
end, {})

vim.api.nvim_create_user_command("DjangoModelsRefresh", function()
	require("django.pickers.models").refresh()
end, {})

vim.api.nvim_create_user_command("DjangoRefreshAll", function()
	require("django").refresh_all()
end, {})

vim.api.nvim_create_user_command("DjangoClearAllCache", function()
	require("django").clear_all_cache()
end, {})

local keymaps = {
	{
		key = "<leader>djv",
		action = function()
			require("django.pickers.views").show()
		end,
		desc = "Django Views",
		icon = "󰖟",
	},
	{
		key = "<leader>djm",
		action = function()
			require("django.pickers.models").show()
		end,
		desc = "Django Models",
		icon = "󰆼",
	},
	{
		key = "<leader>djr",
		action = function()
			require("django").refresh_all()
		end,
		desc = "Django Refresh All",
		icon = "󰑓",
	},
	{
		key = "<leader>djc",
		action = function()
			require("django").clear_all_cache()
		end,
		desc = "Django Clear All Cache",
		icon = "󰃨",
	},
}

for _, map in ipairs(keymaps) do
	vim.keymap.set("n", map.key, map.action, { desc = map.desc })
end

local ok, which_key = pcall(require, "which-key")
if ok then
	local wk_mappings = {
		{ "<leader>dj", group = "django.nvim", icon = "" },
	}
	for _, map in ipairs(keymaps) do
		table.insert(wk_mappings, { map.key, desc = map.desc, icon = map.icon })
	end
	which_key.add(wk_mappings)
end
