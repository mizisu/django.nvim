local M = {}

--- Execute vim.system as a coroutine
--- @param cmd table Command arguments
--- @param opts table|nil System options
--- @return table Result object with code, stdout, stderr
function M.system(cmd, opts)
	local co = coroutine.running()
	if not co then
		error("M.system must be called within a coroutine")
	end

	vim.system(cmd, opts, function(result)
		vim.schedule(function()
			coroutine.resume(co, result)
		end)
	end)

	return coroutine.yield()
end

--- Execute vim.lsp.buf_request as a coroutine
--- @param buf number Buffer number
--- @param method string LSP method name
--- @param params table LSP request params
--- @return any err, any result
function M.lsp_request(buf, method, params)
	local co = coroutine.running()
	if not co then
		error("M.lsp_request must be called within a coroutine")
	end

	vim.lsp.buf_request(buf, method, params, function(err, result)
		vim.schedule(function()
			coroutine.resume(co, err, result)
		end)
	end)

	return coroutine.yield()
end

--- Wait for specified milliseconds
--- @param ms number Milliseconds to wait
function M.wait(ms)
	local co = coroutine.running()
	if not co then
		error("M.wait must be called within a coroutine")
	end

	vim.defer_fn(function()
		coroutine.resume(co)
	end, ms)

	coroutine.yield()
end

--- Check if currently running inside a coroutine
--- @return boolean
function M.in_coroutine()
	return coroutine.running() ~= nil
end

--- Run an async function in a coroutine, or execute directly if already in one
--- @param fn function Function to run (should use M.system, M.lsp_request, etc.)
function M.run(fn)
	if M.in_coroutine() then
		fn()
		return
	end

	local co = coroutine.create(fn)

	local function step(...)
		local results = { coroutine.resume(co, ...) }
		local ok = results[1]

		if not ok then
			local err = results[2]
			vim.schedule(function()
				vim.notify("Async error: " .. tostring(err), vim.log.levels.ERROR)
			end)
		end
	end

	step()
end

return M
