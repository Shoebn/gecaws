from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_trascultura_ca"
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
SCRIPT_NAME = "it_trascultura_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"


def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'it_trascultura_ca'
    notice_data.main_language = 'IT'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 7

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(4) > div").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    notice_data.document_type_description = 'aggiudicazione di appalti pubblici'

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(1) > a').get_attribute("href")      

        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2) > div').text
        
    except:
        try:
            notice_no = notice_data.notice_url.split('-gare-e-contratti_')[1].split('_960_1')[0]
            notice_data.notice_no = notice_no
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#reviewOggetto > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Ufficio: ")]//following::a[1]').text 

        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"RUP: ")]//following::a[1]').text 
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1

        lot_details_data.lot_title = notice_data.notice_title 
        notice_data.is_lot_default = True

        try:
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title) 
        except Exception as e:
            logging.info("Exception in lot_title: {}".format(type(e).__name__))

        try:
            contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Tempi di completamento dell")]//following::div[1]').text 
            contract_start_date = re.findall('\d+-\d+-\d{4}',contract_start_date)[0]
            lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
            pass
        try:
            contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Tempi di completamento dell")]//following::div[2]').text          
            contract_end_date = re.findall('\d+-\d+-\d{4}',contract_end_date)[0]
            lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
            pass

        try:
            award_details_data = award_details()

            award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Aggiudicatari")]//following::li[1]').text 
            try:
                grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importi")]//following::div[2]').text
                grossawardvaluelc = re.sub("[^\d\.\,]", "", grossawardvaluelc)  
                award_details_data.grossawardvaluelc = float(grossawardvaluelc.replace('.','').replace(',','.').strip()) 
            except Exception as e:
                logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                pass
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importi")]//following::div[1]').text
        grossbudgetlc = re.sub("[^\d\.\,]", "", grossbudgetlc) 
        notice_data.grossbudgetlc = float(grossbudgetlc.replace('.','').replace(',','.').strip())
        
        notice_data.est_amount =  notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.campoOggetto48'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.text.split(':')[0]            
                
            attachments_data.external_url = single_record.find_element(By.XPATH, 'a').get_attribute('href')                
                            
            try:     
                if '.pdf' in attachments_data.external_url:
                    attachments_data.file_type = 'pdf'

                elif '.doc' in attachments_data.external_url:
                    attachments_data.file_type = 'doc'

                else:
                    attachments_data.file_type = 'zip'

            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            try:
                file_description = single_record.find_element(By.CSS_SELECTOR, 'a').text
                attachments_data.file_description = file_description .split('.pdf')[0]
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass

            try:
                file_size = single_record.find_element(By.CSS_SELECTOR, 'div.campoOggetto48 span').text  
                
                file_size =file_size.split('Aggiornato il')[1]
                attachments_data.file_size = file_size.split('-')[1].split('-')[0]
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
    
    urls = ["https://trasparenza.cultura.gov.it/pagina960_affidamenti-diretti-di-lavori-servizi-e-forniture-di-somma-urgenza-e-di-protezione-civile.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="regola_default"]/div[2]/div/section/div[2]//tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="regola_default"]/div[2]/div/section/div[2]//tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="regola_default"]/div[2]/div/section/div[2]//tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'>successiva')))   
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="regola_default"]/div[2]/div/section/div[2]//tbody/tr[2]'),page_check))   
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
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
