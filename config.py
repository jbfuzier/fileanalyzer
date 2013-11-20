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
    modules = ['Exiftools']
    logging = {
        'filepath': 'logger.log',

    }
    worker_threads = 2
    flask = {'upload_dir': 'upload'}
    db_path = 'sqlite:///db.sqlite'

