-- Log where requests are sent from and to
count = 0
max_count = 0
sample = false
log_req = false

-- Loads map into Lua script and sets sample rate
function init_logging(txn)

  -- Load map if not yet loaded
  if map == nil then
    local map_file = txn.f:env('map_file')
    map = Map.new(map_file, Map.str)
  end

  -- Set sample rate
  local sample_rate = txn.f:env('sample_rate')
  if sample_rate ~= nil and not sample then
    sample = true
    if tonumber(sample_rate) > 0 then
      max_count = math.floor(tonumber(sample_rate))
    else
      max_count = 0
    end
    count = 0
  end
end

core.register_action("init_logging", {"tcp-req","http-req"}, init_logging)


-- Logs source service of request
function log_src(txn)

  -- Don't log if map doesn't exist or sample rate is 0
  if map == nil or max_count == 0 then
    return
  end

  -- Sample logs
  if sample then
     count = count + 1
     if count < max_count then
        return
     else
        count = 0
        log_req = true
     end
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
  txn.Info(txn, 'Source service: ' .. src_svc)
end

core.register_action("log_src", {"tcp-req","http-req"}, log_src)


-- Logs destination service of request
function log_dest(txn)
  if sample and not log_req then
     return
  end
  dest_svc = txn.f:be_name()
  txn.Info(txn, 'Destination service: ' .. dest_svc)
  local log_text = 'provenance ' .. src_svc .. ' ' .. dest_svc .. '\n'
  txn.Info(txn, log_text)
  log_req = false
end

core.register_action("log_dest", {"tcp-req","http-req"}, log_dest)