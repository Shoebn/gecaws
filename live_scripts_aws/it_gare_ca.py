from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_gare_ca"
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
SCRIPT_NAME = "it_gare_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_gare_ca'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(2)').text.split("Titolo : ")[1]
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text
        if "Servizi" in notice_data.notice_contract_type:
            notice_data.notice_contract_type="Service"
        elif  "Lavori" in notice_data.notice_contract_type:
            notice_data.notice_contract_type="Works"
        elif  "forniture" in notice_data.notice_contract_type:
            notice_data.notice_contract_type="Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(4)').text.split(":")[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "form > div > div:nth-child(5)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(7)').text.split('Stato :')[1]
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML") 
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-action > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div > div > div > main').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'main > div > div'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'IT'
            customer_details_data.org_language = 'IT'
      
            customer_details_data.org_name = single_record.find_element(By.CSS_SELECTOR, 'div.detail-section.first-detail-section > div:nth-child(2)').text.split('Denominazione :')[1]
            
            try:
                customer_details_data.contact_person = single_record.find_element(By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div/div[3]/div[2]').text.split('Responsabile unico procedimento :')[1]
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        url1 = page_details.find_element(By.CSS_SELECTOR, ' div:nth-child(7) > ul > li > a').get_attribute("href")                     
        fn.load_page(page_details1,url1,80)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, '#ext-container > div > div > div > main').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'main > div > div'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = 1
            lot_details_data.lot_title = notice_data.local_title
            notice_data.is_lot_default = True
            lot_details_data.lot_title_english=notice_data.notice_title
            
            try:
                netbudgetlc  = single_record.find_element(By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div/div[2]/div[2]').text.split("Importo a base di gara : ")[1].split("€")[0]
                netbudgetlc = re.sub("[^\d\.\,]", "", netbudgetlc)
                notice_data.netbudgetlc =float(netbudgetlc.replace('.','').replace(',','.').strip())
                notice_data.netbudgeteuro = notice_data.netbudgetlc
            except Exception as e:
                logging.info("Exception in netbudgetlc : {}".format(type(e).__name__))
                pass
           
            try:
                lot_details_data.lot_grossbudget_lc =notice_data.netbudgetlc 
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass

            try:
                lot_award_date = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(6)').text
                lot_award_date = re.findall('\d+/\d+/\d{4}',lot_award_date)[0]
                lot_details_data.lot_award_date = datetime.strptime(lot_award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
            except Exception as e:
                logging.info("Exception in lot_award_date: {}".format(type(e).__name__))
                pass
            
            try:
                award_details_data = award_details()
                try:
                    award_details_data.bidder_name = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(4)').text.split('Ditta aggiudicataria :')[1]
                except Exception as e:
                    logging.info("Exception in bidder_name: {}".format(type(e).__name__))
                    pass
                
                if award_details_data.bidder_name == '' or award_details_data.bidder_name is None:
                    return

                try:
                    award_details_data.initial_estimated_value = lot_details_data.lot_grossbudget_lc
                except Exception as e:
                    logging.info("Exception in initial_estimated_value: {}".format(type(e).__name__))
                    pass
         
                try:
                    netawardvaluelc = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(5)').text.split("Importo aggiudicazione : ")[1].split("€")[0]
                    netawardvaluelc = re.sub("[^\d\.\,]", "", netawardvaluelc)
                    award_details_data.netawardvaluelc =float(netawardvaluelc.replace('.','').replace(',','.').strip())
                    award_details_data.netawardvalueeuro = award_details_data.netawardvaluelc
                except Exception as e:
                    logging.info("Exception in netawardvaluelc: {}".format(type(e).__name__))
                    pass  
         
                try:
                    award_date = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(6)').text
                    award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                    award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
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
        
    try:
        notice_data.est_amount=notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))        
    
    try:
        url2 = page_details.find_element(By.CSS_SELECTOR, ' div:nth-child(8) > ul > li > a').get_attribute("href")                     
        fn.load_page(page_details2,url2,80)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details2.find_element(By.CSS_SELECTOR, '#ext-container > div > div > div > main').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:              
        for single_record in page_details2.find_elements(By.CSS_SELECTOR, ' div.detail-section > div > ul > li '):
            attachments_data = attachments()
            attachments_data.file_type = 'PDF'
       
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' a').get_attribute('href')
            
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
    urls = ["https://gare.comunecatanzaro.it/PortaleAppalti/it/ppgare_esiti_lista.wp;jsessionid=149AB4B731AD2400DEA358D3EDF6886A?_csrf=IYCZ2MP9KBJFIE2CCDHBSWG90PZ1K8IP"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        url1 = page_main.find_element(By.CSS_SELECTOR, ' div:nth-child(5) > div:nth-child(3) > ul > li:nth-child(5) > span > a').get_attribute("href")                     
        fn.load_page(page_main,url1,50)
        
        try:
            for page_no in range(1,20):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.list-item'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.list-item')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.list-item')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="pagination-navi"]/input[8]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.list-item'),page_check))
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
    page_details1.quit()
    page_details2.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
