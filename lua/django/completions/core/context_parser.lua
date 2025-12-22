local M = {}

local async = require("django.async")

--- Parse context for Django completions
--- Must be called within async.run()
--- @param bufnr number Buffer number
--- @param line number Line number (0-indexed)
--- @param col number Column number (0-indexed)
--- @return table|nil context { model_name, method, prefix }
function M.parse(bufnr, line, col)
	-- 1. Parse prefix from current line
	local prefix = M.__parse_prefix(bufnr, line, col)
	if not prefix then
		return nil
	end

	-- 2. Get method and model_name from LSP hover
	local method, model_name = M.__get_method_info(bufnr, line, col)
	if not method or not model_name then
		return nil
	end

	return {
		model_name = model_name,
		method = method,
		prefix = prefix,
	}
end

--- Parse prefix from current line (the part user is typing)
--- @param bufnr number Buffer number
--- @param line number Line number (0-indexed)
--- @param col number Column number (0-indexed)
--- @return string|nil prefix
function M.__parse_prefix(bufnr, line, col)
	local lines = vim.api.nvim_buf_get_lines(bufnr, line, line + 1, false)
	if not lines or not lines[1] then
		return nil
	end

	local before_cursor = lines[1]:sub(1, col)

	-- Get last argument (after last comma, opening paren, or equals sign)
	local current_arg = before_cursor:match("[^,(=]*$") or ""
	current_arg = current_arg:gsub("^%s+", "")

	-- Remove leading quote if present (for string arguments like "author")
	if current_arg:match('^["\']') then
		current_arg = current_arg:sub(2)
	end

	-- Extract prefix (word characters and underscores only)
	local prefix = current_arg:match("^([%w_]*)$")

	return prefix
end

--- Get method and model_name from LSP hover on the call target
--- Must be called within async.run()
--- @param bufnr number Buffer number
--- @param line number Line number (0-indexed)
--- @param col number Column number (0-indexed)
--- @return string|nil method, string|nil model_name
function M.__get_method_info(bufnr, line, col)
	local method_infos = M.__find_all_method_infos(bufnr, line, col)
	if not method_infos or #method_infos == 0 then
		return nil, nil
	end

	-- The last method is the current one (e.g., update, values)
	local current_method = method_infos[#method_infos]

	-- Try hover on each method from current to previous until we find a model
	-- Some methods (like update) return non-QuerySet types, so we need to check previous methods
	for i = #method_infos, 1, -1 do
		local info = method_infos[i]
		local params = {
			textDocument = vim.lsp.util.make_text_document_params(bufnr),
			position = { line = info.line, character = info.target_col },
		}

		local err, result = async.lsp_request(bufnr, "textDocument/hover", params)
		if not err and result and result.contents then
			local model_name = M.__extract_model_from_hover(result.contents)
			if model_name then
				return current_method.method, model_name
			end
		end
	end

	return nil, nil
end

--- Find all method infos in the chain before cursor position
--- @param bufnr number Buffer number
--- @param line number Current line number (0-indexed)
--- @param col number Cursor column (0-indexed)
--- @return table[] Array of { line, method, target_col }
function M.__find_all_method_infos(bufnr, line, col)
	-- Search current line and up to 20 lines above
	local start_line = math.max(0, line - 20)
	local lines = vim.api.nvim_buf_get_lines(bufnr, start_line, line + 1, false)

	-- Search from bottom to top (closest match first)
	for i = #lines, 1, -1 do
		local line_text = lines[i]
		local actual_line = start_line + i - 1
		local search_limit = (actual_line == line) and (col + 1) or #line_text

		-- Find ALL .method( patterns before cursor position
		local methods = {}
		local pos = 1
		while pos <= search_limit do
			local dot_pos, end_pos, method_name = line_text:find("%.([%w_]+)%s*%(", pos)
			if not dot_pos or dot_pos > search_limit then
				break
			end
			table.insert(methods, {
				line = actual_line,
				method = method_name,
				target_col = dot_pos, -- method name position (0-indexed)
			})
			pos = end_pos + 1
		end

		if #methods > 0 then
			return methods
		end
	end

	return {}
end

--- Extract model name from hover contents
--- Looks for "Manager[Model]" or "QuerySet[Model]" pattern
--- @param contents any LSP hover contents
--- @return string|nil model_name
function M.__extract_model_from_hover(contents)
	local text = ""

	if type(contents) == "string" then
		text = contents
	elseif type(contents) == "table" then
		if contents.value then
			text = contents.value
		elseif contents[1] then
			text = type(contents[1]) == "string" and contents[1] or (contents[1].value or "")
		end
	end

	-- Extract model from various patterns:
	-- "Manager[Post]", "BaseManager[Post]", "QuerySet[Post]", "ValuesQuerySet[Post, ...]"
	local model_name = text:match("Manager%[([%w_]+)") or text:match("QuerySet%[([%w_]+)")

	return model_name
end

return M
