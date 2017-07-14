-- Log where requests are sent from and to

LOGFILE_PATH = '/var/log/'

function log_src(txn)
  local ip_from = txn.f:src()
  local log_text = 'Logging source: ' .. txn.f:src()
  txn.Info(txn, log_text)

  local log_file = io.open(LOGFILE_PATH + 'demo_logs', "a")
  log_file:write(log_text)
  log_file:close(log_file)
end

core.register_action("log_src", {"tcp-req","http-req", log_src)

function log_dest(txn)
  local log_text = 'Logging destination'
  txn.Info(txn, log_text)

  local log_file = io.open(LOGFILE_PATH + 'demo_logs', 'a')
  log_file:write(log_text)
  log_file:close(log_file)
end

core.register_action("log_dest", {"tcp-req","http-req"}, log_dest)
