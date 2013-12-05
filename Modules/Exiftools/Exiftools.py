from Tools.tools import exiftool
from Model import Report, ReportSection, Session
from json import JSONEncoder
from Modules.Skeleton.Skeleton import Skeleton, skeletonWorker


class Exiftools(Skeleton):
    def __init__(self, **kwargs):
        self.worker_class = Worker
        Skeleton.__init__(self)


class Worker(skeletonWorker):
    def _preRun(self):
        self.exif_tool = exiftool()

    def _do_work(self, submission):
        #Do the actual work
        metadata = self.exif_tool.get_metadata(submission.file.path)
        metadata_hierarchy = {}
        for key, value in metadata.iteritems():
            parent = metadata_hierarchy
            subkeys = key.split(':')
            for i in range(len(subkeys) - 1):
                current = subkeys[i]
                if current not in parent:
                    parent[current] = {}
                parent = parent[current]
            current = subkeys[-1]
            parent[current] = value
        json = JSONEncoder().encode(metadata_hierarchy)
        s = Session()
        r = Report(
            module=self.__ModuleName__,
            short="",
            full="",
            submission=submission
        )
        s.add(r)
        section = ReportSection(
            type='json',
            value=json,
            report=r
        )
        s.add(section)
        s.commit()
        #r._sa_instance_state.session.expunge(r)
        return r

