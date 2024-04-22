from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_start_ca"
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
SCRIPT_NAME = "it_start_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_start_ca'
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    notice_data.notice_type = 7
    notice_data.procurement_method = 2
    notice_data.class_at_source = 'CPV'
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,180)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, "(//dt[contains('Cig:,CIG:,CIG/SMART CIG:',text())])[3]//following::dd[1]").text
    except:
        notice_data.notice_no = notice_data.notice_url.split('id/')[1].split('/idL')[0]
    notice_data.tender_id = notice_data.notice_no
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.related_tender_id = re.findall('\d+/\d+', notice_data.local_title)[0]
    except:
        pass   
    
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject > span.process-type').text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_start_ca_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.publishedAt").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#Contenuto').get_attribute("outerHTML")
        notice_text = page_details.find_element(By.CSS_SELECTOR, '#Contenuto').text
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '//*[@id="Contenuto"]/dl/dd[1]').text
        grossbudgetlc = re.sub("[^\d\.\,]", "", grossbudgetlc)
        notice_data.netbudgetlc = float(grossbudgetlc.replace('.','').replace(',','.').strip())
        notice_data.est_amount = notice_data.netbudgetlc
        notice_data.netbudgeteuro = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'span.organizationUnit').text.split('-')[0]
        
        try:
            customer_details_data.customer_main_activity = tender_html_element.find_element(By.CSS_SELECTOR, 'span.organizationUnit').text.split('-')[1].split('(')[0].strip()
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass        
        
        try:
            customer_details_data.org_address = notice_text.split('Stazione appaltante:')[1].split('\n')[1].split('Codice ')[0].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass  
        
        try:
            customer_details_data.org_phone = notice_text.split('Stazione appaltante:')[1].split('\n')[1].split('Codice fiscale:')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass  
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#Contenuto > div:nth-child(3)'):
            cpvs_data = cpvs()
            cpvs_data.cpv_code = single_record.find_element(By.CSS_SELECTOR, 'b').text.split('-')[0]
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_contract_type = page_details.find_element(By.CSS_SELECTOR, 'dl > dd:nth-child(7)').text
        notice_data.contract_type_actual = page_details.find_element(By.CSS_SELECTOR, 'dl > dd:nth-child(7)').text
        if 'Servizi' in notice_contract_type or 'Lavori' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Forniture' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Lavori pubblici' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        class_codes_at_source = ''
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#Contenuto > div:nth-child(3)'):
            class_codes_at_source += single_record.find_element(By.CSS_SELECTOR, 'b').text.split('-')[0]
            class_codes_at_source += ','
        notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')
        notice_data.cpv_at_source = notice_data.class_codes_at_source
        logging.info(notice_data.class_codes_at_source)
    except:
        pass
        
    try:
        lot_details_data = lot_details()  
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = notice_data.notice_title
        lot_details_data.contract_type = notice_data.notice_contract_type
        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
        lot_details_data.lot_number = 1
        try:
            count_bidder = WebDriverWait(page_details, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'td:nth-child(3) > ul > li')))
            bidder_count = len(count_bidder)
        except:
            pass
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'td:nth-child(3) > ul > li'):
            award_details_data = award_details()
            award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'span.name').text
            try:
                award_details_data.address = single_record.text
            except Exception as e:
                logging.info("Exception in address: {}".format(type(e).__name__))
                pass
            
            try:
                netawardvaluelc1 = page_details.find_element(By.CSS_SELECTOR, '#list-contractors td:nth-child(4)').text.split('(')[0].strip()
                netawardvaluelc2 = re.sub("[^\d\.\,]", "", netawardvaluelc1)
                netawardvaluelc = float(netawardvaluelc2.replace('.','').replace(',','.').strip())
                award_details_data.netawardvaluelc = (netawardvaluelc//int(bidder_count))
                if '€' in netawardvaluelc1:
                    award_details_data.netawardvalueeuro = award_details_data.netawardvaluelc
            except Exception as e:
                logging.info("Exception in netawardvaluelc: {}".format(type(e).__name__))
                pass

            try:
                award_date = page_details.find_element(By.CSS_SELECTOR, '#list-contractors td:nth-child(5)').text
                award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                lot_details_data.lot_award_date = award_details_data.award_date
            except Exception as e:
                logging.info("Exception in award_date: {}".format(type(e).__name__))
                pass
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        if lot_details_data.award_details != []:
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details : {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# # ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    keywords = ['B0889C310B','A03E3E7909','B0C95B222E','B0C959E1AD','B0C9582A8F','B0C946C527','B0C9467108','201067%Con','A0416B01CF','B0EEA801E0','B076149806']
        
    for keyword in keywords:
        url = 'https://start.toscana.it/awards/list-public?recordNumber=10&keywords='+str(keyword)+'&advancedSearch=&submitButton=Cerca'
        fn.load_page(page_main, url, 150)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            page_check = WebDriverWait(page_main, 150).until(EC.presence_of_element_located((By.XPATH,'//*[@id="AwardsController-list"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="AwardsController-list"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="AwardsController-list"]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
        except:
            logging.info(keyword)
            pass
                
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
