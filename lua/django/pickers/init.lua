local M = {}
local fetcher = require("django.fetcher")

local active_pickers = {}

local function find_item_index_by_key(list, item_key)
	if not item_key or not list or not list.count or not list.get then
		return nil
	end

	for idx = 1, list:count() do
		local item = list:get(idx)
		if item and item.key == item_key then
			return idx
		end
	end

	return nil
end

local function refresh_picker(picker)
	if not picker or not picker.list then
		return
	end

	local current_item = picker.list:current()
	local current_key = current_item and current_item.key or nil
	local current_cursor = picker.list.cursor

	picker:find({
		refresh = true,
		on_done = function()
			if picker.closed or not picker.list then
				return
			end

			local target_idx = find_item_index_by_key(picker.list, current_key)
			if target_idx then
				picker.list:move(target_idx, true)
				return
			end

			picker.list:move(current_cursor or 1, true)
		end,
	})
end

vim.api.nvim_create_autocmd("User", {
	pattern = "DjangoDataRefreshed",
	callback = function(ev)
		local cache_name = ev.data.cache_name
		local picker = active_pickers[cache_name]
		refresh_picker(picker)
	end,
})

function M.create_picker(config)
	local script_name = config.script_name
	local cache_name = config.cache_name
	local prompt = config.prompt
	local format_item = config.format_item
	local prepare_text = config.prepare_text
	local get_item_key = config.item_key
	local refresh_desc = config.refresh_desc or "Refresh data"
	local get_on_picker_open = config.on_picker_open

	local function show_picker()
		local picker_instance = require("snacks").picker.pick({
			prompt = prompt,
			finder = function()
				local items = fetcher.get_cached_data(cache_name)
				for _, item in ipairs(items) do
					item.text = prepare_text(item)
					if get_item_key then
						local item_key = get_item_key(item)
						if item_key ~= nil then
							item.key = tostring(item_key)
						end
					end
				end
				return items
			end,
			preview = "file",
			format = format_item,
			actions = {
				refresh_data = function()
					fetcher.refresh_with_callback(script_name, cache_name, nil)
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
