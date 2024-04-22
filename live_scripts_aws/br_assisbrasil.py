from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "br_assisbrasil"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
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
SCRIPT_NAME = "br_assisbrasil"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'br_assisbrasil'
    
    notice_data.main_language = 'PT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'BRL'
    
    notice_data.procurement_method = 2
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        time.sleep(5)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div > article').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_no = page_details.find_element(By.CSS_SELECTOR, 'div._12vNY > section:nth-child(2) > div:nth-child(1)').text
        if "N° " in notice_no:
            notice_data.notice_no=re.findall(r'N° \d+/\d+', notice_no)[0]
        else:
            try:
                notice_data.notice_no=re.findall(r'N°\d+/\d+', notice_no)[0]
            except:
                notice_data.notice_no = re.findall('\w+-\d+-\d{4}',notice_data.notice_url)[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
 
    try:
        notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, 'div._12vNY > section:nth-child(2) > div:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

  
    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div > div.CorePopover4063288344__root').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Situação/Status")]//following::div[1]').text
        if 'Andamento' in notice_type:
            notice_data.notice_type = 4
        elif 'Concluída' in notice_type or 'Revogada' in notice_type:
            notice_data.notice_type = 7
        elif 'Fracassada' in notice_type or 'Suspensa/Cancelada' in notice_type:
            notice_data.notice_type = 16
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    

    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "div.WncCi > p:nth-child(3)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is None:
        return

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    customer_details_data = customer_details()
    customer_details_data.org_name = 'prefeitura municipal de assis brasil'
    customer_details_data.org_parent_id = 7798082
    customer_details_data.org_country = 'BR'
    customer_details_data.org_language = 'PT'
    customer_details_data.org_email = 'prefeitura.assisbrasil.ac@gmail.com'
    customer_details_data.org_address = 'CNPJ 04.405.993/0001-79 ,R. Raimundo Chaar, 362 - Centro, CEP 69935-000, Assis Brasil, Acre'
    customer_details_data.org_phone = '(68) 3548 1208'
    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)

    
    try:              
        if notice_data.notice_type == 7:
            lot_details_data = lot_details()
            lot_details_data.lot_number = 1
            lot_details_data.lot_title = notice_data.notice_title
            notice_data.is_lot_default = True
            lot_details_data.lot_description = notice_data.notice_summary_english
            try:
                award_details_data = award_details()
            # Onsite Field -Data da Assinatura:
            # Onsite Comment -split award_date from "Data da Assinatura:"
                bidder_name = page_details.find_element(By.CSS_SELECTOR, 'div._3cRjW').text
                if 'CONTRATADO:' in bidder_name or 'CONTRATO:' in bidder_name:
                    award_details_data.bidder_name = bidder_name.split(':')[1].split('\n')[0].strip()

                    try:
                        grossawardvaluelc = page_details.find_element(By.CSS_SELECTOR, 'div._3cRjW').text
                        if 'VALOR' in grossawardvaluelc or 'Valor Total R$' in grossawardvaluelc:
                            grossawardvaluelc = grossawardvaluelc.split('R$')[1].split('\n')[0]
                            grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                            award_details_data.grossawardvaluelc =float(grossawardvaluelc.replace('.','').replace(',','.').strip())
                    except Exception as e:
                        logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                        pass

                    try:
                        award_date = page_details.find_element(By.CSS_SELECTOR, 'div._3cRjW').text.lower().split('assinatura')[1].split('\n')[0]
                        award_date = GoogleTranslator(source='auto', target='en').translate(award_date)
                        try:
                            award_date = re.findall('\w+ \d+, \d{4}',award_date)[0]
                            award_details_data.award_date = datetime.strptime(award_date,'%B %d, %Y').strftime('%Y/%m/%d')
                        except:
                            try:
                                award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]                  
                                award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                            except:
                                pass
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div._3EQWi.fggS-.cell'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.assisbrasil.ac.gov.br/licitacoes?page=1"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        clk=WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="comp-jp8mcxh3"]/div/div/div/div[2]/section/div/button')))
        page_main.execute_script("arguments[0].click();",clk)

        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ul.S4WbK_ > li')))
        length = len(rows)
        try:
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ul.S4WbK_ > li')))[records]
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
