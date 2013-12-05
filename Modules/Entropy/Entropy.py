from Tools.entropy_pil import Entropy as EntropyTool
from Tools.entropy_pil import MapFile
from Model import Report, Session, ReportSection
import os
from json import JSONEncoder
from Modules.Skeleton.Skeleton import Skeleton, skeletonWorker

class Entropy(Skeleton):
    def __init__(self, **kwargs):
        self.worker_class = Worker
        Skeleton.__init__(self)


class Worker(skeletonWorker):

    def _do_work(self, submission):
        #Do the actual work
        e = EntropyTool(submission.file.path)
        (entropy, mean, stdv, max_dev) = e.analyze()
        out = os.path.join(self.module_config['output_dir'], "%s.png" % submission.file.sha256)
        e.writeimg(out)
        mapout = os.path.join(self.module_config['output_dir'], "%s_map.png" % submission.file.sha256)
        MapFile().writeimg(submission.file.path, mapout)
        r1 = {'path': out.replace("\\", "/"), 'comment': 'Entropy of the file'}
        r2 = {'path': mapout.replace("\\", "/"), 'comment': 'Mapping of the file'}
        json1 = JSONEncoder().encode(r1)
        json2 = JSONEncoder().encode(r2)
        r = Report(
            module=self.__ModuleName__,
            short="%s" % e.FileTypeText(),
            full="",
            submission=submission
        )
        Session.add(r)
        section1 = ReportSection(
            type='img',
            value=json1,
            report=r
        )
        Session.add(section1)
        section2 = ReportSection(
            type='img',
            value=json2,
            report=r
        )
        Session.add(section2)
        Session.commit()
        return r

