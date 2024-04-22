import time
import os
import logging
from gec_common import log_config
from gec_common import web_application_properties
import pandas as pd
logging.basicConfig(level=logging.INFO, format="%(asctime)s, %(levelname)s: %(message)s")
import psycopg2

WORK_DIR = "C:/Users/Administrator/Documents/bat"
LOG_DIR = "C:/Users/Administrator/Documents/logs"
LOCK_FILE = "C:/Users/Administrator/Documents/dgscraping.lock"

def check_pid(pid):
    """ Check For the existence of a unix pid. """
    try:
        os.kill(int(pid), 0)
    except OSError:
        return False
    except TypeError:
        return False
    except ValueError:
        return False
    else:
        return True

def createLockFile():
    logging.info("Locking: Creating lock file..")
    lockFile = open(LOCK_FILE, "w")
    lockFile.write(str(os.getpid()))
    lockFile.close()

def lockProcess():
    if not os.path.isfile(LOCK_FILE):
        logging.info("Locking: Lock file doesn't exist")
        createLockFile()
        return True

    lockFile = open(LOCK_FILE, "r")
    pid = lockFile.read()
    lockFile.close()
    if check_pid(pid):
        return False
    else:
        logging.info("Locking: Lock file exists but is stale")
        createLockFile()
        return True

class SourceInfo:
    internalCode = ''
    runTime = ''
    lastRunTime = None

    def __init__(self, sourceInfoFromDB):
        self.internalCode = sourceInfoFromDB[0]
        self.runTime = sourceInfoFromDB[1]
        self.lastRunTime = None

def timeToRun(source):
    if (source.lastRunTime != None and time.mktime(time.localtime()) - time.mktime(source.lastRunTime) < 300):
        return False
    timeNow = time.strftime("%H:%M", time.localtime())
    timeFromSource = source.runTime
    return timeFromSource == timeNow

#if not lockProcess():
    #quit()

def runSource(source):
    logging.info("Running {} ...".format(source.internalCode))
    source.lastRunTime = time.localtime()
    scriptName = source.internalCode
    runStr = "cd /d {} && start {}.bat".format(WORK_DIR, scriptName)
    os.system(runStr)
    
DATABASE_HOST = "prod-gec-db.chsqqj3urp6j.ap-south-1.rds.amazonaws.com"
DATABASE_NAME = "gecuserdb"
DATABASE_USERNAME = "gecpgadmin"
DATABASE_PASSWORD = "g3cStrongPass22"
DATABASE_PORT = "5432"

database = psycopg2.connect(user=DATABASE_USERNAME,
                      password=DATABASE_PASSWORD,
                      database=DATABASE_NAME,
                      host=DATABASE_HOST)
dbCursor = database.cursor()
sql = "select internal_code, TO_CHAR(scheduled_time, 'HH24:MI') as scheduled_time from app_sources where status in (1,13,15,16,17) and instance_name = 1 and scheduled_time is not null"

def initSources():
    logging.info("Reloading sources...")
    database.commit()
    dbCursor.execute(sql)
    allSourcesFromDB = dbCursor.fetchall()
    allSources = []
    for sourceFromDB in allSourcesFromDB:
        allSources.append(SourceInfo(sourceFromDB))
    return allSources

lastSourceInitTime = time.localtime()
allSources = initSources()
while 1 == 1:
    if (time.mktime(time.localtime()) - time.mktime(lastSourceInitTime) > 10 * 60):
        allSources = initSources()
        lastSourceInitTime = time.localtime()
    for source in allSources:
        if timeToRun(source):
            runSource(source)
    time.sleep(10)
