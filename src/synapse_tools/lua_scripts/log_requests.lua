-- Log where requests are sent from and to

LOGFILE_PATH = '/var/log/'

function log_src(txn)
  local ip = "N/A"
  if txn.f:src() ~= nil then
     ip = txn.f:src()
  end

  local from = "N/A"
  local hdr = txn.http:req_get_headers()
  if hdr["from"] ~= nil then
    from = hdr["from"][0]
  end

  local log_text = 'Source: ' .. ip .. ' From: ' .. from .. '\n'
  txn.Info(txn, log_text)

  local fname = LOGFILE_PATH .. 'demo_log'
  local log_file = io.open(fname, 'a')
  log_file:write(log_text)
  io.close(log_file)
end

core.register_action("log_src", {"tcp-req","http-req"}, log_src)

function log_dest(txn)
  local log_text = 'Logging destination'
  txn.Info(txn, log_text)

  local fname = LOGFILE_PATH .. 'demo_log'
  local log_file = io.open(fname, 'a')
  log_file:write(log_text)
  log_file:close(log_file)
end

core.register_action("log_dest", {"tcp-req","http-req"}, log_dest)
