from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_maggiolicloud_spn"
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
SCRIPT_NAME = "it_maggiolicloud_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'it_maggiolicloud_spn'
    notice_data.main_language = 'IT'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    # Onsite Field -Data pubblicazione
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(5)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    # Onsite Field -Data scadenza
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(6)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipologia appalto
    # Onsite Comment -None

    try:
        contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text.split(':')[1].strip()
        if "Servizi" in contract_type_actual:
            notice_data.notice_contract_type ="Service"
        elif "Lavori" in contract_type_actual:
            notice_data.notice_contract_type ="Works"
        elif "forniture" in contract_type_actual:
            notice_data.notice_contract_type ="Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(4)').text
        est_amount = re.sub("[^\d\.\,]", "", est_amount)
        notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.netbudgetlc = notice_data.est_amount
        notice_data.netbudgeteuro = notice_data.netbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Titolo
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2)').text.split(':')[1].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-action > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
 
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.responsive.content').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
        
    # Onsite Field -Riferimento procedura
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(7)').text.split(':')[1].strip()
    except: 
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Titolo :")]/..').text.split('CIG :')[1].split('-')[0].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Procedura di gara : ")]/..').text.split(':')[1].strip()
        type_of_procedure_en = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_maggiolicloud_spn_procedure.csv",type_of_procedure_en)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass


    try:              
        customer_details_data = customer_details()
    # Onsite Field -Stazione appaltante
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-item > div:nth-child(1)').text.split(':')[1].strip()
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//label[contains(text(),"RUP : ")]/..').text.replace('RUP : ','').strip()
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

        customer_details_data.org_language = 'IT'
        customer_details_data.org_country = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

# Onsite Field -None
# Onsite Comment -click on Lotti for details
    try:
        url1= page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(13) > ul > li > a').get_attribute("href")                     
        fn.load_page(page_details1,url1,80)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, 'div.responsive.content').get_attribute("outerHTML")                     
    except:
        pass

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
    # Onsite Field -Titolo
    # Onsite Comment -None
        lot_details_data.lot_title = page_details1.find_element(By.CSS_SELECTOR, 'div.first-detail-section.last-detail-section > div:nth-child(2)').text.split(':')[1].strip()
        lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
        lot_details_data.contract_type = notice_data.notice_contract_type
    # Onsite Field -Importo a base di gara
    # Onsite Comment -None
        try:
            lot_netbudget = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section.first-detail-section.last-detail-section > div:nth-child(3)').text
            lot_netbudget = re.sub("[^\d\.\,]", "", lot_netbudget)
            lot_details_data.lot_netbudget = float(lot_netbudget.replace('.','').replace(',','.').strip())
            lot_details_data.lot_netbudget_lc = lot_details_data.lot_netbudget
        except Exception as e:
            logging.info("Exception in lot_netbudget: {}".format(type(e).__name__))
            pass
    # Onsite Field -split data from "CIG" till "CUP"
    # Onsite Comment -None
        try:
            lot_details_data.lot_actual_number = page_details1.find_element(By.CSS_SELECTOR, 'div.first-detail-section.last-detail-section > div:nth-child(2)').text.split('CIG :')[1].split('-')[0].strip()
        except Exception as e:
            logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
            pass

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.category = ''
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div.detail-section div:nth-child(1)')[1:]:
            notice_data.category += single_record.text.split('- ')[1].split('\n')[0].strip() + ' ,'
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:
        documenti_url = page_details.find_element(By.XPATH, "//*[contains(text(),'Altri atti e documenti')]").get_attribute("href")
        fn.load_page(page_details2,documenti_url,80)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details2.find_element(By.CSS_SELECTOR, 'div.responsive.content').get_attribute("outerHTML")                     
    except:
        pass
    
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'a.bkg.pdf'):
            file_name = single_record.text
            if file_name != '':
                attachments_data = attachments()

                attachments_data.file_name = single_record.text.strip()

                attachments_data.external_url = single_record.get_attribute('href')

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
        
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'a.bkg.download'):
            file_name = single_record.text
            if file_name != '':
                attachments_data = attachments()

                attachments_data.file_name = single_record.text.strip()

                attachments_data.external_url = single_record.get_attribute('href')

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'a.bkg.pdf'):
            file_name = single_record.text
            if file_name != '':
                attachments_data = attachments()

                attachments_data.file_name = single_record.text

                attachments_data.external_url = single_record.get_attribute('href')

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except:
        try:  
            for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'a.bkg.download'):
                file_name = single_record.text
                if file_name != '':
                    attachments_data = attachments()

                    attachments_data.file_name = single_record.text

                    attachments_data.external_url = single_record.get_attribute('href')

                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
page_details2 = fn.init_chrome_driver(arguments)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://appalti-villasofia-cervello.maggiolicloud.it/PortaleAppalti/it/ppgare_bandi_lista.wp?_csrf=B7N7HM5ORQFU6TQ6PCZA4DWMRWDDDFD8"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div[2]/form[2]/div')))
            length = len(rows)
            for records in range(2,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div[2]/form[2]/div')))[records]
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
    page_details1.quit()
    page_details2.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
