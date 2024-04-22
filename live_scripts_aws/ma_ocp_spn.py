from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ma_ocp_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from deep_translator import GoogleTranslator
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ma_ocp_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ma_ocp_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'MA'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'MAD'
    
    notice_data.main_language = 'FR'

    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    
    try:
        class_title_at_source = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div:nth-child(4) > div:nth-child(1)').text.split(':')[1].strip()
        notice_data.class_title_at_source = GoogleTranslator(source='auto', target='en').translate(class_title_at_source)
    except Exception as e:
        logging.info("Exception in class_title_at_source: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'div:nth-child(2) > div:nth-child(4) > div:nth-child(2)').text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div:nth-child(1) > div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, "#main").get_attribute('outerHTML')
    except:
        pass

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, "//*[contains(text(),'Code du dossier')]//following::div[1]").text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = page_details.find_element(By.XPATH, "//*[contains(text(),'Description')]//following::div[1]").text
        notice_data.notice_title =GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Catégorie de travaux')]//following::div[1]").text
        if 'Servizi' in notice_data.contract_type_actual or 'Lavori' in notice_data.contract_type_actual or 'Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Fournitures' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Travaux' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Description')]//following::div[1]").text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except:
        pass

    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Type de procédure')]//following::div[1]").text
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/ma_ocp_spn_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR,"#opportunityDetailFEBean > div > div:nth-child(13) > div > ul > li > table > tbody > tr.table_cnt_body_a > td:nth-child(5)").text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:  
        for single_record in page_details.find_elements(By.CSS_SELECTOR,'div:nth-child(13) > div > ul > li > table > tbody > tr   a'):
            attachments_data = attachments()
            external_url = single_record.click()
            time.sleep(5)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])

            attachments_data.file_name = single_record.text.split('.')[0].strip()

            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = page_details.find_element(By.XPATH, "(//*[contains(text(),'Organisation Acheteur')]//following::div[1])[1]").text
        customer_details_data.org_country = 'MA'
        customer_details_data.org_language = 'FR'

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, "(//*[contains(text(),'Contact')]//following::div[1])[1]").text
        except:
            pass

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, "(//*[contains(text(),'E-mail')]//following::div[1])[1]").text
        except:
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try: 
        page_details.find_element(By.CSS_SELECTOR, "#opportunityDetailFEBean > div > div:nth-child(9) > div > ul > li > table > tbody > tr")
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, "#opportunityDetailFEBean > div > div:nth-child(9) > div > ul > li > table > tbody > tr")[1:]:
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

            try:
                lot_description_click = single_record.find_element(By.CSS_SELECTOR, 'td.tdAction.col__fixed_ > button')
                page_details.execute_script("arguments[0].click();",lot_description_click)
                time.sleep(2)
                page_details.switch_to.window(page_details.window_handles[1]) 
            except:
                pass


            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH,"(//*[contains(text(),'Description courte')]//following::td[1])[1]").text
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass


            try:
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass

            try:
                lot_details_data.contract_type = notice_data.notice_contract_type
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except:
        pass
    
    if notice_data.publish_date == None:
        try:
            publish_date = page_details.find_element(By.XPATH,"(//*[contains(text(),'Publication')]//following::td[1])[1]").text
            publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return
    
    try:  
        attachments_data = attachments()
        # Onsite Field -RFP Document 
        external_url = page_details.find_element(By.CSS_SELECTOR,"#cntDetail > input[type=button]:nth-child(4)").click()
        time.sleep(5)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])

        attachments_data.file_name = "Télécharger en PDF"
        # Onsite Field -RFP Document

        try:
            attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, "#unused-cntAllPage").get_attribute('outerHTML')
    except:
        pass
    
    page_details.switch_to.window(page_details.window_handles[0]) 
    
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = Doc_Download.page_details 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://supplier.ocpgroup.ma/#/landing-page/opportunities"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(1,4):
                page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[2]/div/div[3]/div[2]/div[2]/div'))).text
                rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div/div[3]/div[2]/div[2]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div/div[3]/div[2]/div[2]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="root"]/div[2]/div/div[3]/div[2]/div[3]/div/div/div[2]/button[2]')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div[2]/div/div[3]/div[2]/div[2]/div'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
        except:
            logging.info("No new record")
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
