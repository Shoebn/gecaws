import os
import shutil
import time
import uuid
from datetime import datetime
import platform
import gec_common.web_application_properties as application_properties
from gec_common import functions as fn
from deep_translator import GoogleTranslator

def today_formatted():
    return datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


class Doc_Download:
    folder_name = None
    tmp_dwn_dir = None
    attachment_dir = None

    def __init__(self, script_name):
        self.folder_name = '/' + script_name + "_" + today_formatted()
        system_name = platform.uname().system
        if 'Windows' in system_name:
            ######################### For Windows Server ##############################
            tmp_dwn = application_properties.TMP_DIR + self.folder_name
            self.tmp_dwn_dir = tmp_dwn.replace('/',"\\")        
            attachment_dir = application_properties.NOTICE_ATTACHEMENTS_DIR + self.folder_name
            self.attachment_dir = attachment_dir.replace('/',"\\") 
        else:
            ######################### For Linux Server ##############################
            self.tmp_dwn_dir = application_properties.TMP_DIR + self.folder_name
            self.attachment_dir = application_properties.NOTICE_ATTACHEMENTS_DIR + self.folder_name
        ######################################################################
        os.makedirs(self.tmp_dwn_dir)
        os.makedirs(self.attachment_dir)
        self.experimental_options = {"prefs": {"download.prompt_for_download": False,"plugins.always_open_pdf_externally": True,"download.open_pdf_in_system_reader": False,"profile.default_content_settings.popups": 0,"download.default_directory": self.tmp_dwn_dir}}
        self.page_details = fn.init_chrome_driver(arguments=[], experimental_options=self.experimental_options)

    def latest_download_file(self):
        path = self.tmp_dwn_dir
        os.chdir(path)
        files = sorted(os.listdir(os.getcwd()), key=os.path.getmtime)
        newest = files[-1]
        return newest

    def file_download(self):
        while True:
            time.sleep(5)
            newest_file = self.latest_download_file()
            if not ("crdownload" in newest_file or ".tmp" in newest_file):
                break
        file_name = str(uuid.uuid4())
        newest_file = GoogleTranslator(source='ar', target='en').translate(newest_file)
        new_file_name = newest_file.split(".")[-2] +'.'+ newest_file.split(".")[-1]
        new_file_name = file_name+'.'+new_file_name.replace('#','')
        newest_file_path = self.tmp_dwn_dir + '/' + newest_file
        new_file_path = self.tmp_dwn_dir + '/' + new_file_name
        os.rename(newest_file_path, new_file_path)
        resource_url = application_properties.NOTICE_ATTACHMENTS_BASE_URL + self.folder_name + '/' + new_file_name
        shutil.move(new_file_path, self.attachment_dir)
        return resource_url, new_file_name
