from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_trieste"
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
SCRIPT_NAME = "it_trieste"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_trieste'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
   
    notice_data.document_type_description = "Avvisi e bandi di gara - Profilo di committente"

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_no.startswith("Z") or 'Partecipanti' in notice_data.notice_text or 'Aggiudicatari' in notice_data.notice_text:
        notice_data.notice_type = 7
    elif 'MANIFESTAZIONE DI INTERESSE' in notice_data.local_title:
        notice_data.notice_type = 5
    else:
        notice_data.notice_type = 4
 
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
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
        notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Data di Scadenza:")]').text
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importo dell")]').text
        grossbudgetlc = re.sub("[^\d\.\,]","",grossbudgetlc)
        notice_data.grossbudgetlc =float(grossbudgetlc.replace(',','.').replace('.','').strip())                                          
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.est_amount = notice_data.grossbudgetlc 
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        notice_text  = page_details.find_element(By.CSS_SELECTOR, 'div.review36').text
        notice_data.type_of_procedure_actual = notice_text.split("Procedura di scelta del contraente:")[1].split("\n")[0].strip()
        notice_data.type_of_procedure = fn.procedure_mapping('assets/it_trieste.csv',notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass   
 
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Autorità di Sistema Portuale del Mare Adriatico Orientale'
        customer_details_data.org_parent_id = '7645486'
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
     
        try:
            customer_details_data.org_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        except Exception as e:
            logging.info("Exception in org_description: {}".format(type(e).__name__))
            pass       
 
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, "//*[contains(text(),'Struttura proponente')]").text.split("Struttura proponente:")[1]
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass    
            
        try:
            url1= page_details.find_element(By.CSS_SELECTOR, '  #reviewOggetto > div > div > div:nth-child(n) > a').get_attribute("href")                     
            fn.load_page(page_details1,url1,80)
        except:
            pass
        
        try:
            notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, '#partecentrale > div.container.container-nav-1 > div > div').get_attribute("outerHTML")
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass
    
        try:
            customer_details_data.contact_person = page_details1.find_element(By.XPATH, "//*[contains(text(),'Responsabile:')]").text.split("Responsabile: ")[1]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        try:
            url2= page_details1.find_element(By.CSS_SELECTOR, '  #reviewOggetto > div > div > div.campoOggetto78 > a').get_attribute("href")                     
            fn.load_page(page_details2,url2,80)
        except:
            pass
        
        try:
            notice_data.notice_text += page_details2.find_element(By.CSS_SELECTOR, '#partecentrale > div.container.container-nav-1 > div > div').get_attribute("outerHTML")
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass
    
        try:
            customer_details_data.org_phone = page_details2.find_element(By.XPATH, "//*[contains(text(),'Telefono')]").text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
 
        try:
            customer_details_data.org_email = page_details2.find_element(By.XPATH, "//*[contains(text(),'Email: ')]").text.split("Email: ")[1]
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
 
    try:
        bidder_name = page_details.find_element(By.CSS_SELECTOR, 'ul:nth-child(9) > li').text
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = notice_data.notice_title

        try:
            lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importo dell")]').text
            lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
            lot_details_data.lot_grossbudget_lc =float(lot_grossbudget_lc.replace(',','.').replace('.','').strip())
        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass

        try:
            award_details_data = award_details()

            award_details_data.bidder_name = bidder_name
            
            try:
                award_details_data.initial_estimated_value = lot_details_data.lot_grossbudget_lc 
            except Exception as e:
                logging.info("Exception in initial_estimated_value: {}".format(type(e).__name__))
                pass

            try:
                grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importo di aggiudicazione")]').text
                grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                award_details_data.grossawardvaluelc =float(grossawardvaluelc.replace(',','.').replace('.','').strip())
            except Exception as e:
                logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                pass

            try:
                award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Data di ultimazione dei lavori o forniture")]').text
                award_date = re.findall('\d+-\d+-\d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d-%m-%Y').strftime('%Y/%m/%d') 
                lot_details_data.lot_award_date=award_details_data.award_date
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.campoOggetto48 '):
            attachments_data = attachments()
            
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' a').get_attribute('href')
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
            
            try:   
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'a').text.split(".")[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            
            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'span').text.split("-")[-2]
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
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
page_details2 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    
    for page_no in range(0,80,20):
        url='https://trasparenza.porto.trieste.it/index.php?id_doc=0&id_cat=&id_oggetto=0&id_sezione=876&senso=cre&ordine=data_creazione&id_cat=&inizio='+str(page_no)+'&limite=20&esattamente=&gtp=1&id_cat=&id_criterio=&id_doc=&id_ente=364&id_oggetto=&id_sez_ori=&id_sezione=876&id_sond=&limite=20&ordina_oggetto=&ordine=data_creazione&purecontent=&senso=cre&template_ori=&gtp=1'
    
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[4]/div/main/div/div/div/div[2]/div/div/div[2]/div[2]/div/section/div[2]/table/tbody/tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[4]/div/main/div/div/div/div[2]/div/div/div[2]/div[2]/div/section/div[2]/table/tbody/tr')))[records]
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
    
