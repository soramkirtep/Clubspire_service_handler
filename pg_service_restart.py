import subprocess, time, os, datetime, win32serviceutil, winreg

logging = "c:\\Users\\maros_petrik\\Documents\\0 Coding_playground\\Python\\pg_service_restart\\log.txt"

# First delete postmaster PID which could hang with wrong information after system reboot, second kill postgres malfunctional processes
def delete_postgres_processes(path):
    try:
        postmaster_pid = str(path + '\\postmaster.pid')
        if os.path.exists(postmaster_pid):
            # os.remove(postmaster_pid)
            print('There is file with name ' + postmaster_pid)
        else:
            print('There is not file with name ' + postmaster_pid)

        process_exists = os.system("taskkill /im postgres.exe /f")
        if process_exists != "0":
          print('There is not process with name ' + POSTGRES_PROCESS)
        else:    
            print('Process ' + POSTGRES_PROCESS + 'has been stopped sucessfully.')
    except WindowsError:
        return None

# Get service version and data
def get_service(name):
    try:
        lookup_service = str(subprocess.check_output('sc query state=all | find "SERVICE_NAME: ' + name +'"', shell=True))
        if not lookup_service:
          return ('There is not ' + name + ' service installed')
        service_name = lookup_service.split()[1]
        service = service_name.split('\\')[0]
        return service
    except WindowsError:
        return None

# Get Postgres data location
def postgres_reg_data_path():
    try:
        REG_PATH = r"SYSTEM\\CurrentControlSet\\Services\\" + str(POSTGRES_SERVICE)
        registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_PATH, 0,winreg.KEY_READ)
        value, regtype = winreg.QueryValueEx(registry_key, 'ImagePath')
        winreg.CloseKey(registry_key)
        path = value.split('"')[-2]
        return path
    except WindowsError:
        return None

def service_status(service):
  status = win32serviceutil.QueryServiceStatus(service)[1]
  return status

def start_service(service):
    subprocess.run('net start '+ service)

def stop_service(service):
    subprocess.run('net stop '+ service +' /yes')   

# Get PID of given process name
def get_pid(process_name):
  try:
    lookup_process = str(subprocess.check_output('tasklist | find "'+ process_name + '"', shell=True))
    if lookup_process != 1:
      result = lookup_process.split()[1]
      return result
    else:
      print("There is not running any process with name " + process_name)
  except WindowsError:
    return None

# Check connection on port
def check_connection(process_id):
  try:
    connection = str(subprocess.call('netstat -ano | find ":8093" | find "' + process_id + '"', shell=True))    
    if connection != "1":
      DEPLOY_LOOP = 0
      while DEPLOY_LOOP < 90:
        connection_state = str(subprocess.check_output('netstat -ano | find ":8093" | find "' + process_id + '"', shell=True))
        print(connection_state.split()[-3])
        if connection_state.split()[-3] != "0.0.0.0:0":
          print('Connection has been established on IP ' + connection_state.split()[-3])
          break
        time.sleep(10)
        DEPLOY_LOOP += 1
        print('Connection is not established yet, loop number ' + str(DEPLOY_LOOP) + ' of 20 attempts.')
    else:
      print('Communication was not established with clubspire process ' + process_id)
      print('Connection check ended with error status ' + connection)
      return connection
  except WindowsError:
        return None


if __name__ == '__main__':

  JBOSS_HOME = os.environ['JBOSS_HOME']
  PG_SERVICELOG = JBOSS_HOME + "\\..\\scripts\\PGlog.txt"
  POSTGRES_PROCESS = 'postgres.exe'
  JBOSS_PROCESS = 'JBossService.exe'
  CLUBSPIRE_SERVICE = get_service('clubspire')
  POSTGRES_SERVICE = get_service('postgres')
  POSTGRES_DATA = postgres_reg_data_path()
  CONNECTION_LOOP = 0
  CONNECTION_LOOP2 = 0

# Checking postgres if running. If not repair and start postgres.
  if service_status(POSTGRES_SERVICE) == 1:
    delete_postgres_processes(POSTGRES_DATA)
    start_service(POSTGRES_SERVICE)
  else:
    print('Postgres is running correctly')

# Checking clubspire if running.
  if service_status(CLUBSPIRE_SERVICE) == 1: 
    print("Clubspire is stopped, starting Clubspire...")
    print(datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
    while CONNECTION_LOOP < 20:
      start_service('clubspire')
      time.sleep(20)
      clubspire_process_id = get_pid(JBOSS_PROCESS)
      established = check_connection(clubspire_process_id) 
      if established == "1":
        print(datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
        stop_service('clubspire')
      else:
        break
      CONNECTION_LOOP += 1
    print(datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
    print('Loop restarting clubspire ended successfully...')
    # Starting Webclient
    start_service('clubspire-webclient')
    print('All services are running properly now.')
  elif service_status(CLUBSPIRE_SERVICE) == 4:
    print('Clubspire service is running, verify is comunication is ok.')
    while CONNECTION_LOOP2 < 20:
      clubspire_process_id = get_pid(JBOSS_PROCESS)
      established = check_connection(clubspire_process_id)
      if established == "1":
        print(datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
        stop_service('clubspire')
        time.sleep(20)
        start_service('clubspire')
      else:
        break
      CONNECTION_LOOP2 += 1
    print(datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
  print('Loop restarting clubspire ended successfully...')
  # Starting Webclient
  start_service('clubspire-webclient')
  print('All services are running properly.')
  

        
      