local M = {}
local fetcher = require("django.fetcher")

local active_pickers = {}

vim.api.nvim_create_autocmd("User", {
	pattern = "DjangoDataRefreshed",
	callback = function(ev)
		local cache_name = ev.data.cache_name
		local picker = active_pickers[cache_name]
		if picker then
			picker:find({ refresh = true })
		end
	end,
})

function M.create_picker(config)
	local script_name = config.script_name
	local cache_name = config.cache_name
	local prompt = config.prompt
	local format_item = config.format_item
	local prepare_text = config.prepare_text
	local refresh_desc = config.refresh_desc or "Refresh data"
	local get_on_picker_open = config.on_picker_open

	local function show_picker()
		local picker_instance = require("snacks").picker.pick({
			prompt = prompt,
			finder = function()
				local items = fetcher.get_cached_data(cache_name)
				for _, item in ipairs(items) do
					item.text = prepare_text(item)
				end
				return items
			end,
			preview = "file",
			format = format_item,
			actions = {
				refresh_data = function(picker)
					fetcher.refresh_with_callback(script_name, cache_name, nil, function(data)
						if data then
							picker:find({ refresh = true })
						end
					end)
				end,
			},
			win = {
				input = {
					keys = {
						["<C-r>"] = {
							"refresh_data",
							desc = refresh_desc,
							mode = { "n", "i" },
						},
					},
				},
			},
		})

		active_pickers[cache_name] = picker_instance

		if picker_instance then
			vim.api.nvim_create_autocmd("WinClosed", {
				---@diagnostic disable-next-line: undefined-field
				pattern = tostring(picker_instance.win),
				once = true,
				callback = function()
					active_pickers[cache_name] = nil
				end,
			})
		end

		local on_picker_open = type(get_on_picker_open) == "function" and get_on_picker_open() or get_on_picker_open
		if on_picker_open then
			fetcher.refresh_with_callback(script_name, cache_name, { silent = true })
		end
	end

	return function()
		-- Check if cache exists
		local cached_data = fetcher.get_cached_data(cache_name)
		if not cached_data or vim.tbl_isempty(cached_data) then
			-- No cache, refresh first then show picker
			fetcher.refresh_with_callback(script_name, cache_name, nil, function(data)
				if data and not vim.tbl_isempty(data) then
					show_picker()
				end
			end)
		else
			-- Cache exists, show picker immediately
			show_picker()
		end
	end
end

return M
