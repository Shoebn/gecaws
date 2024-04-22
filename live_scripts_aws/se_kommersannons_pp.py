from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "se_kommersannons_pp"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from deep_translator import GoogleTranslator
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "se_kommersannons_pp"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'se_kommersannons_pp'
    
    notice_data.main_language = 'SV'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'SE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
  
    notice_data.currency = 'SEK'
        
    notice_data.notice_type = 3
    
    notice_data.class_at_source = 'CPV'
    
    try:                                                                                                                      
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' div> div.col-md-8.text-break > h4').text.strip().split('- ')[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no1: {}".format(type(e).__name__))
        pass
    
    try:
        local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' div> div.col-md-8.text-break > h4').text.split(notice_data.notice_no)[1].strip()
        if '-' in local_title:
            notice_data.local_title = local_title.replace('-',' ').strip()
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)

    except:
        local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' div> div.col-md-8.text-break > h4').text
        if '-' in local_title:
            notice_data.local_title = local_title.replace('-',' ').strip()
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    if len(notice_data.local_title) < 5:
        return
    if len(notice_data.notice_title) < 5:
        return
            
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, ' div > div.col-md-8.text-break > div:nth-child(2)').text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    try: 
        dispatch_date = tender_html_element.find_element(By.CSS_SELECTOR, ' div > div.col-md-8.text-break > div:nth-child(2)').text
        dispatch_date = re.findall('\d{4}-\d+-\d+',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.dispatch_date)
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div> div.col-md-8.text-break > h4 > a').get_attribute("href")
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        pass

    try:
        fn.load_page(page_details,notice_data.notice_url,90)
        logging.info(notice_data.notice_url)

        WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div > main > div')))

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div > main > div').get_attribute("outerHTML")                     
        except:
            pass

        try:
            if notice_data.notice_no == '':
                notice_data.notice_no = notice_data.notice_url.split('/')[-1].strip()
        except Exception as e:
            logging.info("Exception in notice_no2: {}".format(type(e).__name__)) 
            pass 

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'SE'
            customer_details_data.org_language = 'SV'

            customer_details_data.org_name =  page_details.find_element(By.XPATH, '//*[contains(text(),"Officellt namn")]//following::div[1]').text

            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Huvudsaklig verksamhet")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__)) 
                pass 

            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Typ av upphandlande myndighet eller enhet")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__)) 
                pass 

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefon")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__)) 
                pass

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-postadress")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__)) 
                pass

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"Plats för utförande (NUTS-kod)")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__)) 
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass 

        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Beskrivning")]//following::div[1]').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__)) 
            pass 

        try:
            notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Typ av kontrakt")]//following::div[1]').text
            if 'Tjänster' in  notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Service' 
            elif 'Varor' in  notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Supply'
            elif 'Byggentreprenader' in  notice_data.contract_type_actual or 'Entrepenad' in  notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Works'
        except Exception as e:
            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
            pass

        try:
            cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Huvudsaklig CPV-kod")]//following::div[1]').text
            cpv_code_title = re.split("\d{8}-\d+", cpv_code)
            class_title_at_source = ''
            for cpv_title in cpv_code_title[1:]:

                class_title_at_source += cpv_title.strip()
                class_title_at_source += ','
            notice_data.class_title_at_source = class_title_at_source.rstrip(',')
        except Exception as e:
            logging.info("Exception in class_title_at_source1: {}".format(type(e).__name__)) 
            pass

        try:  
            class_codes_at_source = ''
            cpv_at_source = ''
            code_data = page_details.find_element(By.XPATH, '//*[contains(text(),"Huvudsaklig CPV-kod")]//following::div[1]').text
            cpv_regex = re.compile(r'\d{8}')
            cpv_code_list = cpv_regex.findall(code_data)
            for cpv in cpv_code_list:
                cpvs_data = cpvs()

                class_codes_at_source += cpv
                class_codes_at_source += ','

                cpv_at_source += cpv
                cpv_at_source += ','

                cpvs_data.cpv_code = cpv

                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)

            notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')

            notice_data.cpv_at_source = cpv_at_source.rstrip(',')        
        except Exception as e:
            logging.info("Exception in cpvs1: {}".format(type(e).__name__)) 
            pass

        try:
            cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Ytterligare CPV-koder")]//following::div[1]').text
            cpv_code_title = re.split("\d{8}-\d+ -", cpv_code)
            class_title_at_source = ''
            for cpv_title in cpv_code_title[1:]:

                class_title_at_source += cpv_title.strip()
                class_title_at_source += ','
            notice_data.class_title_at_source = class_title_at_source.rstrip(',')
        except Exception as e:
            logging.info("Exception in class_title_at_source2: {}".format(type(e).__name__)) 
            pass

        try:  
            class_codes_at_source = ''
            cpv_at_source = ''
            code_data = page_details.find_element(By.XPATH, '//*[contains(text(),"Ytterligare CPV-koder")]//following::div[1]').text
            cpv_regex = re.compile(r'\d{8}')
            cpv_code_list = cpv_regex.findall(code_data)
            for cpv in cpv_code_list:
                cpvs_data = cpvs()

                class_codes_at_source += cpv
                class_codes_at_source += ','

                cpv_at_source += cpv
                cpv_at_source += ','

                cpvs_data.cpv_code = cpv

                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)

            notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')

            notice_data.cpv_at_source = cpv_at_source.rstrip(',')           
        except Exception as e:
            logging.info("Exception in cpvs2: {}".format(type(e).__name__)) 
            pass

        try:
            est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Uppskattat värde")]//following::div[1]').text
            est_amount = re.sub("[^\d\.\,]", "",est_amount)
            notice_data.est_amount = float(est_amount.replace(',','.').strip())
            notice_data.netbudgetlc = notice_data.est_amount
        except Exception as e: 
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass 

        try:
            tender_contract_start_date = page_details.find_element(By.XPATH, '''//*[contains(text(),"Avtalsperiodens start")]//following::div[1]''').text
            tender_contract_start_date = re.findall('\d{4}-\d+-\d+',tender_contract_start_date)[0]
            notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
            pass

        try:
            tender_contract_end_date = page_details.find_element(By.XPATH, '''//*[contains(text(),"Avtalsperiodens slut")]//following::div[1]''').text
            tender_contract_end_date = re.findall('\d{4}-\d+-\d+',tender_contract_end_date)[0]
            notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
            pass

        try:
            notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Typ av förfarande")]//following::div[1]').text
            type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
            notice_data.type_of_procedure = fn.procedure_mapping("assets/se_kommersannons_category.csv",type_of_procedure_actual)
        except Exception as e:
            logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
            pass
        
    except Exception as e:
        logging.info("Exception in page_details: {}".format(type(e).__name__))
        pass
                 
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver_head(arguments)
page_details = fn.init_chrome_driver_head(arguments)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    
    urls = ["https://www.kommersannons.se/Notices/PriorInfoNotices"] 
    for url in urls:
        fn.load_page(page_main, url, 60)
        fn.load_page(page_details, url, 60)
        logging.info('----------------------------------')
        logging.info(url) 
        
        click_language = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#navbarLanguages')))
        page_main.execute_script("arguments[0].click();",click_language) 
        time.sleep(5)
        
        select_svenska = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#Language > li > div.dropdown-menu.dropdown-menu-right.show > a.dropdown-item.no-active')))
        page_main.execute_script("arguments[0].click();",select_svenska) 
        time.sleep(5)
        
        click_language = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#navbarLanguages')))
        page_details.execute_script("arguments[0].click();",click_language) 
        time.sleep(5)
        
        select_svenska = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#Language > li > div.dropdown-menu.dropdown-menu-right.show > a.dropdown-item.no-active')))
        page_details.execute_script("arguments[0].click();",select_svenska) 
        time.sleep(5)

        select_btn = Select(page_main.find_element(By.CSS_SELECTOR,'#NameSort'))
        select_btn.select_by_index(2)
        time.sleep(5)
    
        click_sorting = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#SortAscending')))
        page_main.execute_script("arguments[0].click();",click_sorting)
        time.sleep(5)
        
        try:
            for page_no in range(1,4):
                page_check = WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/main/div[3]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/main/div[3]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/main/div[3]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                try:   
                    next_page = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.col-sm-4.col-4.text-left.p-0 > form > button')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 60).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div/main/div[3]/div'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
