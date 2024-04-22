from gec_common.gecclass import *
import logging
from gec_common import log_config
import re
import jsons
import time
from datetime import date, datetime, timedelta


announceType = '2'
methodId = '2'
startdate = 1
enddate = 1
# deptId = '2' #sys.argv[5]
# project_ids = ['66109396154']

th = date.today() - timedelta(int(startdate))
startdate = th.strftime('%d/%m/%Y')
start_year = startdate.split('/')[-1] 
date_month = startdate.split(start_year)[0]
english_year = int(start_year) + 543
thai_startdate = date_month+str(english_year)
start_date = datetime.strptime(thai_startdate,'%d/%m/%Y').strftime('%d%m%Y')

th2 = date.today() - timedelta(int(enddate))
enddate = th2.strftime('%d/%m/%Y')
year = enddate.split('/')[-1] 
date_month = enddate.split(year)[0]
english_year = int(year) + 543
thai_enddate = date_month+str(english_year)
end_date = datetime.strptime(thai_enddate,'%d/%m/%Y').strftime('%d%m%Y')


if announceType == '5' or announceType == '13' or announceType == '14' or announceType == '16':
    SCRIPT_NAME = "th_gprogo_ca"
elif announceType == '15':
    SCRIPT_NAME = "th_gprogo_rei"
elif announceType == '2':
    SCRIPT_NAME = "th_gprogo_pp"
else:
    SCRIPT_NAME = "th_gprogo_spn"

log_config.log(SCRIPT_NAME)

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import os
from selenium.webdriver.support.ui import Select
from PIL import Image
import pytesseract
import gec_common.th_Doc_Download as Doc_Download
import sys
import base64
import pdfplumber
from gec_common.web_application_properties import *

    
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_folder = "cross_check_output"

def captcha():
    #Change frame to captcha
    iframe = page_main.find_element(By.ID, "iframePop")
    page_main.switch_to.frame(iframe)
    #Set wait time for alert to be created
    wait = WebDriverWait(page_main, 3)
    #Loop where we retry captcha check
    while True:
        # The name of the saved captcha image
        imageName = "captcha-image.png"
        try:
            #Locate captcha image
            time.sleep(1)
            img = page_main.find_element(By.ID, "captcha_image")
            time.sleep(1)

            #save it as variable
            screenshot = img.screenshot_as_png

            #store it locally
            with open(imageName, "wb") as f:
                f.write(screenshot)

            # Use pytesseract to extract text from the image
            extracted_text = pytesseract.image_to_string(Image.open(imageName))

            # Parse text to remove spaces
            parsedText = extracted_text.replace(" ", "")

            # Now 'parsedText' contains the text extracted from the image

            # Find text for completing the captcha
            captcha_input = page_main.find_element(By.ID, "CAPTCHA")
            captcha_input.clear()

            # Enter text into the input field
            page_main.execute_script("arguments[0].value = arguments[1];", captcha_input, parsedText)
            time.sleep(1)

            # Locate confirm button
            elementOk = page_main.find_element(By.NAME, "confirm")  
            elementOk.click()

            try:
                # Wait for alert to appear in case input is wrong
                alertExists = wait.until(EC.alert_is_present())
                alert = page_main.switch_to.alert
                # If the code reaches this point, an alert exists, so we press 'Ok'
                alert.accept()
                # Refresh the captcha image for next retry
                try:
                    elementRefresh = page_main.find_element(By.ID, "BtnRef")  
                    elementRefresh.click()
                except:
                    logging.info("Error")
            except:
                logging.info("No alert appeared")
                break
            # Clean up and remove the temporary screenshot file        
            os.remove(imageName)
        except:
            logging.info("Error")

    # Switch back to the main page
    page_main.switch_to.default_content()
    # Now 'extracted_text' contains the text extracted from the image
    logging.info("Extracted Text:", extracted_text)
    
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = cross_check_output()
    notice_data.method_name = methodId
    
    # Onsite Field -None
    # Onsite Comment -click on "ประกาศวันนี้ = announced today" to get the data
    notice_data.script_name = SCRIPT_NAME

    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        if '-' in publish_date:
            publish_date = publish_date.split('-')[0].strip()
        year = publish_date.split('/')[-1] 
        date = publish_date.split(year)[0]
        english_year = int(year) - 543
        publish_date_english = str(date) + str(english_year)
        publish_date_final = re.findall('\d+/\d+/\d{4}',publish_date_english)[0]
        notice_data.publish_date = datetime.strptime(publish_date_final,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if selectannounceType == 'ประกาศรายชื่อผู้ผ่านการตรวจสอบผู้ไม่มีผลประโยชน์ร่วมกัน':
        notice_data.notice_type = 0
    elif selectannounceType == 'ประกาศรายชื่อผู้ชนะการเสนอราคา' or selectannounceType == 'ประกาศรายชื่อผู้ไม่มีผลฯ เปลี่ยนแปลงประกาศรายชื่อผู้ไม่มีผลฯ และยกเลิกประกาศรายชื่อผู้ไม่มีผลฯ':
        notice_data.notice_type = 7
    elif selectannounceType == 'ประกาศรายชื่อผู้ชนะฯ เปลี่ยนแปลงประกาศรายชื่อผู้ชนะฯ และยกเลิกประกาศรายชื่อผู้ชนะฯ' or selectannounceType == 'ประกาศผลผู้ชนะการจัดซื้อจัดจ้างหรือผู้ได้รับการคัดเลือกรายไตรมาส':
        notice_data.notice_type = 7
    elif selectannounceType == 'เปลี่ยนแปลงประกาศเชิญชวน' or selectannounceType == 'เปลี่ยนแปลงประกาศรายชื่อผู้ผ่านการตรวจสอบผู้ไม่มีผลประโยชน์ร่วมกัน':
        notice_data.notice_type = 16
    elif selectannounceType == 'เปลี่ยนแปลงประกาศรายชื่อผู้ชนะการเสนอราคา' or selectannounceType == 'ประกาศเชิญชวน เปลี่ยนแปลงประกาศเชิญชวน และยกเลิกประกาศเชิญชวน':
        notice_data.notice_type = 16
    elif selectannounceType == 'ยกเลิกประกาศเชิญชวน' or selectannounceType == 'ยกเลิกประกาศรายชื่อผู้ผ่านการตรวจสอบผู้ไม่มีผลประโยชน์ร่วมกัน' or selectannounceType == 'ยกเลิกประกาศรายชื่อผู้ชนะการเสนอราคา':
        notice_data.notice_type = 16
        notice_data.tender_is_canceled = True
    elif selectannounceType == 'สรุปข้อมูลการเสนอราคาเบื้องต้น':
        notice_data.notice_type = 5
    elif selectannounceType == 'ประกาศร่าง TOR/ร่างเอกสารประกวดราคา':
        notice_data.notice_type = 3
    else:
        notice_data.notice_type = 4
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > span').text.split('(เลขที่โครงการ :')[1].split(')')[0].strip()
    except:
        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split('(เลขที่โครงการ :')[1].split(')')[0].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
            
    logging.info(str(notice_data.notice_no))

    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1

    if page_no > 1 and next_page_bool == True:
        back_to_page = WebDriverWait(page_main, 30).until(EC.element_to_be_clickable((By.XPATH,f'(//td[@id="tdpage2"])/b/font/u[contains(text(),"{page_no-1}")]|(//td[@id="tdpage2"])/following-sibling::td[contains(text(),"{page_no-1}")]'))).click()
        time.sleep(5)
    logging.info('----------------------------------')



# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main =  Doc_Download.page_details
page_main.timeouts.page_load = 100
page_main.maximize_window()
next_page_bool = False
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['http://www.gprocurement.go.th/new_index.html'] 
    for url in urls:
        fn.load_page(page_main, url, 150)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            WebDriverWait(page_main, 5).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="home-popup-close-button"]'))).click()
            time.sleep(3)
        except:
            pass
        clk2=WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="layoutContainers"]/div[2]/div[7]/div/div/div[2]/div/div/section/div[2]/div[2]/div[2]/div/div/div/form/div[4]/div[2]/a'))).click()
        time.sleep(3)

        select_announceType = Select(page_main.find_element(By.XPATH,'//*[@id="announceType"]'))
        time.sleep(3)
        select_announceType.select_by_index(announceType)
        time.sleep(2)
        selected_option = select_announceType.first_selected_option
        selectannounceType = selected_option.text

#         select_deptId = Select(page_main.find_element(By.XPATH,'//*[@id="deptId"]'))
#         time.sleep(3)
#         select_deptId.select_by_index(deptId)
#         time.sleep(2)

        select_methodId = Select(page_main.find_element(By.XPATH,'//*[@id="methodId"]'))
        time.sleep(3)
        select_methodId.select_by_index(int(methodId))
        time.sleep(2)
        page_main.find_element(By.XPATH,'//*[@id="announceSDate"]').clear()
        page_main.find_element(By.XPATH,'//*[@id="announceSDate"]').send_keys(str(start_date))
        time.sleep(3)
        
        page_main.find_element(By.XPATH,'//*[@id="announceEDate"]').clear()
        page_main.find_element(By.XPATH,'//*[@id="announceEDate"]').send_keys(str(end_date))
        time.sleep(3)
        
#         page_main.find_element(By.XPATH,'//*[@id="project_id"]').clear()
#         page_main.find_element(By.XPATH,'//*[@id="project_id"]').send_keys(str(project_id))
#         time.sleep(3)
        


        search_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="idBtn"]/table/tbody/tr/td[2]/input[1]')))
        page_main.execute_script("arguments[0].click();",search_click)
        time.sleep(3)
        captcha()
        for page_no in range(2,200):
            try:
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH, "//tr[@style='']"))).text
                logging.info("page_check try")
            except:
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH, "/html/body/form/table[1]/tbody/tr/td/table[3]/tbody/tr[2]")))
                if 'ค้นหาข้อมูลในฐานข้อมูลไม่พบ' in page_check.text:
                    logging.info('page_check no records break Cant find information in the database.')
                    break
            rows = WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.XPATH,"//tr[@style='']")))
            length = len(rows)
            logging.info(length)
            
            for each_record in range(0,length):
                tender_html_element = WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.XPATH, "//tr[@style='']")))[each_record]
                if 'ค้นหาข้อมูลในฐานข้อมูลไม่พบ' in tender_html_element.text:
                    break
                extract_and_save_notice(tender_html_element)

            logging.info(page_no)
            
            try:
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,f'(//td[@id="tdpage2"])/b/font/u[contains(text(),"{page_no}")]|(//td[@id="tdpage2"])/following-sibling::td[contains(text(),"{page_no}")]'))).click()
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH, "//tr[@style='']"),page_check))
                next_page_bool = True
            except:
                try:                            
                    next_page_lots = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="tableb3"]/tbody/tr/td[8]'))).click()
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH, "//tr[@style='']"),page_check))
                    next_page_bool = True
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        logging.info("Done cross checked total notice which has to be downloaded {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)
