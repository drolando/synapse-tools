-- Log where requests are sent from and to

-- Loads map into Lua script
function load_map(txn)
  if map ~= nil then
    return
  end

  local map_file = txn.f:env('map_file')
  txn.Info(txn, 'Mapfile: ' .. map_file)
  map = Map.new(map_file, Map.str)
end

core.register_action("load_map", {"tcp-req","http-req"}, load_map)


-- Logs source service of request
function log_src(txn)
  if map == nil then
    return
  end

  local ip = txn.f:src()
  if ip == nil then
     txn.Info(txn, 'Could not find source IP address')
     ip = 'nil'
  end
  txn.Info(txn, 'Source ip: ' .. ip)

  src_svc = map:lookup(ip)
  if src_svc == nil then
     txn.Info(txn, 'Could not find source service')
     src_svc = 'nil'
  end

  txn.Info(txn, 'Source service: ' .. src_svc)
end

core.register_action("log_src", {"tcp-req","http-req"}, log_src)


-- Logs destination service of request
function log_dest(txn)
  dest_svc = txn.f:be_name()
  txn.Info(txn, 'Destination service: ' .. dest_svc)
  local log_text = 'provenance ' .. src_svc .. ' ' .. dest_svc .. '\n'
  txn.Info(txn, log_text)
end

core.register_action("log_dest", {"tcp-req","http-req"}, log_dest)