#refer this page detail url for fields "https://centraledesmarches.com/marches-publics/Douai-cedex-Commune-de-Douai-Accords-cadres-de-maintenance-d-espaces-verts/6838902"
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_cenedesmarch_spn"
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
SCRIPT_NAME = "fr_cenedesmarch_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'fr_cenedesmarch_spn'
    notice_data.main_language = 'FR'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    
    notice_data.notice_type = 4

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col > h2').text
        notice_data.notice_title = GoogleTranslator(source='fr', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.rounded.p-3.mt-3 > div:nth-child(1)').text.split(':')[1].strip()
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    try:
        procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, 'div.rounded.p-3.mt-3 > div:nth-child(2)').text.split(':')[1].split('\n')[0].strip()
        if "National" in procurement_method:
            notice_data.procurement_method = 0
        else:
            notice_data.procurement_method = 2
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass    
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.rounded.p-3.mt-3 > div:nth-child(3)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, "div.rounded.p-3.mt-3 > div  > div:nth-child(1)").text.split(':')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.card-body > div:nth-child(2)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.text-center.mt-3> a').get_attribute("href")
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
        
    try:
        fn.load_page(page_details,notice_data.notice_url,80)
    
        try:
            notice_data.notice_text += page_details.find_element(By.XPATH, '//div[@class="card annonce mt-3 shadow-sm"]').get_attribute("outerHTML")                     
        except:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass
        try:
            data_text = page_details.find_element(By.XPATH, '''//*[@class='p-3 mt-3']''').text
        except:
            pass
         
        try:
            contract_duration = ['Durée des marchés :','Durée du marché :']
            for i in contract_duration:
                if i in data_text:
                    notice_data.contract_duration = data_text.split(i)[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass
        
        try: 
            local_description_start = page_details.find_element(By.XPATH, '''//*[contains(text(),'Objet')]/.|//*[contains(text(),'Description')]/.''').text
            local_description_end = page_details.find_element(By.XPATH, '''//*[contains(text(),'Objet')]/following-sibling::strong[1]|//*[contains(text(),'Description')]/following-sibling::strong[1]''').text
            notice_data.local_description = data_text.split(local_description_start)[1].split(local_description_end)[0].strip()
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass
                                             
        try:              
            customer_details_data = customer_details()

            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > div:nth-child(3)').text.split(':')[1].strip()
            
            try:
                contact_person = fn.get_after(data_text.lower(),'nom du contact',60)
                if 'adresse mail du contact' in contact_person:
                    try:
                        customer_details_data.contact_person = contact_person.split(':')[1].split('adresse mail du contact')[0].strip()
                    except:
                        contact_person = data_text.lower().split('nom du contact')[1].split('adresse mail du contact')[0].strip()
                        customer_details_data.contact_person = contact_person.split(':')[1].strip()
                else:
                    contact_person = data_text.lower().split('nom du contact')[1].split('\n')[0].strip() 
                    customer_details_data.contact_person = contact_person.split(':')[1].strip()
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
            
            try:  
                postal_code = re.search('code postal(.)+\d{5}',data_text.lower())
                code_postal = postal_code.group()
                customer_details_data.postal_code = re.findall('\d{5}',code_postal)[0]
            except:
                try:  
                    postal_code = page_details.find_element(By.XPATH, '''//*[contains(text(),'Code postal')]''').text
                    if postal_code in data_text:  # \b\d{5}\b
                        postal_code1 = data_text.split(postal_code)[1].split('\n')[0].strip()
                        customer_details_data.postal_code = re.findall('\b\d{5}\b',postal_code1)[0]
                except Exception as e:
                    logging.info("Exception in postal_code: {}".format(type(e).__name__))
                    pass

            try:  
                customer_details_data.org_phone = page_details.find_element(By.XPATH, "(//*[contains(text(),'Tel')])[1]").text.split(':')[1].strip()
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
            try:
                org_address = page_details.find_element(By.XPATH, '''//*[@class="mt-3"]/div[2]''').text
                if re.search("\d{5}.\w+",org_address):
                    customer_details_data.org_address = org_address
                else:
                    customer_details_data.org_address = page_details.find_element(By.XPATH, '''//*[@class="mt-3"]/div[1]''').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

            try:
                org_email = page_details.find_element(By.XPATH, '''//*[contains(text(),'Adresse mail du ')]/.''').text
                customer_details_data.org_email = data_text.split(org_email)[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            customer_details_data.org_language = 'FR'
            customer_details_data.org_country = 'FR'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        
        notice_data.class_at_source = 'CPV'
        try: 
            cpv_at_source = ''

            data_text_lower = data_text.lower().replace('(','').replace(')','')
            for each_cpv in data_text_lower.split('cpv')[1:]:
                cpv_code1 = each_cpv
                if re.search("\d{8}", cpv_code1):
                    regex = re.findall(r'\b\d{8}\b',cpv_code1)
                    for each_cpv in regex:
                        cpvs_data = cpvs()
                        try:
                            cpvs_data.cpv_code = each_cpv
                            cpv_at_source += cpv_code
                            cpv_at_source += ','
                        except:
                            pass

                        cpvs_data.cpvs_cleanup()
                        notice_data.cpvs.append(cpvs_data)
            notice_data.cpv_at_source = cpv_at_source.rstrip(',')
            notice_data.class_codes_at_source = notice_data.cpv_at_source

        except Exception as e:
            logging.info("Exception in load_page: {}".format(type(e).__name__)) 
            pass
        
        try:
            data = ["Type de marché : travaux","Type de marché : Services","Type de marché : Fournitures"]
            for i in data:
                if i in data_text:
                    notice_data.contract_type_actual = i.split(":")[1].strip()
                    if "Services" in notice_data.contract_type_actual:
                        notice_data.notice_contract_type = "Service"
                    elif "travaux" in notice_data.contract_type_actual:
                        notice_data.notice_contract_type = "Works"
                    elif "Fournitures" in notice_data.contract_type_actual:
                        notice_data.notice_contract_type = "Supply"
                    else:
                        pass
        except Exception as e:
            logging.info("Exception in contract_type_actual: {}".format(type(e).__name__)) 
            pass
        
        try:
            notice_data.additional_tender_url= data_text.split('Adresse internet :')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in additional_tender_url: {}".format(type(e).__name__)) 
            pass
            
        try:
            est_amount = data_text.split('Valeur estimée hors TVA')[1].split('\n')[0].strip()
            est_amount = re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount = float(est_amount.replace(' ','').strip())
            notice_data.netbudgetlc = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass
        
        try:
            lst = ["Date denvoi du présent avis :"]
            for i in lst:   # March 5, 2024.
                if i in data_text:
                    dispatch_date = data_text.split(i)[1].split('\n')[0].strip()
                    dispatch_date_en = GoogleTranslator(source='auto', target='en').translate(dispatch_date)
                    try:
                        dispatch_date = re.findall('\w+ \d+, \d{4}',dispatch_date_en)[0]
                        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%B %m, %Y').strftime('%Y/%m/%d')
                    except:
                        pass
                            
        except Exception as e:
            logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
            pass
        
    except Exception as e:
        logging.info("Exception in load_page: {}".format(type(e).__name__))
        notice_data.notice_url = url

    
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

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://centraledesmarches.com/marches-publics?avisType=1&publicationType=1'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(1,50):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@class="card annonce mt-3 shadow-sm collapse show"]'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@class="card annonce mt-3 shadow-sm collapse show"]')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@class="card annonce mt-3 shadow-sm collapse show"]')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//i[@class="fas fa-angle-right"])[2]')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@class="card annonce mt-3 shadow-sm collapse show"]'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
    