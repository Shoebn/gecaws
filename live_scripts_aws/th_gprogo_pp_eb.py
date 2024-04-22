from gec_common.gecclass import *
import logging
from gec_common import log_config
import re
import jsons
import time
import sys
from datetime import date, datetime, timedelta

announceType = '2'
methodId = '2'
startdate = 1
enddate = 1
 # deptId = sys.argv[5]
 # project_id = '66109396154'

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
#previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

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
    
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
    
    download_already = False
    # Onsite Field -None
    # Onsite Comment -click on "ประกาศวันนี้ = announced today" to get the data
    notice_data.script_name = SCRIPT_NAME
    notice_data.main_language = 'TH'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TH'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'THB'
    notice_data.procurement_method = 2
    notice_data.document_type_description = selectannounceType

    notice_data.notice_url = url
    infoProcureDocAnnounZipAdj = False
    s_external = False
    tab_zip = False
    median_price = False
    winner = False
    
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

    #if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        #return
    
    # Onsite Field -เรื่อง   = subject
    # Onsite Comment -None
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
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > span').text.split('(e-bidding)')[0].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except:
        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split('(เลขที่โครงการ :')[0].strip()
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except:
            try:
                notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
            except Exception as e:
                logging.info("Exception in local_title: {}".format(type(e).__name__))
                pass
    
    # Onsite Field -วันที่  ประกาศ   = date announced
    # Onsite Comment -None
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > span').text.split('(เลขที่โครงการ :')[1].split(')')[0].strip()
    except:
        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split('(เลขที่โครงการ :')[1].split(')')[0].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    logging.info(notice_data.notice_no)
            
    
    # Onsite Field -งบประมาณโครงการ(บาท)  =  Project Budget (Baht)
    # Onsite Comment -None

    try:
        netbudgetlc = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_data.netbudgetlc = float(netbudgetlc.replace(',',''))
        notice_data.est_amount = notice_data.netbudgetlc
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass  
        
    try:              
        customer_details_data = customer_details()
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
        customer_details_data.org_country = 'TH'
        customer_details_data.org_language = 'TH'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_url_click = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7) > a').click()
        time.sleep(3)
    except:
        pass

    try:
        WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > form > table:nth-child(17) > tbody > tr > td > table:nth-child(2) > tbody > tr:nth-child(2) > td > table > tbody > tr'))).text
    except:
        pass

    try:
        notice_data.notice_text += page_main.find_element(By.XPATH, '/html/body/form/table[1]').get_attribute("outerHTML")
    except Exception as e:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")  
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:     
        rows = WebDriverWait(page_main, 30).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > form > table:nth-child(17) > tbody > tr > td > table:nth-child(2) > tbody > tr:nth-child(2) > td > table > tbody > tr')))
        doclength = len(rows)
        logging.info("doclength")
        logging.info(doclength)
        for eachrecord in range(1,doclength):
            download_already = False
            single_record = page_main.find_elements(By.CSS_SELECTOR, 'body > form > table:nth-child(17) > tbody > tr > td > table:nth-child(2) > tbody > tr:nth-child(2) > td > table > tbody > tr')[eachrecord]
            try:
                if '(e-Bidding)' in single_record.text:
                    try:
                        try:
                            click = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > span').click()
                            time.sleep(3)
                        except:
                            click = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').click()
                            time.sleep(3)

                        try:
                            notice_data.notice_text += page_main.find_element(By.XPATH,'//*[@id="divPop2"]/div/form').get_attribute("outerHTML")
                        except:
                            pass

                        for single_record2 in page_main.find_elements(By.CSS_SELECTOR, '#showsDiv > table > tbody > tr'):
                            try:
                                attachments_data = attachments()
                    # Onsite Field -ประเภทประกาศ  = announcement type
                    # Onsite Comment -take file_name in textform

                                attachments_data.file_name = single_record2.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
                    # Onsite Field -ประเภทประกาศ  = announcement type
                    # Onsite Comment -None
                                url_infoProcureDocAnnounZipAdj = "https://process5.gprocurement.go.th/egp-approval-service/apv-common/infoProcureDocAnnounZipAdj?projectId="+notice_data.notice_no
                                s_external_url = "https://process5.gprocurement.go.th/egp-approval-service/apv-common/infoProcureDocAnnounZip?projectId="+ notice_data.notice_no

                                if attachments_data.file_name != 'ประกาศเชิญชวน': 
                                    if (Doc_Download.response_contains_data(url_infoProcureDocAnnounZipAdj) == True) and infoProcureDocAnnounZipAdj == False:
                                        attachments_data = attachments()
                                        file_dwn = Doc_Download.switch_tabZipAdj(url_infoProcureDocAnnounZipAdj)
                                        attachments_data.external_url = str(file_dwn)
                                        attachments_data.file_name = single_record2.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
                                        infoProcureDocAnnounZipAdj = True
                                        download_already = True
                                        attachments_data.attachments_cleanup()
                                        notice_data.attachments.append(attachments_data)

                                    if (Doc_Download.response_contains_data(s_external_url) == True) and tab_zip == False:
                                        attachments_data = attachments()
                                        file_dwn = Doc_Download.switch_tabZip(s_external_url)
                                        attachments_data.external_url = str(file_dwn)
                                        attachments_data.file_name = single_record2.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
                                        tab_zip = True
                                        download_already = True
                                        attachments_data.attachments_cleanup()
                                        notice_data.attachments.append(attachments_data)

                                    if (Doc_Download.response_contains_data(url_infoProcureDocAnnounZipAdj) == False) and infoProcureDocAnnounZipAdj == False:
                                        external_url = WebDriverWait(single_record2, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(2) > a'))).click()
                                        time.sleep(5)
                                        file_dwn = Doc_Download.file_download()
                                        attachments_data.external_url = str(file_dwn[0])
                                        attachments_data.file_name = single_record2.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
                                        download_already = True
                                        infoProcureDocAnnounZipAdj = True
                                        attachments_data.attachments_cleanup()
                                        notice_data.attachments.append(attachments_data)


                                if attachments_data.file_name == 'ประกาศเชิญชวน':

                                    if (Doc_Download.response_contains_data(s_external_url) == True) and s_external == False:
                                        s_external = True
                                        file_dwn = Doc_Download.switch_tab(s_external_url)                                    
                                        attachments_data.external_url = str(file_dwn)
                                        attachments_data.file_name = single_record2.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
                                        download_already = True
                                        attachments_data.attachments_cleanup()
                                        notice_data.attachments.append(attachments_data)
                                        if notice_data.notice_type == 4:
                                            try:
                                                folderpath = attachments_data.external_url.split('/th_gprogo')[1]
                                                pdfpath = NOTICE_ATTACHEMENTS_DIR +'/th_gprogo' + folderpath
                                                pdftext = ''
                                                with pdfplumber.open(pdfpath) as pdf:
                                                    for i in pdf.pages:
                                                        pdftext += i.extract_text()
                                                deadline = pdftext.split('ผู้ยื่นข้อเสนอต้องยื่นข้อเสนอและเสนอราคาทางระบบจัดซื้อจัดจ้างภาครัฐด้วยอิเล็กทรอนิกส์\n')[1].split('\n')[0]
                                                notice_deadline = GoogleTranslator(source='th', target='en').translate(deadline)
                                                notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
                                                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
                                                logging.info(notice_data.notice_deadline)
                                            except:
                                                pass
                                    try:
                                        process_tabs_and_download(download_already)
                                    except Exception as e:
                                        logging.info("Exception in Unable to convert PDF: {}".format(type(e).__name__)) 
                            except Exception as e:
                                logging.info("Exception in attachments: {}".format(type(e).__name__)) 
                                pass
                        try:
                            back_click = WebDriverWait(page_main, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'button.ui-dialog-titlebar-close')))
                            page_main.execute_script("arguments[0].click();",back_click)
                            time.sleep(3) 
                        except:
                            pass
                    except Exception as e:
                        logging.info("Exception in ebidding attachments: {}".format(type(e).__name__)) 
                        pass
                if  'ประกาศเชิญชวน' in single_record.text and 'ยกเลิกประกาศเชิญชวน' not in single_record.text :
                    try:                        
                        s_external_url = "https://process5.gprocurement.go.th/egp-approval-service/apv-common/infoProcureDocAnnounZip?projectId=" + notice_data.notice_no

                        if(Doc_Download.response_contains_data(s_external_url) == True) and s_external == False:
                            #Download pdf file
                            attachments_data = attachments()
                            s_external = True
                            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                            file_dwn = Doc_Download.switch_tab(s_external_url)                            
                            attachments_data.external_url = str(file_dwn)
                            download_already = True
                            attachments_data.attachments_cleanup()
                            notice_data.attachments.append(attachments_data)

                        if(Doc_Download.response_contains_data(s_external_url) == True) and tab_zip == False:
                            #Download zip file
                            attachments_data = attachments()
                            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                            file_dwn = Doc_Download.switch_tabZip(s_external_url)
                            tab_zip = True
                            attachments_data.external_url = str(file_dwn)
                            download_already = True
                            attachments_data.attachments_cleanup()
                            notice_data.attachments.append(attachments_data)

                            if notice_data.notice_type == 4 and 'ประกาศเชิญชวน' in single_record.text:
                                try:
                                    folderpath = attachments_data.external_url.split('/th_gprogo')[1]
                                    pdfpath = NOTICE_ATTACHEMENTS_DIR +'/th_gprogo' + folderpath
                                    pdftext = ''
                                    with pdfplumber.open(pdfpath) as pdf:
                                        for i in pdf.pages:
                                            pdftext += i.extract_text()
                                    deadline = pdftext.split('ผู้ยื่นข้อเสนอต้องยื่นข้อเสนอและเสนอราคาทางระบบจัดซื้อจัดจ้างภาครัฐด้วยอิเล็กทรอนิกส์\n')[1].split('\n')[0]
                                    notice_deadline = GoogleTranslator(source='th', target='en').translate(deadline)
                                    notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
                                    notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
                                    logging.info(notice_data.notice_deadline)
                                except:
                                    pass
                        if(Doc_Download.response_contains_data(s_external_url) == False):
                            try:
                                external_url = WebDriverWait(single_record, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(2) > a'))).click()
                            except:
                                external_url = WebDriverWait(single_record, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(2) > span'))).click()
                            download_already = False                            
                    except Exception as e:
                        logging.info("Exception in 'Invitation Announcement' attachments: {}".format(type(e).__name__)) 
                        pass

                if  'ประกาศรายชื่อผู้ชนะการเสนอราคา' in single_record.text:
                    winner_url = "https://process5.gprocurement.go.th/egp-approval-service/apv-common/infoApproveTemplate?projectId=" + notice_data.notice_no + "&templateType=W13" 

                    if(Doc_Download.response_contains_data(winner_url) == True) and winner == False:
                            #Download zip file
                        attachments_data = attachments()
                        attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                        file_dwn = Doc_Download.switch_tabwinner(winner_url)
                        winner = True
                        attachments_data.external_url = str(file_dwn)
                        download_already = True
                        attachments_data.attachments_cleanup()
                        notice_data.attachments.append(attachments_data)

                    if(Doc_Download.response_contains_data(winner_url) == False) and winner == False:
                        try:
                            click = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > span').click()
                            time.sleep(3)
                        except:
                            click = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').click()                                
                            time.sleep(3)
                        download_already = False

                if  'ยกเลิกประกาศเชิญชวน' in single_record.text:
                    try:
                        click = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > span').click()
                        time.sleep(3)
                    except:
                        click = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').click()                                
                        time.sleep(3)
                    download_already = False

                if 'ประกาศราคากลาง' in single_record.text:
                    median_price_url = "https://process5.gprocurement.go.th/egp-doc-price-estimate-service/dpe-common/infoDocPriceestZipHis?projectId="+ notice_data.notice_no
                    if(Doc_Download.response_contains_data(median_price_url) == True) and median_price == False:
                        attachments_data = attachments()
                        attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                        file_dwn = Doc_Download.switch_tabprice(median_price_url)
                        median_price = True
                        attachments_data.external_url = str(file_dwn)
                        download_already = True
                        attachments_data.attachments_cleanup()
                        notice_data.attachments.append(attachments_data)

                    s_external_url = "https://process5.gprocurement.go.th/egp-approval-service/apv-common/infoProcureDocAnnounZip?projectId=" + notice_data.notice_no
                    if(Doc_Download.response_contains_data(s_external_url) == False) and median_price == False:
                        try:
                            attachments_data = attachments()
                            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                            try:
                                external_url = WebDriverWait(single_record, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(2) > a'))).click()
                            except:
                                external_url = WebDriverWait(single_record, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(2) > span'))).click()
                            time.sleep(5)
                            file_dwn = Doc_Download.file_download()
                            attachments_data.external_url = str(file_dwn[0])
                            median_price = True
                            download_already = True
                            attachments_data.attachments_cleanup()
                            notice_data.attachments.append(attachments_data)
                        except:
                            pass

                if 'ข้อมูลรายชื่อผู้ขอรับ/ซื้อเอกสาร' in single_record.text or 'ข้อมูลรายชื่อผู้ยื่นเอกสาร' in single_record.text or 'ข้อมูลรายชื่อผู้ผ่านการพิจารณาคุณสมบัติและเทคนิค' in single_record.text or 'ข้อมูลสาระสำคัญในสัญญา' in single_record.text:
                    try:
                        try:
                            notice_text = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(2) > a').click()
                        except:
                            notice_text = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(2) > span').click()
                        time.sleep(3)
                        notice_data.notice_text += page_main.find_element(By.XPATH,'/html/body/form/table[1]').get_attribute("outerHTML")                      
                        page_main.execute_script("window.history.go(-1)")
                        time.sleep(3)
                    except:
                        pass
                try:
                    process_tabs_and_download(download_already)
                except Exception as e:
                    logging.info("Exception in Unable to convert PDF: {}".format(type(e).__name__)) 
                    pass
            except Exception as e:
                logging.info("Exception in eachrecord attachments: {}".format(type(e).__name__)) 
                pass
            try:
                process_tabs_and_download(download_already)
            except Exception as e:
                logging.info("Exception in Unable to convert PDF: {}".format(type(e).__name__)) 
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    try:
        page_main.find_element(By.XPATH,'/html/body/div[5]/div[1]/button').click()
    except:
        pass
    try:
        time.sleep(1)
        page_main.execute_script("window.history.go(-1)")
        time.sleep(1)
        page_main.execute_script("window.history.go(-1)")
        time.sleep(2)
        WebDriverWait(page_main, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="form1"]/table[1]/tbody/tr/td/table[3]/tbody/tr')))
    except Exception as e:
        logging.info("Exception in Moving back to index page: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier =  str(notice_data.script_name) + str(notice_data.publish_date) + str(notice_data.notice_no) +  str(notice_data.notice_type) 
    logging.info(notice_data.identifier)
    #duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    #NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    #if duplicate_check_data[0] == False:
        #return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1

    if page_no > 1 and next_page_bool == True:
        back_to_page = WebDriverWait(page_main, 30).until(EC.element_to_be_clickable((By.XPATH,f'(//td[@id="tdpage2"])/b/font/u[contains(text(),"{page_no-1}")]|(//td[@id="tdpage2"])/following-sibling::td[contains(text(),"{page_no-1}")]'))).click()
        time.sleep(3)
    logging.info('----------------------------------')

def download_pdf_from_tab(page, tab_index):
    try:
        page.switch_to.window(page_main.window_handles[tab_index])
                 
        # Execute JavaScript to trigger the print-to-pdf function
        pdf_data = page.execute_cdp_cmd("Page.printToPDF", {
            "landscape": False,
            "displayHeaderFooter": False,
            "printBackground": True,
            "preferCSSPageSize": True
        })

        pdf_content = pdf_data['data']
        pdf_bytes = base64.b64decode(pdf_content)

        with open(f"webpage_{tab_index}.pdf", "wb") as pdf_file:
            pdf_file.write(pdf_bytes)

        file_dwn = Doc_Download.file_download()
        attachments_data = attachments()
        attachments_data.file_name = f'Document_{tab_index}'
        attachments_data.external_url = str(file_dwn[0])

        return attachments_data

    except Exception as e:
        logging.info(f"Error downloading PDF from tab {tab_index}: {e}")
        return None

def close_tab(page, tab_index):
    try:
        page.switch_to.window(page.window_handles[tab_index])
        page.close()
        page.switch_to.window(page.window_handles[0])
    except Exception as e:
        logging.info(f"Error closing tab {tab_index}: {e}")

def process_tabs_and_download(download_already):
    # Assuming 'attachments' and 'Doc_Download' classes are defined
    # Assuming 'notice_data' is defined

    # Iterate over each open tab (excluding the main one)
    for tab_index in range(1, len(page_main.window_handles)):

        if(download_already is False):
            attachments_data = download_pdf_from_tab(page_main, tab_index)

            if attachments_data is not None:
                # Process attachments_data as needed
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)

        # Close the tab whether download was successful or not
        close_tab(page_main, tab_index)

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
            WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="home-popup-close-button"]'))).click()
            time.sleep(3)
        except:
            pass
        clk2=WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="layoutContainers"]/div[2]/div[7]/div/div/div[2]/div/div/section/div[2]/div[2]/div[2]/div/div/div/form/div[4]/div[2]/a'))).click()
        time.sleep(2)
        select_announceType = Select(page_main.find_element(By.XPATH,'//*[@id="announceType"]'))
        time.sleep(2)
        
        select_announceType.select_by_index(announceType)
        time.sleep(2)
        selected_option = select_announceType.first_selected_option
        selectannounceType = selected_option.text

#         select_deptId = Select(page_main.find_element(By.XPATH,'//*[@id="deptId"]'))
#         time.sleep(2)
#         select_deptId.select_by_index(deptId)
#         time.sleep(2)

        select_methodId = Select(page_main.find_element(By.XPATH,'//*[@id="methodId"]'))
        time.sleep(2)
        select_methodId.select_by_index(int(methodId))
        time.sleep(2)
        page_main.find_element(By.XPATH,'//*[@id="announceSDate"]').clear()
        page_main.find_element(By.XPATH,'//*[@id="announceSDate"]').send_keys(str(start_date))
        time.sleep(2)
        
        page_main.find_element(By.XPATH,'//*[@id="announceEDate"]').clear()
        page_main.find_element(By.XPATH,'//*[@id="announceEDate"]').send_keys(str(end_date))
        time.sleep(2)
        
#         page_main.find_element(By.XPATH,'//*[@id="project_id"]').clear()
#         page_main.find_element(By.XPATH,'//*[@id="project_id"]').send_keys(str(project_id))
#         time.sleep(3)
        
        search_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="idBtn"]/table/tbody/tr/td[2]/input[1]')))
        page_main.execute_script("arguments[0].click();",search_click)
        time.sleep(2)
        captcha()
        for page_no in range(2,200):
            try:
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH, "//tr[@style='']"))).text
            except:
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH, "/html/body/form/table[1]/tbody/tr/td/table[3]/tbody/tr[2]")))
                if 'ค้นหาข้อมูลในฐานข้อมูลไม่พบ' in page_check.text:
                    break
            rows = WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.XPATH,"//tr[@style='']")))
            length = len(rows)
            logging.info(length)
            
            for each_record in range(0,length):
                tender_html_element = WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.XPATH, "//tr[@style='']")))[each_record]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break
                if notice_count == 50:
                    output_json_file.copyFinalJSONToServer(output_json_folder)
                    output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                    notice_count = 0
                    
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
        logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
