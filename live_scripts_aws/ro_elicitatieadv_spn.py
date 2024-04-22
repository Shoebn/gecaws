from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ro_elicitatieadv_spn"
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
import gec_common.Doc_Download_VPN as Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ro_elicitatieadv_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'ro_elicitatieadv_spn'
    notice_data.main_language = 'RO'
    
    notice_data.currency = 'RON'

    notice_data.procurement_method = 2
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RO'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.notice_type = 4
    notice_data.class_at_source = 'CPV'

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div > h2 > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass 
    # Onsite Field -Numar anunt
    # Onsite Comment -also take notice_no from notice url
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div:nth-child(1) > strong').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    # Onsite Field -Data publicare
    # Onsite Comment -None
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(2) > div:nth-child(1) > span > strong").text
        publish_date = re.findall('\d+.\d+.\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Data limita depunere oferta:
    # Onsite Comment -None
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(2) > div:nth-child(2) > span > strong").text
        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    # Onsite Field -Tip contract:
    # Onsite Comment -"Lucrari=Works","Furnizare=Supply","Servicii=Service" 
    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div:nth-child(2) > strong').text
        if "Servicii" in notice_data.contract_type_actual:
            notice_data.notice_contract_type="Service"
        elif "Lucrari" in notice_data.contract_type_actual:
            notice_data.notice_contract_type='Works'
        elif "Furnizare" in notice_data.contract_type_actual:
            notice_data.notice_contract_type='Supply'
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    try:
        org_name1 = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > dic > strong').text
        org_name2 = re.findall(r'\d+',org_name1)[0]
        org_name = org_name1.split(org_name2)[1]
    except:
        pass

    try:
        notice_url = WebDriverWait(tender_html_element, 100).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.title-entity.ng-binding.ng-scope')))
        page_main.execute_script("arguments[0].click();",notice_url)
        time.sleep(3)
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    time.sleep(5)
    # Onsite Field -Descriere succinta
    # Onsite Comment -None
    
    try: 
        notice_data.local_description = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(),"Descriere contract:")]//following::div[1]'))).text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -Valoare
    # Onsite Comment -ref url "https://www.e-licitatie.ro/pub/notices/adv-notices/view/100546383"
    try:
        est_amount1 = page_main.find_element(By.XPATH, '//*[contains(text(),"Valoare estimata")]//following::div[1]').text
        if '-' in est_amount1:
            est_amount = est_amount1.split("-")[1]
            est_amount = re.sub("[^\d\.\,]","",est_amount1)
            notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
        else:
            est_amount = re.sub("[^\d\.\,]","",est_amount1)
            notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        contract_duration = page_main.find_element(By.XPATH, '//*[contains(text(),"Conditii referitoare la contract:")]//following::div[1]').text
        notice_data.contract_duration = re.findall(r'\d+ luni',contract_duration)[0]
    except:
        pass

    # Onsite Field -None
    # Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ---- "//*[@id="container-sizing"]/div[5]/div[2]/div"
    try: 
        notice_data.notice_text += WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#container-sizing > div:nth-child(3)'))).get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()

        customer_details_data.org_country = "RO"
        customer_details_data.org_language = 'RO'

        customer_details_data.org_name = org_name

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Punct")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # Onsite Field - adrese
    # Onsite Comment -

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Adresa")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
    # Onsite Field -E-mail
    # Onsite Comment -None
        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"E-mail:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # Onsite Field -Telefon
    # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_main.find_element(By.CSS_SELECTOR, 'div.c-df-notice__box').text.split("Tel:")[1].split("Fax:")[0]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
    # Onsite Field -Fax
    # Onsite Comment -
        try:
            org_fax = page_main.find_element(By.CSS_SELECTOR, 'div.c-df-notice__box').text.split("Fax:")[1].split("E-mail:")[0]
            if org_fax != '' and len(org_fax) > 1 :
                customer_details_data.org_fax = org_fax
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

    # Onsite Field -Localitate
    # Onsite Comment -None

        try:
            customer_details_data.org_city = page_main.find_element(By.XPATH, '//*[contains(text(),"Localitate:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        custom_tags_data = custom_tags()
    # Onsite Field -CIF
    # Onsite Comment -None
        custom_tags_data.tender_custom_tag_company_id = page_main.find_element(By.CSS_SELECTOR, 'div.s-row.u-displayfield').text.split("CIF:")[1].strip()
       
        custom_tags_data.custom_tags_cleanup()
        notice_data.custom_tags.append(custom_tags_data)
    except Exception as e:
        logging.info("Exception in custom_tags: {}".format(type(e).__name__)) 
        pass  

# Onsite Field -None
# Onsite Comment - Cod CPV Principal

    try:
        cpv_code1 = page_main.find_element(By.XPATH, '//*[contains(text(),"CPV")]//following::div[1]').text
        cpv_code = re.findall('\d{8}',cpv_code1)
        for cpv in cpv_code:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:
        cpv_at_source = ''
        cpv_code1 = page_main.find_element(By.XPATH, '//*[contains(text(),"CPV")]//following::div[1]').text
        cpv_code = re.findall('\d{8}',cpv_code1)
        for cpv in cpv_code:
            cpv_at_source += cpv
            cpv_at_source += ','
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
    except:
        pass
        
    try:              
        attachments_data = attachments()
    # Onsite Field -Caiet de sarcini:
    # Onsite Comment -
        try:
            attachments_data.file_type = page_main.find_element(By.CSS_SELECTOR, 'a.ng-isolate-scope').text.split(".")[-1]
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass
        
        attachments_data.file_name = page_main.find_element(By.CSS_SELECTOR, 'a.ng-isolate-scope').text.replace(attachments_data.file_type,'')
        time.sleep(3)
        external_url = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.ng-isolate-scope')))
        page_main.execute_script("arguments[0].click();",external_url)
        time.sleep(5)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
        time.sleep(10)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    time.sleep(3)
    back = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"button.ng-isolate-scope.btn.btn-default.carbon.shutter-out-vertical")))
    page_main.execute_script("arguments[0].click();",back)
    time.sleep(3)
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="container-sizing"]/div[5]/div[2]/div')))
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
page_main = Doc_Download.page_details 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.e-licitatie.ro/pub/adv-notices/list/1"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(1,50):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.u-items-list__item.ng-scope'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.u-items-list__item.ng-scope')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.u-items-list__item.ng-scope')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div:nth-child(6) > div > ul > li:nth-child(5) > a")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(4)
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.u-items-list__item.ng-scope'),page_check))
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
    
