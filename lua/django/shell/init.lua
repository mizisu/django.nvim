local M = {}

local utils = require("django.utils")

--- Get shell config from django.config
--- @return table
function M.__get_config()
	local config = require("django.config")
	return config.current.shell or {}
end

--- Build the shell command string
--- @return string Command string
function M.__build_command()
	local cfg = M.__get_config()
	local python = utils.get_python_path()
	local command = cfg.command or "shell"

	return python .. " manage.py " .. command
end

--- Build terminal options
--- @return table
function M.__build_opts()
	local cfg = M.__get_config()
	local opts = {
		win = { position = cfg.position or "bottom" },
	}

	-- Only include env if it has values
	if cfg.env and next(cfg.env) then
		opts.env = cfg.env
	end

	return opts
end

--- Get Snacks module
--- @return table|nil
function M.__get_snacks()
	local ok, Snacks = pcall(require, "snacks")
	if not ok then
		vim.notify("snacks.nvim is required for Django shell", vim.log.levels.ERROR)
		return nil
	end
	return Snacks
end

--- Toggle Django shell
function M.toggle()
	local Snacks = M.__get_snacks()
	if not Snacks then
		return
	end

	local cmd = M.__build_command()
	Snacks.terminal.toggle(cmd, M.__build_opts())
end

--- Open Django shell
function M.open()
	local Snacks = M.__get_snacks()
	if not Snacks then
		return
	end

	local cmd = M.__build_command()
	Snacks.terminal.open(cmd, M.__build_opts())
end

--- Close Django shell
function M.close()
	local Snacks = M.__get_snacks()
	if not Snacks then
		return
	end

	local cmd = M.__build_command()
	local term = Snacks.terminal.get(cmd, { create = false })
	if term then
		term:hide()
	end
end

--- Send code to shell
--- @param code string|string[] Code to send
function M.send(code)
	local Snacks = M.__get_snacks()
	if not Snacks then
		return
	end

	local cmd = M.__build_command()

	-- Get or create terminal
	local term = Snacks.terminal.get(cmd, M.__build_opts())
	if not term then
		return
	end

	local lines = type(code) == "table" and code or { code }
	local text = table.concat(lines, "\n") .. "\n"

	local chan = vim.bo[term.buf].channel
	if chan and chan > 0 then
		vim.api.nvim_chan_send(chan, text)
	end

	if not term:win_valid() then
		term:show()
	end
	term:focus()
	vim.cmd("startinsert")
end

--- Send current line to shell
function M.send_line()
	local line = vim.api.nvim_get_current_line()
	M.send(line)
end

--- Send visual selection to shell
function M.send_selection()
	-- Exit visual mode first to set '< and '> marks
	vim.api.nvim_feedkeys(vim.api.nvim_replace_termcodes("<Esc>", true, false, true), "nx", false)

	-- Get selection range from marks (1-indexed)
	local start_line = vim.fn.getpos("'<")[2]
	local end_line = vim.fn.getpos("'>")[2]

	-- Validate marks
	if start_line == 0 or end_line == 0 then
		return
	end

	local lines = vim.api.nvim_buf_get_lines(0, start_line - 1, end_line, false)

	if #lines == 0 then
		return
	end

	M.send(lines)
end

return M
