local M = {}

--- Execute vim.system as a coroutine
--- @param cmd table Command arguments
--- @param opts table|nil System options
--- @return table Result object with code, stdout, stderr
function M.system(cmd, opts)
	if not M.in_coroutine() then
		error("M.system must be called within async.run()")
	end

	local co = coroutine.running()

	vim.system(cmd, opts, function(result)
		vim.schedule(function()
			M.__resume(co, result)
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
	if not M.in_coroutine() then
		error("M.lsp_request must be called within async.run()")
	end

	local co = coroutine.running()

	vim.lsp.buf_request(buf, method, params, function(err, result)
		vim.schedule(function()
			M.__resume(co, err, result)
		end)
	end)

	return coroutine.yield()
end

--- Wait for specified milliseconds
--- @param ms number Milliseconds to wait
function M.wait(ms)
	if not M.in_coroutine() then
		error("M.wait must be called within async.run()")
	end

	local co = coroutine.running()

	vim.defer_fn(function()
		M.__resume(co)
	end, ms)

	coroutine.yield()
end

--- Check if the current context can yield to its resumer
--- @return boolean
function M.in_coroutine()
	-- Neovim 0.12 returns the main thread from coroutine.running(), so
	-- coroutine.running() alone cannot distinguish the main thread from a
	-- resumable coroutine. coroutine.isyieldable() reports whether yielding
	-- is actually possible in the current context.
	if coroutine.isyieldable then
		return coroutine.isyieldable()
	end

	return coroutine.running() ~= nil
end

--- Run an async function in a coroutine, or execute directly if already in one
--- @param fn function Function to run (should use M.system, M.lsp_request, etc.)
function M.run(fn)
	if M.in_coroutine() then
		fn()
		return
	end

	M.__resume(coroutine.create(fn))
end

--- Resume a coroutine and notify on error
--- @param co thread Coroutine to resume
--- @param ... any Values passed to the coroutine
function M.__resume(co, ...)
	local ok, err = coroutine.resume(co, ...)
	if not ok then
		vim.schedule(function()
			vim.notify("Async error: " .. tostring(err), vim.log.levels.ERROR)
		end)
	end
end

return M
