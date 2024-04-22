import datetime
import shutil
import xml.etree.ElementTree as ET
import gec_common.web_application_properties as application_properties


def today_formatted():
    return datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


class OutputXML:
    filename = None
    file = None

    def __init__(self, script_name):
        self.filename = script_name + "_" + today_formatted() + ".xml"
        self.file = open(application_properties.TMP_DIR + "/" + self.filename, encoding="utf8", mode="w")
        self.file.write("<NOTICES>\n")

    def writeNoticeToXMLFile(self, result):
        self.file.write(result)
        self.file.write("\n")

    def copyFinalXMLToServer(self, directory_name):
        self.close()
        final_full_filename = application_properties.GENERATED_XML_ROOT_DIR + "/" + directory_name + "/" + self.filename
        shutil.move(application_properties.TMP_DIR + "/" + self.filename, final_full_filename)

    def close(self):
        self.file.write("</NOTICES>\n")
        self.file.close()
