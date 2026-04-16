local M = {}
local fetcher = require("django.fetcher")
local picker = require("django.pickers")
local config = require("django.config")
local watcher = require("django.watcher")

local SCRIPT_NAME = "get_views.py"
local CACHE_NAME = "DjangoViews"

function M.setup()
	local auto_refresh = config.current.views.auto_refresh
	if auto_refresh and auto_refresh.file_watch_patterns then
		watcher.register("views", auto_refresh.file_watch_patterns, function()
			M.refresh({ silent = true })
		end)
	end
end

function M.refresh(opts)
	fetcher.refresh_with_callback(SCRIPT_NAME, CACHE_NAME, opts)
end

function M.__append_unique(values, seen, value)
	if not value or value == "" or seen[value] then
		return
	end

	seen[value] = true
	table.insert(values, value)
end

function M.__normalize_query_path(query)
	if not query or query == "" then
		return nil
	end

	local normalized = vim.trim(query)
	if normalized == "" or normalized:find("%s") then
		return nil
	end

	normalized = normalized:gsub("^[%a][%w+.-]*://[^/]+", "")
	normalized = normalized:gsub("[?#].*$", "")
	normalized = normalized:gsub("//+", "/")

	if normalized == "" then
		return nil
	end

	if normalized:sub(1, 1) ~= "/" then
		normalized = "/" .. normalized
	end

	if #normalized > 1 and normalized:sub(-1) ~= "/" then
		normalized = normalized .. "/"
	end

	return normalized
end

function M.__normalize_pattern(pattern)
	if not pattern or pattern == "" then
		return nil
	end

	if pattern:find("(?P<format>", 1, true) then
		return nil
	end

	local normalized = pattern
	normalized = normalized:gsub("%(%?P<([%w_]+)>[^%)]*%)", "<%1>")
	normalized = normalized:gsub("<[%w_]+:([%w_]+)>", "<%1>")
	normalized = normalized:gsub("%^", "")
	normalized = normalized:gsub("%$", "")
	normalized = normalized:gsub("\\/", "/")
	normalized = normalized:gsub("//+", "/")

	if normalized:sub(1, 1) ~= "/" then
		normalized = "/" .. normalized
	end

	return normalized
end

function M.__expand_optional_groups(pattern)
	if not pattern or pattern == "" then
		return {}
	end

	local results = {}
	local seen = {}

	local function visit(value)
		if not value or value == "" or seen[value] then
			return
		end

		seen[value] = true

		local before, inner, after = value:match("^(.-)%(%?:([^%(%)]+)%)%?(.*)$")
		if before and inner and after then
			visit(before .. after)
			visit(before .. inner .. after)
			return
		end

		table.insert(results, value)
	end

	visit(pattern)

	return results
end

function M.__canonicalize_pattern(pattern)
	local normalized = M.__normalize_pattern(pattern)
	if not normalized then
		return nil
	end

	normalized = normalized:gsub("%(%?:", "(")
	normalized = normalized:gsub("%b()", "<param>")
	normalized = normalized:gsub("<[%w_]+>", "<param>")
	normalized = normalized:gsub("//+", "/")

	if normalized:sub(1, 1) ~= "/" then
		normalized = "/" .. normalized
	end

	if #normalized > 1 and normalized:sub(-1) ~= "/" then
		normalized = normalized .. "/"
	end

	return normalized
end

function M.__pattern_variants(pattern)
	local normalized = M.__normalize_pattern(pattern)
	if not normalized then
		return {}
	end

	local values = {}
	local seen = {}

	for _, candidate in ipairs(M.__expand_optional_groups(normalized)) do
		M.__append_unique(values, seen, M.__canonicalize_pattern(candidate))
	end

	if vim.tbl_isempty(values) then
		M.__append_unique(values, seen, M.__canonicalize_pattern(normalized))
	end

	return values
end

function M.__split_segments(path)
	local segments = {}

	for segment in (path or ""):gmatch("[^/]+") do
		table.insert(segments, segment)
	end

	return segments
end

function M.__is_dynamic_segment(segment)
	if not segment or segment == "" then
		return false
	end

	if segment == "<param>" or segment:match("^<[%w_]+>$") then
		return true
	end

	return segment:find("[%(%)%[%]%?%+%*\\|]") ~= nil
end

function M.__static_path(pattern)
	local segments = {}

	for _, segment in ipairs(M.__split_segments(pattern)) do
		if not M.__is_dynamic_segment(segment) then
			table.insert(segments, segment)
		end
	end

	if vim.tbl_isempty(segments) then
		return nil
	end

	return "/" .. table.concat(segments, "/") .. "/"
end

function M.__matches_pattern(pattern, query)
	local pattern_segments = M.__split_segments(pattern)
	local query_segments = M.__split_segments(query)

	if #pattern_segments ~= #query_segments then
		return false
	end

	for index, pattern_segment in ipairs(pattern_segments) do
		local query_segment = query_segments[index]
		if M.__is_dynamic_segment(pattern_segment) then
			if not query_segment or query_segment == "" then
				return false
			end
		elseif pattern_segment ~= query_segment then
			return false
		end
	end

	return true
end

function M.__matches_concrete_path(pattern, query)
	local normalized_query = M.__normalize_query_path(query)
	if not normalized_query then
		return false
	end

	for _, candidate in ipairs(M.__pattern_variants(pattern)) do
		if M.__matches_pattern(candidate, normalized_query) then
			return true
		end
	end

	return false
end

function M.__build_search_text(endpoint)
	local values = {}
	local seen = {}
	local view_display = endpoint.view_display or endpoint.view_name or endpoint.view or ""

	M.__append_unique(values, seen, endpoint.pattern)
	M.__append_unique(values, seen, M.__normalize_pattern(endpoint.pattern))
	M.__append_unique(values, seen, endpoint.name)
	M.__append_unique(values, seen, endpoint.view_name)
	M.__append_unique(values, seen, endpoint.view)
	M.__append_unique(values, seen, view_display)
	M.__append_unique(values, seen, endpoint.method)
	M.__append_unique(values, seen, endpoint.action)

	for _, candidate in ipairs(M.__pattern_variants(endpoint.pattern)) do
		M.__append_unique(values, seen, candidate)
		M.__append_unique(values, seen, M.__static_path(candidate))
	end

	return table.concat(values, " ")
end

function M.__transform_item(item, ctx)
	local query = ctx and ctx.filter and ctx.filter.pattern or ""
	if query == "" or not M.__matches_concrete_path(item.pattern, query) then
		return item
	end

	local values = {}
	local seen = {}
	local normalized_query = M.__normalize_query_path(query)

	M.__append_unique(values, seen, query)
	M.__append_unique(values, seen, normalized_query)
	M.__append_unique(values, seen, item.text)

	item.text = table.concat(values, " ")
	return item
end

function M.__should_refresh_for_query(picker_instance, filter)
	local pattern = filter and filter.pattern or ""
	if picker_instance.__django_views_pattern == pattern then
		return false
	end

	picker_instance.__django_views_pattern = pattern
	return true
end

M.show = picker.create_picker({
	script_name = SCRIPT_NAME,
	cache_name = CACHE_NAME,
	prompt = "Django Views ",
	prepare_text = function(endpoint)
		return M.__build_search_text(endpoint)
	end,
	format_item = function(item, _)
		local file_name = ""
		if item.file and item.file ~= "" then
			file_name = vim.fn.fnamemodify(item.file, ":t")
		end

		local view_display = item.view_display or item.view_name or item.view or ""

		return {
			{ string.format("%-50s", item.pattern or ""), "Normal" },
			{ " " },
			{ view_display, "Function" },
			{ " " },
			{ file_name, "Comment" },
		}
	end,
	item_key = function(endpoint)
		local action = endpoint.action or endpoint.method or ""
		return table.concat({ endpoint.pattern or "", endpoint.view or "", action, endpoint.name or "" }, "|")
	end,
	refresh_desc = "Refresh views",
	on_picker_open = function()
		return config.current.views.auto_refresh.on_picker_open
	end,
	transform = function(item, ctx)
		return M.__transform_item(item, ctx)
	end,
	filter = {
		transform = function(picker_instance, filter)
			return M.__should_refresh_for_query(picker_instance, filter)
		end,
	},
})

return M