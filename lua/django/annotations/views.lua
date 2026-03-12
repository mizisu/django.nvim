local M = {}

local fetcher = require("django.fetcher")
local utils = require("django.utils")

local SCRIPT_NAME = "get_views.py"
local CACHE_NAME = "DjangoViews"
local NAMESPACE = vim.api.nvim_create_namespace("DjangoViewAnnotations")

function M.setup()
	local augroup = vim.api.nvim_create_augroup("DjangoViewAnnotations", { clear = true })

	vim.api.nvim_create_autocmd({ "BufEnter", "BufWinEnter" }, {
		group = augroup,
		pattern = "*.py",
		callback = function(args)
			M.render(args.buf)
		end,
	})

	vim.api.nvim_create_autocmd("User", {
		group = augroup,
		pattern = "DjangoDataRefreshed",
		callback = function(ev)
			if ev.data and ev.data.cache_name == CACHE_NAME then
				M.render_visible_buffers()
			end
		end,
	})

	vim.schedule(function()
		M.render_visible_buffers()
	end)
end

function M.clear(bufnr)
	if vim.api.nvim_buf_is_valid(bufnr) then
		vim.api.nvim_buf_clear_namespace(bufnr, NAMESPACE, 0, -1)
	end
end

function M.render_visible_buffers()
	local seen = {}

	for _, win in ipairs(vim.api.nvim_list_wins()) do
		local bufnr = vim.api.nvim_win_get_buf(win)
		if not seen[bufnr] then
			seen[bufnr] = true
			M.render(bufnr)
		end
	end
end

function M.render(bufnr)
	if not M.__should_render(bufnr) then
		M.clear(bufnr)
		return
	end

	local data = fetcher.get_cached_data(CACHE_NAME)
	if not data or vim.tbl_isempty(data) then
		M.clear(bufnr)
		if utils.is_django_project() then
			fetcher.refresh_with_callback(SCRIPT_NAME, CACHE_NAME, { silent = true })
		end
		return
	end

	local file_path = M.__normalize_path(vim.api.nvim_buf_get_name(bufnr))
	local class_lines = M.__find_class_lines(bufnr)
	if vim.tbl_isempty(class_lines) then
		M.clear(bufnr)
		return
	end

	local class_annotations, method_annotations = M.__collect_annotations(data, file_path, class_lines)

	M.clear(bufnr)
	M.__render_class_annotations(bufnr, class_annotations)
	M.__render_method_annotations(bufnr, method_annotations)
end

function M.__should_render(bufnr)
	if not vim.api.nvim_buf_is_valid(bufnr) or not vim.api.nvim_buf_is_loaded(bufnr) then
		return false
	end

	if vim.bo[bufnr].buftype ~= "" then
		return false
	end

	if vim.bo[bufnr].filetype ~= "python" then
		return false
	end

	local file_path = vim.api.nvim_buf_get_name(bufnr)
	return file_path ~= ""
end

function M.__normalize_path(path)
	if not path or path == "" then
		return ""
	end

	return vim.fs.normalize(vim.fn.fnamemodify(path, ":p"))
end

function M.__find_class_lines(bufnr)
	local class_lines = {}
	local lines = vim.api.nvim_buf_get_lines(bufnr, 0, -1, false)

	for line_number, line in ipairs(lines) do
		local class_name = line:match("^%s*class%s+([%a_][%w_]*)%s*[%(:]")
		if class_name then
			class_lines[class_name] = line_number
		end
	end

	return class_lines
end

function M.__collect_annotations(data, file_path, class_lines)
	local class_patterns = {}
	local method_annotations = {}
	local seen_method_keys = {}

	for _, item in ipairs(data) do
		if M.__is_class_view_item(item, file_path, class_lines) then
			local class_name = item.view_name
			local class_line = class_lines[class_name]
			local pattern = M.__normalize_pattern(item.pattern)

			if pattern then
				class_patterns[class_name] = class_patterns[class_name] or {}
				class_patterns[class_name][pattern] = true

				if item.method and item.line and item.line > 0 and item.line ~= class_line then
					local method_line = item.line
					local key = string.upper(item.method) .. "|" .. pattern

					method_annotations[method_line] = method_annotations[method_line] or {}
					seen_method_keys[method_line] = seen_method_keys[method_line] or {}

					if not seen_method_keys[method_line][key] then
						seen_method_keys[method_line][key] = true
						table.insert(method_annotations[method_line], {
							method = string.upper(item.method),
							pattern = pattern,
						})
					end
				end
			end
		end
	end

	local class_annotations = {}
	for class_name, patterns in pairs(class_patterns) do
		local class_line = class_lines[class_name]
		local root_pattern = M.__pick_root_pattern(vim.tbl_keys(patterns))
		if class_line and root_pattern then
			class_annotations[class_line] = root_pattern
		end
	end

	return class_annotations, method_annotations
end

function M.__is_class_view_item(item, file_path, class_lines)
	if not item or not item.file or not item.view_name then
		return false
	end

	if not class_lines[item.view_name] then
		return false
	end

	return M.__normalize_path(item.file) == file_path
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
	normalized = normalized:gsub("//+", "/")

	if normalized:sub(1, 1) ~= "/" then
		normalized = "/" .. normalized
	end

	return normalized
end

function M.__pick_root_pattern(patterns)
	if not patterns or vim.tbl_isempty(patterns) then
		return nil
	end

	if #patterns == 1 then
		return patterns[1]
	end

	local split_patterns = {}
	local min_segment_count = nil

	for _, pattern in ipairs(patterns) do
		local segments = M.__split_pattern_segments(pattern)
		table.insert(split_patterns, segments)
		if not min_segment_count or #segments < min_segment_count then
			min_segment_count = #segments
		end
	end

	local common_segments = {}
	for index = 1, min_segment_count or 0 do
		local segment = split_patterns[1][index]
		if not segment or M.__is_dynamic_segment(segment) then
			break
		end

		for pattern_index = 2, #split_patterns do
			if split_patterns[pattern_index][index] ~= segment then
				return M.__build_root_pattern(common_segments, patterns)
			end
		end

		table.insert(common_segments, segment)
	end

	return M.__build_root_pattern(common_segments, patterns)
end

function M.__split_pattern_segments(pattern)
	local segments = {}

	for segment in pattern:gmatch("[^/]+") do
		table.insert(segments, segment)
	end

	return segments
end

function M.__is_dynamic_segment(segment)
	return segment:match("^<.+>$") ~= nil
end

function M.__build_root_pattern(common_segments, patterns)
	if common_segments and not vim.tbl_isempty(common_segments) then
		return "/" .. table.concat(common_segments, "/") .. "/"
	end

	table.sort(patterns, function(left, right)
		if #left == #right then
			return left < right
		end
		return #left < #right
	end)

	return patterns[1]
end

function M.__render_class_annotations(bufnr, class_annotations)
	local line_count = vim.api.nvim_buf_line_count(bufnr)

	for line_number, pattern in pairs(class_annotations) do
		if line_number >= 1 and line_number <= line_count then
			vim.api.nvim_buf_set_extmark(bufnr, NAMESPACE, line_number - 1, 0, {
				virt_text = {
					{ " # " .. pattern, "Comment" },
				},
				virt_text_pos = "eol",
				hl_mode = "combine",
			})
		end
	end
end

function M.__render_method_annotations(bufnr, method_annotations)
	local line_count = vim.api.nvim_buf_line_count(bufnr)

	for line_number, items in pairs(method_annotations) do
		table.sort(items, function(left, right)
			if left.method == right.method then
				return left.pattern < right.pattern
			end
			return left.method < right.method
		end)

		if line_number >= 1 and line_number <= line_count then
			vim.api.nvim_buf_set_extmark(bufnr, NAMESPACE, line_number - 1, 0, {
				virt_text = M.__build_method_virt_text(items),
				virt_text_pos = "eol",
				hl_mode = "combine",
			})
		end
	end
end

function M.__build_method_virt_text(items)
	local virt_text = {
		{ " # ", "Comment" },
	}

	for index, item in ipairs(items) do
		if index > 1 then
			table.insert(virt_text, { " · ", "Comment" })
		end

		table.insert(virt_text, { item.method, M.__method_highlight(item.method) })
		table.insert(virt_text, { " " .. item.pattern, "Comment" })
	end

	return virt_text
end

function M.__method_highlight(method)
	local highlights = {
		GET = "String",
		POST = "Special",
		PUT = "Type",
		PATCH = "Identifier",
		DELETE = "WarningMsg",
		HEAD = "PreProc",
		OPTIONS = "PreProc",
	}

	return highlights[method] or "Comment"
end

return M