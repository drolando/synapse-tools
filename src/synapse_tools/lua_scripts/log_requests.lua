-- Log where requests are sent from and to
sample_rate = 0

-- Loads map into Lua script and sets sample rate
function init_logging(txn)

  -- Load map if not yet loaded
  if map == nil then
    local map_file = txn.f:env('map_file')
    map = Map.new(map_file, Map.str)
  end

  -- Set sample rate
  if txn.f:env('sample_rate') ~= nil then
     sample_rate = tonumber(txn.f:env('sample_rate'))
  else
     sample_rate = 1
  end
end

core.register_action("init_logging", {"tcp-req","http-req"}, init_logging)


-- Logs source and destination service of request
function log_provenance(txn)

  -- Don't log if map doesn't exist or sampled out
  if (map == nil) or (sample_rate == 0) or (math.random() > sample_rate) then
    return
  end

  -- Get source service
  local ip = txn.f:src()
  if ip == nil then
     ip = 'nil'
  end
  src_svc = map:lookup(ip)
  if src_svc == nil then
     src_svc = ip
  end

  -- Get destination service
  dest_svc = txn.f:be_name()
  local log_text = 'provenance ' .. src_svc .. ' ' .. dest_svc .. '\n'
  txn.Info(txn, log_text)
end

core.register_action("log_provenance", {"tcp-req","http-req"}, log_provenance)