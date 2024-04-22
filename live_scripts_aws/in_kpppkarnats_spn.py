from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_kpppkarnats_spn"
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
import gec_common.Doc_Download_ingate
import cv2
from pytesseract import image_to_string
import pytesseract
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_kpppkarnats_spn"
Doc_Download = gec_common.Doc_Download_ingate.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element,extract_and_save_notice):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'in_kpppkarnats_spn'

    notice_data.main_language = 'EN'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'INR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.notice_contract_type = 'Service'
    notice_data.contract_type_actual = 'Service'
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text  
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text  
        notice_data.notice_title = notice_data.local_title 
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.kebab > lib-icon:nth-child(1) > img').get_attribute("href")        
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        notice_data.est_amount = float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(8)").text

        publish_date = publish_date.strip()
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(9)").text
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text 

        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text  
        except Exception as e:
            logging.info("Exception in org_adderss: {}".format(type(e).__name__))
            pass            
        
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
    
        view_tenders_click = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td.kebab > lib-icon:nth-child(1)')))  
        page_main.execute_script("arguments[0].click();",view_tenders_click)
        time.sleep(5)
    
        try:
            org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"ಕಛೇರಿ ದೂರವಾಣಿ ಸಂಖ್ಯೆ")]//following::div[1]').text      
            if len(org_phone)>5:
                customer_details_data.org_phone = org_phone
            else:
                org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"ಮೊಬೈಲ್ ದೂರವಾಣಿ ಸಂಖ್ಯೆ")]//following::div[1]').text      
                customer_details_data.org_phone = org_phone
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
            
        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Contact Person Name:")]//following::div[1]').text  
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.earnest_money_deposit = page_main.find_element(By.XPATH, '//*[contains(text(),"ಮುಂಗಡ ಹಣ ಠೇವಣಿ ಮೊತ್ತ(INR)")]//following::div[1]').text   
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Scope")]//following::div[1]').text 
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(5)').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        notice_data.eligibility = page_main.find_element(By.XPATH, '//*[contains(text(),"General Conditions of Eligibility")]//following::div[1]').text  
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_duration = page_main.find_element(By.XPATH, '//*[contains(text(),"ಬೆಲೆ ಕೂಗು ಊರ್ಜಿತ ಅವಧಿ")]//following::div[1]').text  
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    try:
        Tender_Group_Items = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'tr > td:nth-child(4) > lib-icon')))
        page_main.execute_script("arguments[0].click();", Tender_Group_Items)
        time.sleep(10)
    except:
        pass

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#serviceItemDetails > tbody > tr'):
            lot_details_data = lot_details()
            
            lot_details_data.contract_type = notice_data.notice_contract_type
            lot_details_data.lot_contract_type_actual  = notice_data.notice_contract_type

            lot_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            lot_details_data.lot_number = int(lot_number)

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            lot_details_data.lot_title_english = lot_details_data.lot_title

            try:
                lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, '#serviceItemDetails  tr > td:nth-child(4)').text  
                lot_details_data.lot_description_english = lot_details_data.lot_description
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text  
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass

            try:
                lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
                lot_details_data.lot_quantity = float(lot_quantity)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass

            try:
                lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(11)').text
                lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.document_fee = page_main.find_element(By.XPATH, '//*[contains(text(),"ಟೆಂಡರ್ ಶುಲ್ಕ (INR)")]//following::div[1]').text 
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass
    
    back_to_main_page_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//button[@id="idButton"]')))
    page_main.execute_script("arguments[0].click();",back_to_main_page_click)                            
    time.sleep(5)
 
    services_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#stepperTabLabel2 > a')))
    page_main.execute_script("arguments[0].click();",services_click)
    time.sleep(5)

    try:
        attachment_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,f'//*[@id="services"]/tbody/tr[{iteration}]/td[10]/lib-icon[2]')))
        page_main.execute_script("arguments[0].click();", attachment_click)  
        time.sleep(5)
    except:
        attachment_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,f'//*[@id="services"]/tbody/tr[{iteration}]/td[10]/lib-icon[2]')))
        page_main.execute_script("arguments[0].click();", attachment_click)  
        time.sleep(5)
        
    try:

        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#table > tbody> tr'):
            attachments_data = attachments()
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
            time.sleep(10)

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments_data: {}".format(type(e).__name__)) 
        pass
            
    bck =  WebDriverWait(page_main, 15).until(EC.element_to_be_clickable((By.XPATH,'//button[@id="idButton"]')))
    page_main.execute_script("arguments[0].click();",bck)
    time.sleep(5)
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="services"]/tbody/tr'))).text
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
page_main = Doc_Download.page_details

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://kppp.karnataka.gov.in/#/portal/searchTender/live"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        time.sleep(5)
        logging.info('----------------------------------')
        logging.info(url)
        
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
        
        services_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#stepperTabLabel2 > a')))
        page_main.execute_script("arguments[0].click();",services_click)
        time.sleep(5)

        pages = 4
        try:
            for page_no in range(1,9):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="services"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="services"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    iteration = records+1
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="services"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element,iteration)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:
                    if pages == 6:
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[@id="pagination-controls"]/ul/li[6]/a/span[2])[2]')))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        time.sleep(5)
                        WebDriverWait(page_main, 100).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="services"]/tbody/tr'),page_check))
                    else:
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[@id="pagination-controls"]/ul/li['+str(pages)+']/a/span[2])[2]')))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        time.sleep(5)
                        WebDriverWait(page_main, 100).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="services"]/tbody/tr'),page_check))
                        pages +=1
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
