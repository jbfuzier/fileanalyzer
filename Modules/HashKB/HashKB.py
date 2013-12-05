from Model import Report, ReportSection, Session
from json import JSONEncoder
import sqlite3
from Modules.Skeleton.Skeleton import Skeleton, skeletonWorker

# TODO Add custom hash db


class HashKB(Skeleton):
    def __init__(self, **kwargs):
        self.worker_class = Worker
        Skeleton.__init__(self)


class Worker(skeletonWorker):

    def _preRun(self):
        self.db = sqlite3.connect(self.module_config['dbpath'])


    def _do_work(self, submission):
        s = Session()
        r = Report(
            module=self.__ModuleName__,
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
        return r
