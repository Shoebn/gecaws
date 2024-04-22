from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_marcheawsol_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "fr_marcheawsol_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'fr_marcheawsol_spn'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)

    notice_data.main_language = 'FR'
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    # Onsite Field -Publié le
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "#entity  div.col-6.col-md-3.col-sm-12").get_attribute('innerHTML')
        publish_date = re.findall('\d+/\d+/\d{2}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

     # Onsite Field -Date limite
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "#entity  div.col-6.col-md-7.col-sm-12").get_attribute('innerHTML')
        notice_deadline = re.findall('\d+/\d+/\d{2}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass


    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-2.text-center.first-child-bandeau').get_attribute("innerHTML")
        notice_data.notice_url = "https://www.marches-publics.info"+notice_url.split('="')[1].split('"')[0].strip()
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#content > div > div.container-fluid').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Référence
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, "//*[contains(text(),'Référence')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

#Format 1 : "https://www.marches-publics.info/Annonces/MPI-pub-2023298141.htm"  use following for "format 1"

    # Onsite Field -Objet
    # Onsite Comment -None

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, "//*[contains(text(),'Objet')]//following::td[1]").text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Description')]//following::td[1]").text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type de marché
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Type de marché')]//following::td[1]").text
        if "SERVICES" in notice_data.contract_type_actual.upper():
            notice_data.notice_contract_type ="Service"
        elif "TRAVAUX" in notice_data.contract_type_actual.upper():
            notice_data.notice_contract_type ="Works"
        elif "FOURNITURES" in notice_data.contract_type_actual.upper():
            notice_data.notice_contract_type ="Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Mode
    # Onsite Comment -None

    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Mode')]//following::td[1]").text
        notice_data.type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Durée
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, "//*[contains(text(),'Durée')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass


    try:              
        customer_details_data = customer_details()

        org_name = tender_html_element.find_element(By.CSS_SELECTOR, '#entity > div:nth-child(2) > div > h2').get_attribute('innerHTML')
        customer_details_data.org_name = org_name.split('(')[0].strip()
    # Onsite Field -Tel
    # Onsite Comment -None

        try:
            org_phone = page_details.find_element(By.CSS_SELECTOR, '#AAPCGenere > table:nth-child(3) > tbody').text.split('Tél :')[1].split('\n')[0].strip()
            if 'Fax : ' in org_phone:
                customer_details_data.org_phone = org_phone.split('-')[0].strip()
            else:
                customer_details_data.org_phone = org_phone
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_fax = page_details.find_element(By.CSS_SELECTOR, '#AAPCGenere > table:nth-child(3) > tbody').text.split('Fax : ')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -None
    # Onsite Comment -take second line data as "contact person" from the given selector

        try:
            customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, '#AAPCGenere > table:nth-child(3) > tbody').text.split('\n')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -None
    # Onsite Comment -take "third line" and "fourth line" as org address

        try:
            org_address = page_details.find_element(By.CSS_SELECTOR, '#AAPCGenere > table:nth-child(3) > tbody').text.split('\n')[2:4]
            customer_details_data.org_address = ' '.join(org_address).strip() 
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        
        customer_details_data.org_country = 'FR'
        customer_details_data.org_language = 'FR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None 

    try:      
        cpv_at_source = ''
        for single_record in page_details.find_elements(By.XPATH, "//td[contains('Code CPV principal,Code CPV complémentaire',text())]//following::tr/td/strong"):
        # Onsite Field -UNSPSC Categories / UNSPSC Category
        # Onsite Comment -for detail page: click on (selector : "tr> td > a"), split the cpvs from "Categories" tab (selector : #categoriesAbstractTab > a)

            cpv_code = single_record.text
            cpv_code = re.findall('\d{8}',cpv_code)[0]
            cpv_at_source += cpv_code
            cpv_at_source += ','
            
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
            
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')            
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tr > td > table > tbody > tr')[2:]:
            cpvs_data = cpvs()
            # Onsite Field -split "lot cpv"
            # Onsite Comment -None

            cpv_code = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(4)').text
            cpvs_data.cpv_code = cpv_code

            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
        pass
    

    try:
        lotss = page_details.find_element(By.XPATH, '//td[@class="AW_TableM_Bloc1_Clair"]/descendant::tr[1]').text
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tr > td > table > tbody > tr')[2:]:
            if 'Lots' in lotss:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
            # Onsite Field -split data from "Lots" for  "lot actual number"
            # Onsite Comment -None

                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

            # Onsite Field -split data from "Libellé" for  "lot title" just take first line for  as second line is location
            # Onsite Comment -None

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

            # Onsite Field -split data from "Estimé € HT" for  "lot netbudget"
            # Onsite Comment -Estimé € HT

                try:
                    lot_netbudget = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                    lot_netbudget = re.sub("[^\d\.\,]","",lot_netbudget)
                    lot_netbudget =lot_netbudget.replace(' ','').replace('.','')
                    lot_details_data.lot_netbudget = float(lot_netbudget.replace(',','.').strip())
                    lot_details_data.lot_netbudget_lc = lot_details_data.lot_netbudget
                except Exception as e:
                    logging.info("Exception in lot_netbudget: {}".format(type(e).__name__))
                    pass

                try:
                    lot_cpvs_data = lot_cpvs()
                    # Onsite Field -split "lot cpv"
                    # Onsite Comment -None

                    lot_cpv = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(4)').text
                    lot_cpvs_data.lot_cpv_code = lot_cpv

                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass

                try:
                    cpv_sources = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(4)').text
                    lot_details_data.lot_cpv_at_source = cpv_sources
                    notice_data.cpv_at_source +=  ',' + lot_details_data.lot_cpv_at_source
                except:
                    pass
                
                # Onsite Field -split "lot cpv"
            # Onsite Comment -None

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Award criteria	: if the award criteria having value of weight withthe field name "Technical" and "price" than only take the data.. do not pass the hole line of  Award criteria
# Onsite Comment -None

    try:
        criteria =  page_details.find_element(By.XPATH, "//*[contains(text(),'Critères')]//following::td[1]").text

        for single_record in criteria.split('\n')[1:]:
            if '%' in single_record:
                tender_criteria_data = tender_criteria()
            # Onsite Field -split title after percentage value ...  eg "60 % : Prix"    then just take  "Prix"
            # Onsite Comment -None
                tender_criteria_data.tender_criteria_title = single_record.split(':')[1].split('\n')[0].strip()

                if 'prix' in tender_criteria_data.tender_criteria_title.lower():
                    tender_criteria_data.tender_criteria_title = 'price'
                    tender_criteria_data.tender_is_price_related = True

            # Onsite Field -split  percentage value  just take value ...  eg "60 % : Prix"    then just take  "60%"
            # Onsite Comment -None
                if tender_criteria_data.tender_criteria_title !='':
                    tender_criteria_weight = single_record.split('%')[0].strip()
                    tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)                 

                tender_criteria_data.tender_criteria_cleanup()
                notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass

# Onsite Field -Documents
# Onsite Comment -None
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'td.AW_TableM_Bloc2_Clair a'):
            attachments_data = attachments()
        # Onsite Field -Documents
        # Onsite Comment -None

            attachments_data.file_name = single_record.text
        # Onsite Field -Documents
        # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Format 2 "https://www.marches-publics.info/Annonces/MPI-pub-2023298097.htm" use following link for "format 2"


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
    urls = ["https://www.marches-publics.info/Annonces/lister"]

    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        Toutes_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="toutes"]'))).click()
        time.sleep(2)
        
        pp_btn = Select(page_main.find_element(By.CSS_SELECTOR,'#dateParution'))
        pp_btn.select_by_index(3)
        time.sleep(5)
        
        Toutes_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="Dume"]'))).click()
        time.sleep(2)
        
        clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'input#sub.buttonBleuv2')))
        page_main.execute_script("arguments[0].click();",clk)

        try:
            ids = ['travaux','services','fournitures']
            for t in ids:
                try:
                    click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.ID,t))).click()
                    time.sleep(10)
                except:
                    pass
        
                for page_no in range(1,7):
                    page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.ID,'entity'))).text
                    rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.ID, 'entity')))
                    length = len(rows)
                    for records in range(0,length):
                        tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.ID, 'entity')))[records]
                        extract_and_save_notice(tender_html_element)
                        if notice_count >= MAX_NOTICES:
                            break

                        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                            break
    
                        if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                            logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                            break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
        
                    try:   
                        if t == 'travaux':
                            next_page = 'https://www.marches-publics.info/Annonces/lister?pager_t='+str(page_no)+'&pager_s=2'
                            next_page_no = next_page.split('t=')[1].split('&pager')[0].strip()
                            fn.load_page(page_main,next_page,80)
                        else:
                            next_page = 'https://www.marches-publics.info/Annonces/lister?pager_t='+str(next_page_no)+'&pager_s='+str(page_no)
                            fn.load_page(page_main,next_page,80)
                        WebDriverWait(page_main, 80).until_not(EC.text_to_be_present_in_element((By.ID,'entity'),page_check))
                    except Exception as e:
                        logging.info("Exception in next_page: {}".format(type(e).__name__))
                        logging.info("No next page")
                        break
        except Exception as e:
            logging.info("No new record")
            pass
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
