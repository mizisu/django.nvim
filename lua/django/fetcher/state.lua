local M = {}

local fetching = {}
local pending_timers = {}

--- Check if a cache is currently being fetched
--- @param cache_name string
--- @return boolean
function M.is_fetching(cache_name)
	return fetching[cache_name] == true
end

--- Set fetching state for a cache
--- @param cache_name string
--- @param value boolean
function M.set_fetching(cache_name, value)
	fetching[cache_name] = value
end

--- Cancel and cleanup pending timer for a cache
--- @param cache_name string
function M.cancel_pending_timer(cache_name)
	local timer = pending_timers[cache_name]
	if timer then
		timer:stop()
		timer:close()
		pending_timers[cache_name] = nil
	end
end

--- Set a pending timer for a cache
--- @param cache_name string
--- @param timer userdata
function M.set_pending_timer(cache_name, timer)
	pending_timers[cache_name] = timer
end

return M
