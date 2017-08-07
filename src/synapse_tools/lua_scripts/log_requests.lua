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
     ip = 'nil'
  end
  txn.Info(txn, 'Source ip: ' .. ip)

  local from = map:lookup(ip)
  if from == nil then
     txn.Info(txn, 'Could not find source service')
     from = 'nil'
  end

  local log_text = 'provenance ' .. from .. '\n'
  txn.Info(txn, log_text)
end

core.register_action("log_src", {"tcp-req","http-req"}, log_src)