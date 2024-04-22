from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "br_governo"
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
SCRIPT_NAME = "br_governo"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'br_governo'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'BRL'
    
    notice_data.main_language = 'PT'
    
    notice_data.procurement_method = 2

    notice_data.notice_type = 4

    notice_data.document_type_description = 'CONSULTAR CONTRATOS E ADITIVOS'

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(10) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url

        
    try:
        grossbudgetlc  = page_details.find_element(By.XPATH, "//*[contains(text(),'Valor')]").text
        grossbudgetlc = re.sub("[^\d\.\,]", "", grossbudgetlc)  
        notice_data.grossbudgetlc = float(grossbudgetlc.replace('.','').replace(',','.').strip()) 
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, 'div > p').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)  
        logging.info(notice_data.notice_title)
    except Exception as e:
        logging.info("notice_data.notice_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.est_amount  = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass   
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.body').get_attribute("outerHTML")    
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()

        try:
            org_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Contratante')]").text 
            customer_details_data.org_name = org_name.split('Contratante: ')[1]   
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

        try:
            contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Contratada')]").text 
            customer_details_data.contact_person  = contact_person.split('Contratada(o):')[1] 
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'BR'
        customer_details_data.org_language = 'PT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        lot_number = 1
        page_details.find_element(By.CSS_SELECTOR, ' div.body > div:nth-child(2) > div:nth-child(2) > table > tbody > tr')
        for single_record in page_details.find_elements(By.CSS_SELECTOR, ' div.body > div:nth-child(2) > div:nth-child(2) > table > tbody > tr'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text

            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)  


            try:
                lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                lot_grossbudget_lc = re.sub("[^\d\.\,]", "", lot_grossbudget_lc) 
                lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace('.','').replace(',','.').strip()) 
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
            
            try:
                lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text 
                lot_quantity = lot_quantity.replace(',','.')
                lot_details_data.lot_quantity = float(lot_quantity)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass


            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text  
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1

    except:

        try:
            page_details1_url = page_details.find_element(By.CSS_SELECTOR, ' div.body > div:nth-child(3) > div:nth-child(2) > div > div.pmbb-body.p-l-30 > div > dl > a').get_attribute("href") 
            fn.load_page(page_details1,page_details1_url,80)


            notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, 'div.body').get_attribute("outerHTML") 
            
            try:
                grossbudgetlc  = page_details1.find_element(By.XPATH, "//*[contains(text(),'Valor')]").text
                grossbudgetlc = re.sub("[^\d\.\,]", "", grossbudgetlc)  
                notice_data.grossbudgetlc = float(grossbudgetlc.replace('.','').replace(',','.').strip()) 
            except Exception as e:
                logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
                pass
            
            try:
                notice_data.est_amount  = notice_data.grossbudgetlc
            except Exception as e:
                logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
                pass   
            
            
            lot_number = 1
            for single_record in page_details1.find_elements(By.CSS_SELECTOR, ' div.body > div:nth-child(2) > div:nth-child(2) > table > tbody > tr'):
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text

                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)  


                try:
                    lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                    lot_grossbudget_lc = re.sub("[^\d\.\,]", "", lot_grossbudget_lc) 
                    lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace('.','').replace(',','.').strip()) 
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text 
                    lot_quantity = lot_quantity.replace(',','.')
                    lot_details_data.lot_quantity = float(lot_quantity)
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text  
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['http://www.governotransparente.com.br/acessoinfo/12059489/consultarcontratoaditivo?ano=11&credor=-1&page=1&datainfo=%22MTIwMjMwNjA1MDUzOFBQUA==%22&inicio=05/05/2023&fim=05/06/2023&unid=&valormax=&valormin='] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="data-table"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="data-table"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="data-table"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.body.table-responsive.w-100.pt-0 > div.pagination > a.next')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="data-table"]/tbody/tr'),page_check))
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

    
