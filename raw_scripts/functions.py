import csv
import logging
import os
import re
import shutil
import time
import xml.etree.cElementTree as ET
from datetime import date, datetime, timedelta
from xml.etree import ElementTree
import htmlmin
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
import ml.cpv_classifier as classifier
from gec_common.web_application_properties import *
from false_cpv import false_cpv
import requests
import speech_recognition as sr
from os import path
from pydub import AudioSegment
import uuid
import glob
from webdriver_manager.chrome import ChromeDriverManager
import db_connection as db_conn
db = db_conn.get_conn()

EPROCUREMENT_SCRAPE_FROM_DAYS_AGO = 3

logging.basicConfig(level=logging.INFO, format="%(asctime)s, %(levelname)s: %(message)s")


def today_formatted():
    return date.today().strftime('%Y-%m-%d')


def today_formatted_for_saving_output_xmls():
    return datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


doc_folder = today_formatted()

def is_scraped(internal_code, reference):
    return False


def add_unique(internal_code, reference, pd):
    pass


def get_string_between(extract, start, end):
    extract = ' ' + extract
    try:
        ini = extract.index(start)
    except:
        return ''
    if (ini == 0):
        return ''
    ini += len(start)
    newSrting = extract[ini:]
    end_position = newSrting.index(end)
    output = newSrting[:end_position]
    return output


def extract_most_recent_file_from_directory(directory: str):
    full_path = max([directory + "/" + f for f in os.listdir(directory)], key=os.path.getctime)
    return full_path.split("/")[-1]


def indent(elem, level=0):
    i = "\n" + level * "  "
    j = "\n" + (level - 1) * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem


def get_after(extract, start, length):
    try:
        ini = extract.index(start)
    except:
        return ''

    if (ini == 0):
        return ''
    ini += len(start)
    end = ini + length
    output = extract[ini:end]
    return output


def xmlUpload(folder, internal_code, NOTICES, notice_count):
    today = today_formatted_for_saving_output_xmls()
    tree = ET.ElementTree(NOTICES)
    temp_filename = internal_code + "_" + today + ".xml"
    tree.write(temp_filename, method="xml", xml_declaration=True, encoding="utf-8")  # creating xml

    root = ElementTree.parse(temp_filename).getroot()
    tree = ET.ElementTree(root)
    indent(root)
    tree.write(temp_filename, method="xml", xml_declaration=True, encoding="UTF-8")

    final_full_filename = GENERATED_XML_ROOT_DIR + "/" + folder + "/" + internal_code + "_" + today + ".xml"
    shutil.move(temp_filename, final_full_filename)


def unique(list1):
    # intilize a null list
    unique_list = []
    # traverse for all elements
    for x in list1:
        # check if exists in unique_list or not
        if x not in unique_list:
            unique_list.append(x)
    # print list
    return unique_list


def log_entry(internal_code, notice_count, status):
    td = date.today()
    today = td.strftime('%Y-%m-%d')

    datestring = str(datetime.now())
    fields = [internal_code, datestring, notice_count, status]
    log_file = 'logs/log_' + today + '.csv'

    with open(log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(fields)


def log_auto_cpv(internal_code, notice_count, mapped, ml):
    td = date.today()
    today = td.strftime('%Y-%m-%d')

    # datestring = str(datetime.now())
    fields = [internal_code, notice_count, mapped, ml]
    log_file = 'logs/log_auto_cpv_' + today + '.csv'

    with open(log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(fields)


def error_log(internal_code,e=None,notice_count = None,status=None):
    pass

def session_log(internal_code, notice_count, status, e=None):
    pass

def session_log_india(internal_code, notice_count, mapped, ml, status):
    session_log(internal_code, notice_count, mapped)


def get_email(text):
    emails = re.findall(r'[\w\.-]+@[\w\.-]+', text)
    if (len(emails) > 0):
        return emails[0]
    else:
        return ''


def last_success(internal_code):
    return 1


def minifyHTML(html):
    return htmlmin.minify(html, remove_empty_space=True)


def cleanup_image_for_capcha(image_as_string: str):
    return image_as_string.replace('data:image/png;base64,', '').replace('%0A', '').strip()


def wait_for_presence(driver: WebDriver, locator, timeout_seconds=5):
    MAX_LOAD_PAGE_ATTEMPTS = 2
    for loop_counter in range(1, MAX_LOAD_PAGE_ATTEMPTS):
        try:
            if locator is not None:
                element_present = expected_conditions.presence_of_element_located(locator)
                WebDriverWait(driver, timeout_seconds).until(element_present)
            else:
                time.sleep(5)
            return
        except TimeoutException as e:
            if loop_counter == MAX_LOAD_PAGE_ATTEMPTS:
                raise e
            else:
                pass


def load_page_by_locator(driver: WebDriver, url: str, locator=None, timeout_seconds=5):
    MAX_LOAD_PAGE_ATTEMPTS = 2
    for loop_counter in range(1, MAX_LOAD_PAGE_ATTEMPTS):
        try:
            driver.get(url)
            if locator is not None:
                element_present = expected_conditions.presence_of_element_located(locator)
                WebDriverWait(driver, timeout_seconds).until(element_present)
            else:
                time.sleep(5)
            return
        except TimeoutException as e:
            if loop_counter == MAX_LOAD_PAGE_ATTEMPTS:
                raise e
            else:
                pass


def load_page(driver: WebDriver, url: str, timeout_seconds=5):
    return load_page_by_locator(driver, url, None, timeout_seconds)


def load_page_expect_id(driver: WebDriver, url: str, wait_fo_element_with_id: str, timeout_seconds=5):
    assert wait_fo_element_with_id is not None
    return load_page_by_locator(driver, url, (By.ID, wait_fo_element_with_id), timeout_seconds)


def load_page_expect_xpath(driver: WebDriver, url, wait_of_element_with_xpath: str, timeout_seconds=5):
    assert wait_of_element_with_xpath is not None
    return load_page_by_locator(driver, url, (By.XPATH, wait_of_element_with_xpath), timeout_seconds)


def init_chrome_driver(arguments=[], experimental_options={}):
    MAX_LOAD_DRIVER_ATTEMPTS = 10

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    for argument in arguments:
        chrome_options.add_argument(argument)
    for key, value in experimental_options.items():
        chrome_options.add_experimental_option(key, value)

    for loop_counter in range(1, MAX_LOAD_DRIVER_ATTEMPTS + 1):
        try:
            driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), chrome_options=chrome_options)
            if driver is not None:
                return driver
        except WebDriverException as e:
            if loop_counter == MAX_LOAD_DRIVER_ATTEMPTS:
                raise e
            else:
                pass


def assign_cpvs_from_title(title: str, category = None):
    clean_cpvs = []

    if title == '' or title is None:
        return clean_cpvs

    cpvs_with_false_cpv = classifier.get_cpvs(title.lower(), category)
    for cpv in cpvs_with_false_cpv:
        if cpv not in false_cpv:
            clean_cpvs.append(cpv)

    return clean_cpvs


def captcha(audio_url):
    doc = requests.get(audio_url)
    file_name = str(uuid.uuid4())
    with open(TMP_DIR + '/' + file_name + '.mp3', 'wb') as f:
        f.write(doc.content)
    time.sleep(10)
    sound = AudioSegment.from_mp3(TMP_DIR + '/' + file_name + '.mp3')
    sound.export(TMP_DIR + '/' + file_name + '.wav', format="wav")
    time.sleep(10)
    r = sr.Recognizer()
    with sr.AudioFile(TMP_DIR + '/' + file_name + '.wav') as source:
        audio_text = r.listen(source)
        try:
            text = r.recognize_google(audio_text)
        except:
            pass
    mp3file = TMP_DIR + '/' + file_name + '.mp3'
    wavfile = TMP_DIR + '/' + file_name + '.wav'
    os.remove(mp3file)
    os.remove(wavfile)
    return text

def previous_scraping_log_check(script_name):
    log_file_name_wildcard = "{}/{}-*.log".format(LOG_PATH, script_name)
    log_file_names = glob.glob(log_file_name_wildcard)
    sorted_files = sorted(log_file_names, key=os.path.getmtime)
    second_latest_file = sorted_files[-1]
    file = open(second_latest_file, mode="r", encoding="latin-1")
    fread = file.read()
    file.close()
    if 'Finished processing' in fread or 'No new record' in fread:
        return False
    else:
        return True
    
def write_website_first_page_data(file_path,driver,locator,path):
    Func = open(file_path,"w", encoding="utf8")
    new_text = WebDriverWait(driver, 50).until(expected_conditions.presence_of_element_located((locator,path))).text 
    Func.write(new_text)
    Func.close()
    
def compare_website_first_page_data_from_previous_scraping(driver,locator,path,file_name,script_name):
    file_path = WEBSITE_FIRST_PAGE_DATA+"/"+file_name+'.txt'
    if os.path.exists(file_path):
        new_text = WebDriverWait(driver, 50).until(expected_conditions.presence_of_element_located((locator,path))).text
        with open(file_path, 'r', encoding="utf8") as f:
            previous_scraped_text = f.read()
            f.close()
            if new_text == previous_scraped_text:
                try:
                    previous_scraping_logcheck = previous_scraping_log_check(script_name)
                    if previous_scraping_logcheck == False:
                        return False
                    else:
                        os.remove(file_path)
                        write_website_first_page_data(file_path,driver,locator,path)
                        return True
                except:
                    return True
            else:
                os.remove(file_path)
                write_website_first_page_data(file_path,driver,locator,path)
                return True
    else:
        write_website_first_page_data(file_path,driver,locator,path)
        return True

def CPV_mapping(filename,category = None):
    cpvs= []
    if category is not None:
        category = category.lower()
        if ',' in category or '.' in category:
            category = category.replace(',','')
            category = category.replace('.','')
        
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            maps = list(reader)
            CPV_mapping = dict(maps)
        try:
            cpv = CPV_mapping.get(category)
            cpvss = cpv.split('#')
            for cpv in cpvss:
                if cpv == '':
                    pass
                else:
                    cpvs.append(cpv.strip())
        except:
            pass
    return cpvs

def duplicate_check_data_from_previous_scraping(script_name,NOTICE_DUPLICATE_COUNT,data,previous_scraping_log_check):
    th = date.today() - timedelta(1)
    back_date = th.strftime('%Y-%m-%d')
    today = date.today()
    current_date = today.strftime('%Y-%m-%d')
    
    back_date_file_path = WEBSITE_FIRST_PAGE_DATA+"/"+script_name +'-'+ back_date +'.txt'
    file_path = WEBSITE_FIRST_PAGE_DATA+"/"+script_name +'-'+ current_date +'.txt'
    
    if not os.path.exists(file_path):
        Func = open(file_path,"w", encoding="utf8")
        Func.close()    
    else:
        pass

    with open(file_path, 'a', encoding="utf8") as f:
        f.write(data +'\n' )
        f.close()          
        
    if os.path.exists(back_date_file_path) and previous_scraping_log_check == False:
        with open(file_path, 'r', encoding="utf8") as f:
            html_text = f.read()
            data_lines = html_text.splitlines()
            if data in data_lines:
                f.close()
                NOTICE_DUPLICATE_COUNT_ATTEMPTS = NOTICE_DUPLICATE_COUNT + 1
                return False, NOTICE_DUPLICATE_COUNT_ATTEMPTS
            else:
                f.close()
                return True, 0
    else:
        return True, 0
    
def bytes_converter(filesize):
    try:
        if 'kb' in filesize.lower() or 'kilobytes' in filesize.lower():
            filesize = filesize.lower().replace('kb','').replace('kilobytes','').replace(',','.').strip()
            filesize_bytes = float(filesize) * 1024
        elif 'mb' in filesize.lower() or 'megabytes' in filesize.lower():
            filesize = filesize.lower().replace('mb','').replace('megabytes','').replace(',','.').strip()
            filesize_bytes = float(filesize) * 1024 * 1024
        elif 'gb' in filesize.lower() or 'gigabytes' in filesize.lower():
            filesize = filesize.lower().replace('gb','').replace('gigabytes','').replace(',','.').strip()
            filesize_bytes = float(filesize) * 1024 * 1024 * 1024
        else:
            filesize_bytes = 0.00
    except:
        filesize_bytes = 0.00
    return filesize_bytes

def procedure_mapping(filename,type_of_procedure_actual = None):
    type_of_procedure = 'Other'
    if type_of_procedure_actual is not None:
        type_of_procedure_actual = type_of_procedure_actual.replace(',','').replace('.','')
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            maps = list(reader)
            procedure_mapping = dict(maps)
        type_of_procedure = procedure_mapping.get(type_of_procedure_actual)
    return type_of_procedure

def url_match(url):
    regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
            r'localhost|' #localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def valid_email(email):
    email_valid = bool(re.search(r'[\w\.-]+@[\w\.-]+', email))
    return email_valid

def cpv_dict():
    sql = 'select cpv from app_cpvs'
    cpv_q = db.cursor()
    cpv_q.execute(sql)
    data = cpv_q.fetchall()
    cpv_dict = list((y[0]) for y in data)
    return cpv_dict
