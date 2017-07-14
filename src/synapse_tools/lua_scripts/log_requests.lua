-- Log where requests are sent from and to

SYNAPSE_PATH = '~/pg/synapse-tools/'
LOGFILE_PATH = SYNAPSE_PATH + 'src/synapse_tools/logs/'
-- mp = Map.new("maps/ip_svc.map", Map.str)

function log_src(txn)
  local ip_from = txn.f:src()
  local log_text = 'Logging source: ' .. txn.f:src()
  txn.Info(txn, log_text)

  local log_file = io.open(LOGFILE_PATH + 'demo_logs', "a")
  log_file:write(log_text)
  log_file:close(log_file)

  -- if ip_from == nil then
     -- return 'N/A'
  -- end
  
  -- local svc_from = mp:lookup(ip_from)
  -- if svc_from == nil then
  --    return 'N/A'
  -- end
  -- txn.set_var(txn, 'from_svc', svc_from)
  -- txn.Info(txn, 'From: ' .. svc_from)
end

core.register_action("log_src", {"tcp-req","http-req", log_src)

function log_dest(txn)
  -- local from_svc = txn.get_var(txn, 'txn.from_svc')
  -- local to_svc = txn.get_var(txn, 'req.backend_name')
  -- local date = txn.sc:http_date(txn.f:date())
  -- local log_text = date .. " Request from: " .. from_svc .. " Request to: " .. to_svc .. "\n"
  -- txn.Info(txn, log_text)

  local log_text = 'Logging destination'
  txn.Info(txn, log_text)

  local log_file = io.open(LOGFILE_PATH + 'demo_logs', 'a')
  log_file:write(log_text)
  log_file:close(log_file)
end

core.register_action("log_dest", {"tcp-req","http-req"}, log_dest)
