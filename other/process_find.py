import psutil
def now_ps_find(word : str):
    for proc in psutil.process_iter():
        try:
            # Get process name & pid from process object.
            processName = proc.name()
            if processName.lower().find(word.lower()) != -1:
                # print(processName)
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) :
            pass
    return False