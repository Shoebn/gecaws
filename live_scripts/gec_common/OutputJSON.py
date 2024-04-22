import datetime
import shutil
import json
import gec_common.web_application_properties as application_properties


def today_formatted():
    return datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


class OutputJSON:
    filename = None
    file = None

    def __init__(self, script_name):
        self.filename = script_name + "_" + today_formatted() + ".json"
        self.file = open(application_properties.TMP_DIR + "/" + self.filename, encoding="utf8", mode="w")
        self.list = []

    def writeNoticeToJSONFile(self, dictionary):
        self.list.append(dictionary)

    def copyFinalJSONToServer(self, directory_name):
        json.dump(self.list,self.file,indent = 6,sort_keys = True)
        self.close()
        final_full_filename = application_properties.GENERATED_JSON_ROOT_DIR + "/" + directory_name + "/" + self.filename
        shutil.move(application_properties.TMP_DIR + "/" + self.filename, final_full_filename)
        
    def copycrosscheckoutputJSONToServer(self, directory_name):
        json.dump(self.list,self.file,indent = 6,sort_keys = True)
        self.close()
        final_full_filename = application_properties.GENERATED_JSON_ROOT_DIR + "/" + directory_name + "/" + self.filename
        shutil.move(application_properties.TMP_DIR + "/" + self.filename, final_full_filename)

    def close(self):
        self.file.write("\n")
        self.file.close()

    
