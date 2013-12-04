import os

#DO NOT PUT SHARED DYNAMIC VALUES IN HERE, IT IS RECOMPUTED IN EVERY PROCESS
class ConfigBorg:  # Shared state class (singleton like http://code.activestate.com/recipes/66531/ )
    __shared_state = {}
    print "CONFIG BORG INIT"
    def __init__(self):
        os.environ['PATH'] += ";Tools"  # For win32api dll load
        self.__dict__ = self.__shared_state
    # and whatever else you want in your class -- that's all!
    # This is evaluated only once in a process, but several times in different processes
    exiftool = {'win32_binary_location': 'Tools\\exiftool.exe'}
    entropy = {'output_dir': 'output\\entropy'}
    modules = ['Exiftools', 'Entropy', 'VirusTotal', 'HashKB']
    logging = {
        'filepath': 'logger.log',

    }
    virustotal = {'submit_unknown': True, 'apikey': '0ef995125afc13d4a0822753c776e65072d1cc2078e8892217de1d61e8d49750', 'request_rate': 4, 'worker_threads' : 1}
    hashKB = {'worker_threads' : 1, 'dbpath': 'd:\\LocalData\\a189493\\Desktop\\NOT_BACKUPED\\NSLR.sqlite'}
    worker_threads = 2
    flask = {'upload_dir': 'upload'}
    db_path = 'sqlite:///db.sqlite?check_same_thread=False'
    proxyhandler = {'https': 'https://:3128', 'http': 'http://:3128'}


