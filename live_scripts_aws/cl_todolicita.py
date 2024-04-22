#excluding the "Local_title /  Local_description "all fields should be in English
#innerHTML attribute  is  used throughout, because .text is scraping blank information

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cl_todolicita"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cl_todolicita"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'cl_todolicita'

    notice_data.notice_type = 4
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CL'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2

    notice_data.main_language = 'ES'
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "p > span:nth-child(4)").get_attribute('innerHTML')
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return 

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "p > span:nth-child(6)").get_attribute('innerHTML')
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    
    try:
        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, "p > span:nth-child(7)").get_attribute('innerHTML').split('Código: ')[1]
        except:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, "p > span:nth-child(9)").get_attribute('innerHTML').split('Código: ')[1]                                                                                                                
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    

    try:
        document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'p > span:nth-child(2) > span').get_attribute('innerHTML')
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.title.h6.text-primary > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.local_title = page_details.find_element(By.XPATH, "//*[contains(text(),'Descripcion')]//following::div[1]").get_attribute('innerHTML')
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#profile > div.page-content > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Descripcion')]//following::div[1]").get_attribute('innerHTML')
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_summary_english = page_details.find_element(By.XPATH, "//*[contains(text(),'Descripcion')]//following::div[1]").get_attribute('innerHTML')
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        grossbudgetlc = page_details.find_element(By.XPATH, "//*[contains(text(),'Monto estimado')]//following::div[1]").get_attribute('innerHTML').split('$ ')[1]
        notice_data.grossbudgetlc = GoogleTranslator(source='es', target='en').translate(grossbudgetlc).replace(',','').split('</')[0].split('<span>')[1]
        notice_data.grossbudgetlc = int(notice_data.grossbudgetlc)
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass


    try:
        notice_data.currency = page_details.find_element(By.XPATH, "//*[contains(text(),'Moneda')]//following::div[1]").get_attribute('innerHTML')
    except Exception as e:
        logging.info("Exception in currency: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()

        try:
            org_name = page_details.find_element(By.XPATH, '//*[@id="profile"]/div[3]/div/div/div[2]/div[1]/div/div[1]/div[2]/a').get_attribute('innerHTML')
            customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

        try:
            org_unidad = page_details.find_element(By.XPATH, '//*[@id="profile"]/div[3]/div/div/div[2]/div[1]/div/div[2]/div[2]/a').get_attribute('innerHTML')

            org_rut = page_details.find_element(By.XPATH, '//*[@id="profile"]/div[3]/div/div/div[2]/div[1]/div/div[3]/div[2]').get_attribute('innerHTML')

            org_region = page_details.find_element(By.XPATH, '//*[@id="profile"]/div[3]/div/div/div[2]/div[1]/div/div[4]/div[2]/a').get_attribute('innerHTML')

            org_comuna = page_details.find_element(By.XPATH, '//*[@id="profile"]/div[3]/div/div/div[2]/div[1]/div/div[5]/div[2]/a').get_attribute('innerHTML')

            org_direccion = page_details.find_element(By.XPATH, '//*[@id="profile"]/div[3]/div/div/div[2]/div[1]/div/div[6]/div[2]').get_attribute('innerHTML')
        except Exception as e:
            logging.info("Exception in org_add_details: {}".format(type(e).__name__))
            pass

        try:
            org_address = str(org_unidad)+str(org_rut)+str(org_region)+str(org_comuna)+str(org_direccion)
            customer_details_data.org_address = GoogleTranslator(source='es', target='en').translate(org_address)
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'CL'
        customer_details_data.org_language = 'ES'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    lot_number =  1
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.profile-box.info-box.contact.card.mb-4 div.content.p-4 div.info-line.mb-6'):
            lot_details_data = lot_details()
            lot_details_data.lot_number =  lot_number

            try:
                lot_title = single_record.find_element(By.CSS_SELECTOR, "div.title.font-weight-bold.mb-1").get_attribute('innerHTML').split('</a>')[0].split('href=\"')[1].split('">')[1]
                lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass


            try:
                lot_description = single_record.find_element(By.CSS_SELECTOR, "div.info").get_attribute('innerHTML')
                lot_details_data.lot_description = GoogleTranslator(source='auto', target='en').translate(lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

            try:
                lot_quantity = single_record.find_element(By.CSS_SELECTOR, "table.info.jobs tbody tr:nth-child(1) td:nth-child(2)").get_attribute('innerHTML').split(' ')[0]
                lot_quantity = float(lot_quantity)
                lot_details_data.lot_quantity = lot_quantity
                lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, "table.info.jobs tbody tr:nth-child(1) td:nth-child(2)").get_attribute('innerHTML').split(' ')[1]
                lot_details_data.lot_quantity_uom = GoogleTranslator(source='auto', target='en').translate(lot_quantity_uom)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass

            try:
                lot_details_data.lot_grossbudget_lc = notice_data.grossbudgetlc
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass

            

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number+= 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    
    for page_no in range(0,20):
        urls = ["https://todolicitaciones.cl/busqueda/licitaciones?textSearch=&currentPage="+str(page_no)+"&orderByType=date&ESTADO=Publicada"] 
        for url in urls:
            fn.load_page(page_main, url, 50)
            logging.info('----------------------------------')
            logging.info(url)
            try:
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/main/div[1]/div/div/div[1]/div[3]/div/div/div/div[3]/div/div'))).text
                rows_path = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/main/div[1]/div/div/div[1]/div[3]/div/div/div/div[3]/div')))
                rows = WebDriverWait(rows_path, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.result-item.mb-8')))
    
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/main/div[1]/div/div/div[1]/div[3]/div/div/div/div[3]/div/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
