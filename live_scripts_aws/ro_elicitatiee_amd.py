 #NOTE- USE VPN... Select "DATA PUBLICARE" >>>> select previous and current date >>>>  FILTREAZA 

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ro_elicitatiee_amd"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import gec_common.Doc_Download_VPN

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ro_elicitatiee_amd"
Doc_Download = gec_common.Doc_Download_VPN.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'ro_elicitatiee_amd'
  
    notice_data.currency = 'RON'
    
    notice_data.main_language = 'RO'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RO'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 16
    
    # Onsite Field -Numar anunt erata
    # Onsite Comment -also take notice_no from notice url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div:nth-child(1) > strong').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data publicare
    # Onsite Comment -None 5 dec. 2023

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(2) > div:nth-child(2) > strong").text
        publish_date = re.findall('\d+ \w+. \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    # Onsite Field -Data transmitere spre publicare
    # Onsite Comment -None 29 nov. 2023

    try:
        notice_deadline1 = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(3) > div:nth-child(2)").text
        notice_deadline = re.findall('\d+ \w+. \d{4}',notice_deadline1)[0]
        notice_deadline_date = datetime.strptime(notice_deadline,'%d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment - along with title merge the following statement with a dash"-" "Modification of the original information provided by the contracting authority".... eg "title - Modification of the original......" 

    try:
        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div > h2 > a').text
        notice_data.local_title = local_title+' '+'- Modification of the original information provided by the contracting authority'
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        custom_tags_data = custom_tags()
    
        custom_tags_data.tender_custom_tag_company_id = tender_html_element.find_element(By.CSS_SELECTOR, 'div.row.margin-0.ng-scope > div').text.split('Autoritatea contractanta:')[1].split('-')[0].strip()
       
        custom_tags_data.custom_tags_cleanup()
        notice_data.custom_tags.append(custom_tags_data)
    except Exception as e:
        logging.info("Exception in tender_custom_tag_company_id: {}".format(type(e).__name__))
        pass
        
    try:
        notice_url_click = WebDriverWait(tender_html_element,150).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div:nth-child(1) > div > h2 > a')))
        page_main.execute_script("arguments[0].click();",notice_url_click)
        
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#esection-1 > div.widget-body')))

        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url_click: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    # Onsite Field -Tipul contractului
    # Onsite Comment -"Lucrari=Works","Furnizare=Supply","Servicii=Service"

    try:
        notice_data.contract_type_actual = page_main.find_element(By.XPATH, '//*[contains(text(),"contractului")]//following::span[1]').text
        if "Servicii" in notice_data.contract_type_actual:
            notice_data.notice_contract_type="Service"
        elif "Lucrari" in notice_data.contract_type_actual:
            notice_data.notice_contract_type='Works'
        elif "Furnizare" in notice_data.contract_type_actual:
            notice_data.notice_contract_type='Supply'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        deadline = page_main.find_element(By.CSS_SELECTOR, '#esection-7 > div.widget-body > ng-transclude > div:nth-child(2) > table > tbody').text
        if 'Termen limita pentru primirea ofertelor' in deadline:
            for date in page_main.find_elements(By.CSS_SELECTOR, "#esection-7 > div.widget-body > ng-transclude > div:nth-child(2) > table > tbody > tr"):
                    data = date.text
                    if 'Termen limita pentru primirea ofertelor' in data:
                        notice_deadline = date.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+',notice_deadline)[0]
                        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
                        logging.info(notice_data.notice_deadline)
        else:
            notice_data.notice_deadline = notice_deadline_date
            logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        amount = page_main.find_element(By.CSS_SELECTOR, '#esection-7 > div.widget-body > ng-transclude > div:nth-child(2) > table > tbody').text
        if 'Valoarea totala estimata' in amount:
            for date in page_main.find_elements(By.CSS_SELECTOR, "#esection-7 > div.widget-body > ng-transclude > div:nth-child(2) > table > tbody > tr"):
                    data = date.text
                    if 'Valoarea totala estimata' in data:
                        est_amount = date.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                        est_amount = re.sub("[^\d\.\,]","",est_amount)
                        notice_data.est_amount =float(est_amount.strip())
                        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
      # Onsite Field -Descriere succinta:
    # Onsite Comment -None

    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text()," succinta")]//following::span[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Numar de referinta
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = page_main.find_element(By.XPATH, '//*[contains(text(),"Numar de referinta")]//following::span[1]').text.strip()
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass

    # Onsite Field -Data expedierii prezentului anunt
    # Onsite Comment -None

    try:
        dispatch_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Data expedierii prezentului")]//following::span[1]').text
        dispatch_date = re.findall('\d+.\d+.\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass

#     # Onsite Field -None
#     # Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ----"//*[@id="container-sizing"]/div[5]/div[2]/div/div"
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#container-sizing').get_attribute("outerHTML")                     
    except:
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'RO'
        customer_details_data.org_language = 'RO'

    #         # Onsite Field -Autoritate contractanta
    #         # Onsite Comment -take data which is after "Autoritate contractanta"

        customer_details_data.org_name = page_main.find_element(By.CSS_SELECTOR, 'div.c-sticky-header__details > ul.ng-scope').text.split('AUTORITATE CONTRACTANTA:')[1].strip()

    #         # Onsite Field -Adresa principala (URL)
    #         # Onsite Comment -None

        try:
            customer_details_data.org_website = page_main.find_element(By.XPATH, '//*[contains(text(),"Adresa principala")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

    #         # Onsite Field -Autoritate contractanta
    #         # Onsite Comment -take data which is after "Autoritate contractanta"

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Punct")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    #         # Onsite Field -Denumire si adrese
    #         # Onsite Comment -Note: splite data between  Adresa till E-mail

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Denumire si adrese")]//following::div[1]').text.split('Adresa:')[1].split('E-mail:')[0].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    #         # Onsite Field -E-mail
    #         # Onsite Comment -None

        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"E-mail:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    #         # Onsite Field -Telefon
    #         # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Telefon:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    #         # Onsite Field -Denumire si adrese
    #         # Onsite Comment -Note:Splite after Fax

        try:
            customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Denumire si adrese")]//following::div[1]').text.split('Fax:')[1].split('Adresa principala(URL):')[0].strip()
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

    #         # Onsite Field -Localitate
    #         # Onsite Comment -None

        try:
            customer_details_data.org_city = page_main.find_element(By.XPATH, '//*[contains(text(),"Localitate:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    #         # Onsite Field -Cod postal
    #         # Onsite Comment -

        try:
            customer_details_data.postal_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Cod postal:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

# # Onsite Field -None
# # Onsite Comment - Cod CPV Principal

    try:              
        cpvs_data = cpvs()
        cpvs_data.cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"CPV")]//following::span[1]').text.split('-')[0].strip()
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass  

# #Onsite Field -
# # Onsite Comment - ref no. - "https://www.e-licitatie.ro/pub/notices/e-notice/v2/view/100184898"
    
    try: 
        lot_number = 1
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#esection-7 > div.widget-body > ng-transclude > div:nth-child(2) > table > tbody > tr'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        # Onsite Field -Lot nr.  
        # Onsite Comment -just take no

            try:
                lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > div:nth-child(3)').text
                lot_details_data.lot_actual_number= re.findall('\d+',lot_actual_number)[-1]
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
            
            if "Lot" in lot_actual_number or 'lot' in lot_actual_number:
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1) > div:nth-child(3)').text.split(lot_details_data.lot_actual_number)[-1].strip()
            if lot_details_data.lot_title != None:
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

# Onsite Field -None
# Onsite Comment -ref url -"https://www.e-licitatie.ro/pub/notices/e-notice/v2/view/100184666"

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#detailsAboutValidation  div:nth-child(2)  strong > a'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.text

            try:
                attachments_data.file_type = attachments_data.file_name.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            external_url = single_record.click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    page_main.execute_script("window.history.go(-1)")
    
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="container-sizing"]/div[5]/div[2]/div/div')))
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body

page_main = Doc_Download.page_details
time.sleep(20)

action = ActionChains(page_main)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.e-licitatie.ro/pub/notices/e-notices"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        previous_date = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' div:nth-child(2) > div:nth-child(4) > div > div:nth-child(1) > span > span > span')))
        page_main.execute_script("arguments[0].click();",previous_date)
        time.sleep(2)
                
        action.send_keys(Keys.ARROW_LEFT)
        time.sleep(2)
        
        action.send_keys(Keys.ENTER) 
        time.sleep(2)

        action.perform()
        
        todays_date = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div:nth-child(2) > div:nth-child(4) > div > div:nth-child(2) > span > span > span')))
        page_main.execute_script("arguments[0].click();",todays_date)
        time.sleep(2)
         
        action.send_keys(Keys.ENTER) 
        time.sleep(2)
    
        action.perform()
        
        search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="THE-SEARCH-BUTTON"]')))
        page_main.execute_script("arguments[0].click();",search)
        time.sleep(5)
        
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="container-sizing"]/div[5]/div[2]/div/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="container-sizing"]/div[5]/div[2]/div/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="container-sizing"]/div[5]/div[2]/div/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="container-sizing"]/div[5]/div[2]/div/div'),page_check))
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
    
    output_json_file.copyFinalJSONToServer(output_json_folder) 
