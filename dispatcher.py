import Model
from Model import Session
import logging
from threading import Thread
from Tools import tools
from Model import Submission
from config import ConfigBorg
import Queue


class Dispatcher(Thread):
    def __init__(self, job_queue, log_queue=None):
        Thread.__init__(self)
        self.config = ConfigBorg()
        self.modules = []
        self.log_queue = log_queue
        self.initModules()
        logging.debug("Dispatcher started with %s modules" % len(self.modules))
        self.queue = job_queue

    def initModules(self):
        for mod_name in self.config.modules:
            exec("from Modules.%s.%s import %s" % (mod_name, mod_name, mod_name))
            exec("mod_inst = %s(log_queue=self.log_queue)" % mod_name)
            self.modules.append(mod_inst)

    def run(self):
        #print self.log_queue.__dict__['_opid']
        #tools.EnableLogging(self.log_queue)
        #self.db = Model.Db()
        self.eventLoop()
        #self.db.close()
        logging.warning("DISPATCHER ENDED")

    def eventLoop(self):
        print "DISPATCHER LOOP STARTED"
        while True:

            # Get Job & Dispatch it
            try:
                logging.debug("Waiting for a job")
                job = self.queue.get(block=True, timeout=15)
                self.queue.task_done()
                if job is None:
                    logging.warning("Dispatcher received None, exiting...")
                    break
                submission = self.generateSubmission(job)
                # Dispatch Job
                logging.debug("Got %s, dispatching to modules" % submission)
                self.analyseSubmission(submission)
            except Queue.Empty:
                logging.debug("Timeout while waiting for job...")

            # Get results, handle this asynchronously
            for m in self.modules:
                try:
                    result = m.result_queue.get(block=True, timeout=1)
                    m.result_queue.task_done()
#                    logging.debug("Got result %s" % result)
                    self.handleResult(m, result)
                except Queue.Empty:
                    logging.debug("No result for %s..." % m)

        # Terminate modules
        logging.debug("Sending termination job to every modules...")
        for m in self.modules:
            m.analyse(None)  # Send the exit signal to modules, blocking

        # Handle remaining results every modules are already stopped
        logging.debug("Looking for remaining results in queue")
        for m in self.modules:
            while True:
                try:
                    r = m.result_queue.get_nowait()
                    m.result_queue.task_done()
                    self.handleResult(m, r)
                except Queue.Empty:
                    break

    def handleResult(self, module, result):
        # TODO handle results (save to DB based on module name, Result object linked to the Submission
#        logging.debug("Got result %s from %s, saving to Db..." % (result, module))
        result = Session().merge(result)
        submission = result.submission
        Session().refresh(submission)
        submission.results += 1
        Session().commit()

    def generateSubmission(self, job):
        file_path = job['path']
        file_name = job['name']
        submission = Model.Submission(file_path, file_name)
        return submission

    def analyseSubmission(self, submission):
        sid = submission.id
        Session().expunge(submission)
        if type(submission) != Model.Submission:
            raise Exception("Invalid submission object")
        nb_of_modules_for_this_submission = 0
        for m in self.modules:
            if m.analyse(submission) is True:
                nb_of_modules_for_this_submission += 1
        submission = Session().query(Submission).filter(Submission.id == sid).one()
        submission.working_modules = nb_of_modules_for_this_submission
        Session.commit()


if __name__ == '__main__':
    d = Dispatcher(None)
