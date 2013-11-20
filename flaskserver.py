from flask import Flask, render_template, request, g
from werkzeug import secure_filename
from config import ConfigBorg
from Tools.tools import hashdigest
import os
import logging
from Queue import Queue
from dispatcher import Dispatcher
from Model import Db, Report, File

config = ConfigBorg()


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = config.flask['upload_dir']
db = Db()

@app.route('/report/<sha256>')
def report(sha256):
    file = db.session.query(File).filter_by(sha256=sha256).one()
    submissions = file.submissions
    reports = [(s, s.reports) for s in submissions]
    return "%s"%files
    return sha256

@app.route('/shutdown')
def shutdown():
    if not dispatcher.isAlive():
        logging.warning("Cannot stop dispatcher : Dispatcher is not running...")
        return "Cannot stop dispatcher : Dispatcher is not running..."
    else:
        job_queue.put(None)
        dispatcher.join()
        return "Dispatcher stopped..."

@app.route('/start')
def start():
    global dispatcher
    if dispatcher.isAlive():
        logging.warning("Cannot start dispatcher : Dispatcher is already running")
        return "Cannot start dispatcher : Dispatcher is already running"
    else:
        dispatcher = Dispatcher(job_queue=job_queue)
        dispatcher.start()
        return "Dispatcher started... %s" % dispatcher

@app.route('/', methods=['GET', 'POST'])
def hello_world():
    if request.method == 'POST':
        file = request.files['file']
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        sha256 = hashdigest(save_path)['sha256']
        normalized_name_path = os.path.join(app.config['UPLOAD_FOLDER'], sha256)
        try:
            os.rename(save_path, normalized_name_path)
        except OSError:
            #  File already here on windows raise exception
            os.remove(save_path)
        job = {'path': normalized_name_path, 'name': filename}
        job_queue.put(job)
        return "%s (%s) saved to %s - job : %s" % (filename, sha256, normalized_name_path, job)
    else:
        return render_template('submit.html')


def start_flask():
    global  job_queue
    global  dispatcher
    # Create IN job queue & job dispatcher
    job_queue = Queue()
    #d = Dispatcher(job_queue=job_queue, log_queue=loggingqueue.queue) Process based logging
    dispatcher = Dispatcher(job_queue=job_queue)
    dispatcher.start()
    app.run(debug=True, use_reloader=False)


if __name__ == '__main__':
    start_flask()