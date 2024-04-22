from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_kpppkarnat_ppn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download_ingate as Doc_Download
import cv2
from pytesseract import image_to_string
import pytesseract
from selenium.webdriver.common.keys import Keys
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

#Note:Fill the captcha to get tender data
#Note:Open site than click this  "PQ ಟೆಂಡರ್‌ಗಳನ್ನು ಹುಡುಕಿ" and grab the data
#Note:for opening detail page make sure that tender html page is in local language then only it will grab all data

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
row_num = 1
SCRIPT_NAME = "in_kpppkarnat_ppn"
Doc_Download = gec_common.Doc_Download_ingate.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global row_num
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'in_kpppkarnat_ppn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'INR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -Note:If the tender title start with "EXPRESSION OF INTEREST", "EOI" Invitation for Expression of Interest "  will be notice type 5"

    
    # Onsite Field -ಟೆಂಡರ್ ಸಂಖ್ಯೆ
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -ಟೆಂಡರ್ ಶೀರ್ಷಿಕೆ
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = notice_data.local_title
        if 'Expression of Interest' in notice_data.notice_title or 'Expression Of Interest (Eoi)' in  notice_data.notice_title or 'Invitation for Expression of Interest' in notice_data.notice_title or 'EXPRESSION OF INTEREST' in notice_data.notice_title:
            notice_data.notice_type = 5
        else:
            notice_data.notice_type = 6
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -ಎನ್ ಐ ಟಿ ಪ್ರಕಟಿಸಿದ ದಿನಾಂಕ
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    org_name=tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(4)').text


    
    # Onsite Field -ಬೆಲೆ ಕೂಗು ಸಲ್ಲಿಸಲು ಕೊನೆಯ ದಿನಾಂಕ
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(8)").text
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

                                                        
    try:
        notice_url_click =  WebDriverWait(tender_html_element, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td.kebab > lib-icon:nth-child(1)')))
        page_main.execute_script("arguments[0].click();",notice_url_click)
        time.sleep(10) 
        notice_data.notice_url = page_main.current_url
    except:
        notice_data.notice_url = url  
         
                                                        
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Scope:")]//following::div[1]').text
        notice_data.notice_summary_english =  notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -General Conditions of Eligibility
#     # Onsite Comment -None
    try:
        notice_data.eligibility = page_main.find_element(By.CSS_SELECTOR, '#idNameCard').text
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Tender Processing Fee:
#     # Onsite Comment -None

    try:
        notice_data.document_fee = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Processing Fee:")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass
        
#     # Onsite Field -ಬೆಲೆ ಕೂಗು ಊರ್ಜಿತ ಅವಧಿ:
#     # Onsite Comment -None

    try:
        notice_data.contract_duration = page_main.find_element(By.XPATH, '//*[contains(text(),"ಬೆಲೆ ಕೂಗು ಊರ್ಜಿತ ಅವಧಿ:")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass   
    
    
#     # Onsite Field -Date and Time for Opening of Pre Qualification Bid:
#     # Onsite Comment -None

    try:
        document_opening_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Date and Time for Opening of Pre Qualification Bid:")]//following::div[1]').text
        document_opening_time  = re.findall('\d+-\d+-\d{4}',document_opening_time)[0]
        notice_data.document_opening_time  = datetime.strptime(document_opening_time,'%d-%m-%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass    
    
    try:              
#         for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(5)'):
        customer_details_data = customer_details()
    # Onsite Field -ಸಂಪಾದನೆ ಘಟಕ
    # Onsite Comment -None

        customer_details_data.org_name = org_name

    # Onsite Field -ವಿಳಾಸ:
    # Onsite Comment -None

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"ವಿಳಾಸ:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # Onsite Field -ನಗರ:
    # Onsite Comment -None

        try:
            customer_details_data.org_city = page_main.find_element(By.XPATH, '//*[contains(text(),"ನಗರ:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -ರಾಜ್ಯ:
    # Onsite Comment -None

        try:
            customer_details_data.org_state = page_main.find_element(By.XPATH, '//*[contains(text(),"ರಾಜ್ಯ:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass

    # Onsite Field -ಪಿನ್:
    # Onsite Comment -None

        try:
            customer_details_data.postal_code = page_main.find_element(By.XPATH, '//*[contains(text(),"ಪಿನ್:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

    # Onsite Field -Contact Person Name:
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Contact Person Name:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # Onsite Field -ಮೊಬೈಲ್ ದೂರವಾಣಿ ಸಂಖ್ಯೆ:
    # Onsite Comment -None
        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"ಕಛೇರಿ ದೂರವಾಣಿ ಸಂಖ್ಯೆ")]//following::div[1]').text
            if customer_details_data.org_phone == '---':
                customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"ಮೊಬೈಲ್ ದೂರವಾಣಿ ಸಂಖ್ಯೆ")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass    
    try:
        notice_data.notice_text += page_main.find_element(By.XPATH, '//*[@id="box"]').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    bck =  WebDriverWait(page_main, 15).until(EC.element_to_be_clickable((By.XPATH,'//button[@id="backButton"]')))
    page_main.execute_script("arguments[0].click();",bck)
    time.sleep(15)
    
    try:
        attach_click = page_main.find_element(By.XPATH, '//*[@id="prequalTable"]/tbody/tr['+str(row_num)+']/td[9]/lib-icon[2]/img')
        page_main.execute_script("arguments[0].click();",attach_click)
    except:
        pass
 
    time.sleep(10) 
    
    
    try:
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#table > tbody> tr'):
            attachments_data = attachments()
    #         # Onsite Field -File Name
    #         # Onsite Comment -Note:Don't take file extention

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        
            try:
                attachments_data.file_type = attachments_data.file_name.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass


            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass

            external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > lib-icon').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            time.sleep(20)

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)

    except:
        pass
    
    bck =  WebDriverWait(page_main, 15).until(EC.element_to_be_clickable((By.XPATH,'//button[@id="idButton"]')))
    page_main.execute_script("arguments[0].click();",bck)
    time.sleep(15)
    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    row_num += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://kppp.karnataka.gov.in/#/portal/searchTender/live"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(20)
        while True:
            imageName = "captcha-image.png"
            time.sleep(2)
            img = page_main.find_element(By.ID, "captcahCanvas")
            time.sleep(2)
            screenshot = img.screenshot_as_png
            with open(imageName, "wb") as f:
                f.write(screenshot)
            img = cv2.imread(imageName)
            gry = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            (h, w) = gry.shape[:2]
            gry = cv2.resize(gry, (w*2, h*2))
            cls = cv2.morphologyEx(gry, cv2.MORPH_CLOSE, None)
            thr = cv2.threshold(cls, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            extracted_text = image_to_string(thr)

            # Parse text to remove spaces
            parsedText = extracted_text.replace(" ", "")
            

            input1 = page_main.find_element(By.XPATH,'//*[@id="AuctionCaptcha"]/div/div[2]/ngx-captcha/div/div/input[1]').send_keys(parsedText)
            time.sleep(3)
            
            Search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="AuctionCaptcha"]/div/div[2]/ngx-captcha/div/div/input[2]')))
            page_main.execute_script("arguments[0].click();",Search)
            
            try:
                table_row = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#works > tbody > tr'))).text
                break
            except:
                try:
                    elementRefresh = page_main.find_element(By.CSS_SELECTOR, "a.cpt-btn.reload")  
                    elementRefresh.click()
                    input1 = page_main.find_element(By.XPATH,'//*[@id="AuctionCaptcha"]/div/div[2]/ngx-captcha/div/div/input[1]').clear()
                except:
                    pass

        bck = WebDriverWait(page_main, 15).until(EC.element_to_be_clickable((By.XPATH,"//a[@ID='tab-sliderTabLabel1']")))
        page_main.execute_script("arguments[0].click();",bck)
        time.sleep(10)
        
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="prequalTable"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="prequalTable"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="prequalTable"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="prequalTable"]/tbody/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info('No new record')
            break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
