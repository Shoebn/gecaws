from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_aric"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_aric"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_aric'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
        
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
  

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass



    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(2)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} - \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y - %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(3)').text
        if 'Lavori pubblici' in notice_data.notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'Servizi' in notice_data.notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Forniture' in notice_data.notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
 
    try:
        notice_data.document_type_description = 'Bandi di gara e contratti'
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass


    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)  
    except:
        notice_data.notice_url = url
 
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'section.col-lg-6').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.field.field-name-field-oggetto-bando').text.split('Oggetto:')[1]
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        est_amount = page_details.find_element(By.CSS_SELECTOR, 'div.field.field-name-field-importo-a-base-d-asta').text.split('€')[1]
        est_amount = re.sub("[^\d\.\,]", "", est_amount)
        notice_data.est_amount = est_amount.replace('.','').replace(',','.').strip()
        notice_data.est_amount = float(notice_data.est_amount)
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.CSS_SELECTOR, 'div.field.field-name-field-procedura-di-scelta-del-co').text.split(':')[1] 
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    
    try:
        p_date = page_details.find_element(By.CSS_SELECTOR, "div.field.field-name-field-data-di-pubblicazione-del-.field-type-datetime.field-label-inline.clearfix > div.field-items > div > span").text
        try:
            publish_date = GoogleTranslator(source='it', target='en').translate(p_date)
            publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                publish_date = re.findall('\d+ \w+ \d{4}',p_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                try:
                    publish_date = re.findall('\d+ \w+ \d{4}',p_date)[0]
                    notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    try:
                        publish_date = re.findall('\w+ \d+, \d{4}',p_date)[0]
                        notice_data.publish_date = datetime.strptime(publish_date,'%b %d, %Y').strftime('%Y/%m/%d %H:%M:%S') 
                    except Exception as e:
                        logging.info("Exception in publish_date: {}".format(type(e).__name__))
                        pass
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
        

 
    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'div.field.field-name-field-cig-smart-cig').text.split(':')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.post_content'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'IT'

            customer_details_data.org_name = single_record.find_element(By.CSS_SELECTOR, 'div.field.field-name-field-stazione-appaltante').text.split(':')[1]
            
            try:
                customer_details_data.contact_person = single_record.find_element(By.CSS_SELECTOR, 'div.field.field-name-field-rup').text.split(':')[1]
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        lot_number = 1
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'tr > td:nth-child(1)'):
            lot_details_data = lot_details()
            lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(1)').text    
            lot_details_data.lot_title_english =  GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            lot_details_data.lot_number = lot_number
            lot_details_data.contract_type = notice_data.notice_contract_type
            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#main > div > div'):        
                    if 'Affidamento diretto' in notice_data.local_title:
                        award_details_data = award_details()
                        notice_data.notice_type = 7
        
                        award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'div.field.field-name-field-aggiudicatario').text.split(':')[1] 
        
                        try:
                            final_estimated_value = single_record.find_element(By.CSS_SELECTOR, 'div.field.field-name-field-importo-di-aggiudicazione').text.split('€')[1]
                            final_estimated_value = re.sub("[^\d\.\,]", "", final_estimated_value)
                            award_details_data.final_estimated_value = float(final_estimated_value.replace('.','').replace(',','.').strip())
        
                        except Exception as e:
                            logging.info("Exception in final_estimated_value: {}".format(type(e).__name__))
                            pass
                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[@id="main"]/div/div'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div.field-items > div > span > a').text
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'div.field-items > div > span > a').get_attribute('href')
                

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    if notice_data.publish_date is None:
        try:
            publish_date =  attachments_data.file_name
            publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass    
 
    try:
        notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'div.field.field-name-field-link  > div > div > a').text    
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.aric.it/bandi-gara-aperti?order=field_tipo_di_appalto&sort=asc'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="block-system-main"]/div/div/div[1]/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="block-system-main"]/div/div/div[1]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="block-system-main"]/div/div/div[1]/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="block-system-main"]/div/div/div[1]/div/table/tbody/tr'),page_check))
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
