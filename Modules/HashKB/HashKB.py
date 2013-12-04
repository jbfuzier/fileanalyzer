from threading import Thread
from Queue import Queue
from config import ConfigBorg
import logging
from Model import Report, ReportSection, Session, Submission
from json import JSONEncoder
import sqlite3
__ModuleName__ = "HashKB"

# TODO Add custom hash db

class HashKB():
    def __init__(self, log_queue=None):
        self.workers = []
        self.queue = Queue()
        self.result_queue = Queue()
        self.log_queue = log_queue
        self.config = ConfigBorg()
        self.__init_workers()

    def __init_workers(self):
        logging.debug("Spawning workers")
        dbpath = self.config.hashKB['dbpath']
        for w in range(self.config.hashKB['worker_threads']):
            p = skeletonWorker(self.queue, self.result_queue, self.log_queue, dbpath)
            self.workers.append(p)
            p.start()
        logging.debug("Done : %s" % self.workers)

    def analyse(self, submission):
        if submission is None:
            logging.debug("Notifying every worker to exit...")
            for m in self.workers:
                self.queue.put(None)
                logging.debug("Waiting for %s worker to exit" % m)
            for m in self.workers:
                m.join()
                logging.debug("%s worker exit success" % m)
            logging.debug("Module ended")
            return False
        else:
            return self._filter_submissions(submission)

    def reportAlreadyAvailable(self, submission):
        return len([r for s in submission.file.submissions for r in s.reports if r.module == __ModuleName__]) != 0

    def _filter_submissions(self, submission):
        # TODO Filter by file type
        if not self.reportAlreadyAvailable(submission):  # Check if a report has already been generated for this file
            return self._accept(submission)
        else:
            return self._reject(submission)

    def _accept(self, submission):
        logging.debug("Accepted")
        self.queue.put(submission.id)
        return True

    def _reject(self, submission):
        logging.debug("Rejected")
        return False


class skeletonWorker(Thread):
    def __init__(self, job_queue, result_queue, log_queue, dbpath):
        Thread.__init__(self)
        self.log_queue = log_queue
        self.queue = job_queue
        self.result_queue = result_queue
        self.dbpath = dbpath

    def run(self):
    #if self.log_queue is not None:
    #EnableLogging(self.log_queue)
        self.db = sqlite3.connect(self.dbpath)
        while True:
            logging.debug("Waiting for a job...")
            job = self.queue.get()
            if job is None:
                logging.warning("Got None job, exiting...")
                self.queue.task_done()
                break
            logging.debug("Got a job %s"%(job))
            self._do_work(job)
            logging.debug("job done %s"%(job))
            self.queue.task_done()
        return 0

    def _do_work(self, submission_id):
        s = Session()
        submission = s.query(Submission).filter(Submission.id==submission_id).one()
        r = Report(
            module=__ModuleName__,
            short="Short desc...",
            full="",
            submission=submission
        )
        s.add(r)
        #Do the actual work
        sql = """select sha1, md5, FileName, FileSize, ProductName, ProductVersion, Language, ApplicationType, o.OpSystemCode, OpSystemName, OpSystemVersion, o.MfgCode, MfgName
                from file f inner join Prod p on p.ProductCode=f.ProductCode inner join OS o on f.OpSystemCode=o.OpSystemCode inner join Mfg m on m.MfgCode=o.MfgCode
                where sha1=?;"""
        results = self.db.execute(sql, (submission.file.sha1.upper(),)).fetchall()

        if len(results) == 0:
            # Unknown in Db
            r.short = "Unknown File - sha1 : %s" % (submission.file.sha1)
        else:
            # Known in Hash Db
            r.short = "File known to be safe (%s match)" % (len(results))
            r.threat_level = 0
            for result in results:
                report_details = {
                    'FileName': result[2],
                    'FileSize': result[3],
                    'Product': {
                        'ProductName': result[4],
                        'ProductVersion': result[5],
                        'Language': result[6],
                        'ApplicationType': result[7],
                        'OS': {
                            'OpSystemCode': result[8],
                            'OpSystemName': result[9],
                            'OpSystemVersion': result[10],
                            'MfgCode': result[11],
                            'MfgName': result[12],
                        },
                    },
                }
                json = JSONEncoder().encode(report_details)
                section = ReportSection(
                    type='json',
                    value=json,
                    report=r
                )
                s.add(section)
        s.commit()
        #r._sa_instance_state.session.expunge(r)
        s.expunge(r)
        self.result_queue.put(r)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    s =Skeleton()