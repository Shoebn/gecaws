from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_unibas_ca"
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
SCRIPT_NAME = "it_unibas_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_unibas_ca'
    notice_data.main_language = 'IT'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7

    try:
        notice_data.document_type_description = page_main.find_element(By.CSS_SELECTOR, 'div > section > h3 > span').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_summary_english = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4) > div").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.review36').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        notice_text  = page_details.find_element(By.CSS_SELECTOR, 'div.review36').text
        if 'Procedura di scelta del contraente:' in notice_text:
            notice_data.type_of_procedure_actual = notice_text.split("Procedura di scelta del contraente: ")[1].split("\n")[0].strip()  
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.type_of_procedure = fn.procedure_mapping('assets/it_unibas_procedure.csv',notice_data.type_of_procedure_actual)   
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_url_1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > div > a').get_attribute("href")                     
        fn.load_page(page_details1,notice_url_1,80)
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div.review36'):
            customer_details_data = customer_details()
            customer_details_data.org_name = 'Università degli Studi della Basilicata'
            customer_details_data.org_parent_id = 7798037
            customer_details_data.org_country = 'IT'
            customer_details_data.org_language = 'IT'

            try:
                customer_details_data.org_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in org_description: {}".format(type(e).__name__))
                pass


            try:
                org_address = single_record.find_element(By.XPATH, "//*[contains(text(),'Indirizzo:')]").text
                customer_details_data.org_address = org_address.split('Indirizzo:')[1].strip()
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

            try:
                org_phone = single_record.find_element(By.XPATH, "//*[contains(text(),'Telefono:')]").text
                customer_details_data.org_phone = org_phone.split('Telefono:')[1].strip()
            except Exception as e:  
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass


            try:
                customer_details_data.org_email = single_record.find_element(By.XPATH, "//*[contains(text(),'Email:')]//following::a[1]").text 
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass


            try:
                customer_details_data.contact_person = single_record.find_element(By.XPATH, "//*[contains(text(),'Responsabile:')]//following::a[1]").text 
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except:
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Università degli Studi della Basilicata'
        customer_details_data.org_parent_id = 7798037
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    
    try:
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        try:
            lot_details_data.lot_title = notice_data.notice_title
            notice_data.is_lot_default = True
        except Exception as e:
            logging.info("Exception in lot_title: {}".format(type(e).__name__))
            pass

        try:
            lot_details_data.lot_description = notice_data.notice_title
        except Exception as e:
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass

        try:
            lot_grossbudget_lc = single_record.text
            if 'Importo delle somme liquidate' in lot_grossbudget_lc:
                lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'div > div > div:nth-child(14)').text 
                lot_grossbudget_lc  = lot_grossbudget_lc.split(': € ')[1]
                lot_grossbudget_lc =  lot_grossbudget_lc.replace('.','').replace(',','.').strip() 
                lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
                notice_data.grossbudgetlc=lot_details_data.lot_grossbudget_lc 
            else:
                pass

        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass
        try:
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.review36'):
                award_details_data = award_details()

                try:
                    bidder_name = single_record.text 
                    if 'Aggiudicatari' in bidder_name:
                        award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'ul:nth-child(9) > li').text  
                    else:
                        pass
                except Exception as e:
                    logging.info("Exception in bidder_name: {}".format(type(e).__name__))
                    pass

                try:
                    grossawardvaluelc = single_record.text 
                    if 'Importo di aggiudicazione: ' in grossawardvaluelc:
                        grossawardvaluelc = single_record.find_element(By.CSS_SELECTOR, '#reviewOggetto > div > div > div.campoOggetto').text  
                        grossawardvaluelc  = grossawardvaluelc.split(': € ')[1]
                        grossawardvaluelc =  grossawardvaluelc.replace('.','').replace(',','.').strip() 
                        award_details_data.grossawardvaluelc = float(grossawardvaluelc)

                except Exception as e:
                    logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                    pass
                
                try:
                    award_details_data.initial_estimated_value = lot_details_data.lot_grossbudget_lc
                except Exception as e:
                    logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                    pass
                

                try:
                    award_date = single_record.text
                    if 'Data di ultimazione dei lavori o forniture:' in award_date:
                        award_date = page_details.find_element(By.XPATH, "//*[contains(text(),'lavori o forniture:')]//following::div[1]").text 
                        award_date = re.findall('\d+-\d+-\d{4}',award_date)[0]
                        award_details_data.award_date  = datetime.strptime(award_date,'%d-%m-%Y').strftime('%Y/%m/%d')
                except Exception as e:
                    logging.info("Exception in award_date: {}".format(type(e).__name__))
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.campoOggetto48'):
            attachments_data = attachments()
        
            try:
                file_name = page_details.find_element(By.CSS_SELECTOR, 'div.campoOggetto48').text
                attachments_data.file_name = file_name.split(': ')[0]  
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass        
            
            
            try:
                file_description = page_details.find_element(By.CSS_SELECTOR, 'div.campoOggetto48').text
                attachments_data.file_description = file_name.split('.pdf')[0] 
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass                    
            
            
                  

            try:
                attachments_data.file_type = file_name
                if '.pdf' in attachments_data.file_type:
                    attachments_data.file_type = 'pdf'
                elif 'xlsx' in attachments_data.file_type:
                    attachments_data.file_type  = 'xlsx'
                elif 'doc' in attachments_data.file_type:
                    attachments_data.file_type = 'xlsx'
                elif 'zip' in attachments_data.file_type:
                    attachments_data.file_type = 'zip'
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        

            try:
                file_size = page_details.find_element(By.CSS_SELECTOR, 'div.campoOggetto48 > span').text
                file_size = file_size.split(' - ')[2].split(' - ')[0] 
                file_size = file_size.split(' kb')[0].strip('')
                attachments_data.file_size = float(file_size)
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        

            try:
                attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div.campoOggetto48 > a').get_attribute('href') 
            except Exception as e:
                logging.info("Exception in external_url: {}".format(type(e).__name__))
                pass
        
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://unibas.etrasparenza.it/index.php?id_sezione=876&id_cat=0'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[4]/div/main/div/div/div/div[2]/div/div/div[2]/div[2]/div/section/div[2]/table/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[4]/div/main/div/div/div/div[2]/div/div/div[2]/div[2]/div/section/div[2]/table/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[4]/div/main/div/div/div/div[2]/div/div/div[2]/div[2]/div/section/div[2]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'>successiva')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div[4]/div/main/div/div/div/div[2]/div/div/div[2]/div[2]/div/section/div[2]/table/tbody/tr[2]'),page_check))   
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
    page_details1.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
    
