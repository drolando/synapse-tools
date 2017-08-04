-- Log where requests are sent from and to

LOG_WITH_SVC = '/var/log/log_with_svc'
LOG_WITHOUT_SVC = '/var/log/log_without_svc'
MAP_WITH_SVC = '/etc/maps/map_with_svc.map'
MAP_WITHOUT_SVC = '/etc/maps/map_without_svc.map'


function log_src(txn)
  local map = Map.new(MAP_WITH_SVC, Map.str)
  write_log(txn, map, LOG_WITH_SVC)
  map = Map.new(MAP_WITHOUT_SVC, Map.str)
  write_log(txn, map, LOG_WITHOUT_SVC)
end

core.register_action("log_src", {"tcp-req","http-req"}, log_src)

function write_log(txn, map_file, log_filename)
  local ip = txn.f:src()
  if ip == nil then
     ip = 'nil'
  end
  txn.Info(txn, 'Source ip: ' .. ip)

  local from = map_file:lookup(ip)
  if from == nil then
     txn.Info(txn, 'Could not find source service')
     from = 'nil'
  end

  local log_text = 'provenance ' .. ip .. ' ' .. from .. '\n'
  txn.Info(txn, log_text)
  local log_file = io.open(log_filename, 'a')
  log_file:write(log_text)
  io.close(log_file)
end

function log_dest(txn)
  local log_text = 'Logging destination'
  txn.Info(txn, log_text)

  local log_file = io.open(LOG_FILE, 'a')
  log_file:write(log_text)
  log_file:close(log_file)
end

core.register_action("log_dest", {"tcp-req","http-req"}, log_dest)
