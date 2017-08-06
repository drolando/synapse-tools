-- Log where requests are sent from and to

map_file = '/etc/maps/ip_to_svc.map'
map = Map.new(map_file, Map.str)

function log_src(txn)
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