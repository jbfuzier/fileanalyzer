import hashlib
from Tools.exiftool import ExifTool
from config import ConfigBorg
from multiprocessing import Process, Queue
from Tools.QueueLoggingHandler import QueueHandler
import logging

config = ConfigBorg()

def exiftool():
    # TODO remove from shared state ?
    #config = ConfigBorg()
    #if not 'instance' in config.exiftool:
    print("Starting EXIFTOOL")
    et = ExifTool(executable_=config.exiftool['win32_binary_location'])
    et.start()
        #config.exiftool['instance'] = et
    #else:
     #   et = config.exiftool['instance']
    return et

def hashdigest(path):
    stream = open(path, 'rb')
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    for block in stream.read(1024 * 1024 * 10):
        md5.update(block)
        sha1.update(block)
        sha256.update(block)
    return {'md5': md5.hexdigest(), 'sha1': sha1.hexdigest(), 'sha256': sha256.hexdigest()}




def EnableLogging():
    # TODO handle config flags
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # send all messages, for demo; no other level or filter logic applied.
    h = logging.handlers.RotatingFileHandler(config.logging['filepath'], 'a', 300, 10)
    log_format_console = """%(threadName)-10s - %(levelname)-8s: %(filename)s(%(module)s.%(funcName)s:%(lineno)d)-> %(message)s"""
    log_format_file = """%(asctime)s-20s - %(processName)-10s - %(levelname)-8s: %(filename)s(%(module)s.%(funcName)s:%(lineno)d)-> %(message)s"""
    f = logging.Formatter(log_format_file)
    h.setFormatter(f)
    #root.addHandler(h)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(fmt=logging.Formatter(fmt=log_format_console))
    root.addHandler(console)


"""
    Multiprocess logging system
"""


def EnableLoggingMp(q):
    print q.__dict__['_opid']
    h = QueueHandler(q)  # Just the one handler needed
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(logging.DEBUG)  # send all messages, for demo; no other level or filter logic applied.


class QueueLogging(Process):
    def __init__(self):
        Process.__init__(self)
        self.config = ConfigBorg()
        self.queue = Queue()
        self.start()

    def run(self):
        self.listener()

    def listener(self):
        root = logging.getLogger()
        h = logging.handlers.RotatingFileHandler(self.config.logging['filepath'], 'a', 300, 10)
        log_format_console = """%(processName)-10s - %(levelname)-8s: %(filename)s(%(module)s.%(funcName)s:%(lineno)d)-> %(message)s"""
        log_format_file = """%(asctime)s-20s - %(processName)-10s - %(levelname)-8s: %(filename)s(%(module)s.%(funcName)s:%(lineno)d)-> %(message)s"""
        f = logging.Formatter(log_format_file)
        h.setFormatter(f)
        root.addHandler(h)
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(fmt=logging.Formatter(fmt=log_format_console))
        root.addHandler(console)
        while True:
            try:
                record = self.queue.get()
                if record is None:  # We send this as a sentinel to tell the listener to quit.
                    break
                logger = logging.getLogger(record.name)
                logger.handle(record)  # No level or filter logic applied - just do it!
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                import sys, traceback
                print >> sys.stderr, 'Whoops! Problem:'
                traceback.print_exc(file=sys.stderr)
        logging.warning("Stopping logging")