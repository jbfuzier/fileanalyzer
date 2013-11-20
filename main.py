import logging
from Tools.tools import EnableLogging


from config import ConfigBorg


if __name__ == '__main__':
    # Start logging thread -> to log with multiple processes, not needed for threads
    # loggingqueue = QueueLogging()
    # Configure logging for main process
    # EnableLogging(loggingqueue.queue)
    #print loggingqueue.queue.__dict__['_opid']
    EnableLogging()
    logging.debug("test")

    import flaskserver
    flaskserver.start_flask()

    #f = {"path": "c:\\windows\\system32\\calc.exe", "name": "calc.exe"}
    #g = {"path": "upload\\80c10ee5f21f92f89cbc293a59d2fd4c01c7958aacad15642558db700943fa22", "name": "calc.exe"}
    #job_queue.put(g)
    #job_queue.put(f)
    #job_queue.put(f)
    #job_queue.put(None)

    #d.join()
    # Stopping logging
#    loggingqueue.queue.put(None)
#    loggingqueue.join()
#http://stackoverflow.com/questions/7478403/sqlalchemy-classes-across-files