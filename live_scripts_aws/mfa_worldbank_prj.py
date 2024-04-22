from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "mfa_worldbank_prj"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "mfa_worldbank_prj"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'mfa_worldbank_prj'
    
    notice_data.main_language = 'EN'
    
    notice_data.currency = 'USD'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 10
    
    # Onsite Field -Project Title
    # Onsite Comment -None Project Title
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Country
    # Onsite Comment -1.replace following countries with given keyword(West Bank and Gaza,OECS Countries,
    #Andean Countries,Western and Central Africa,Eastern and Southern Africa,Pacific Islands,World,Middle East 
    #and North Africa,Latin America,Latin America and Caribbean,Multi-Regional,Africa,Western Africa,Eastern Africa,
    #Europe and Central Asia,South East Asia,East Asia and Pacific,South Asia = US)

    try:
        country = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        performance_country_data = performance_country()
        performance_country_1 = country
        performance_country_data.performance_country = fn.procedure_mapping("assets/mfa_worldbank_all_countrycode.csv",performance_country_1)
        if performance_country_data.performance_country == None:
            performance_country_data.performance_country = 'US'
        notice_data.performance_country.append(performance_country_data)
    except Exception as e:
        logging.info("Exception in performance_country: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Project ID
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:              
        funding_agencies_data = funding_agencies()
        funding_agencies_data.funding_agency = 1012
        funding_agencies_data.funding_agencies_cleanup()
        notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Last updated Date
    # Onsite Comment -None 

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_url ='https://projects.worldbank.org/en/projects-operations/project-detail/'+str(notice_data.notice_no)
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
   
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.par.parsys > div > project-details').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
     # Onsite Field -Commitment Amount
    # Onsite Comment -None

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Commitment Amount")]//following::p[1]').text
        if 'million' in est_amount:
            est_amount = re.sub("[^\d\.\,]","",est_amount)
            est_amount1 =float(est_amount.replace(',','').strip())
            notice_data.est_amount = est_amount1*1000000
            notice_data.grossbudgetlc =  notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'EN'
        
         # Onsite Field -Implementing Agency
        # Onsite Comment -1.if org_name is blank then pass "The World Bank" as org_name static. and then also add new field "org_parent_id" and in this field pass "1012" static.

        
        org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Implementing Agency")]//following::p[1]').text
        if org_name == '' :
            customer_details_data.org_name = 'The World Bank'
            customer_details_data.org_parent_id = 1012
        else:
            customer_details_data.org_name = org_name
            
        # Onsite Field -Country
        # Onsite Comment -1.replace following countries with given keyword(West Bank and Gaza,OECS Countries,Andean Countries,Western and Central Africa,Eastern and Southern Africa,Pacific Islands,World,Middle East and North Africa,Latin America,Latin America and Caribbean,Multi-Regional,Africa,Western Africa,Eastern Africa,Europe and Central Asia,South East Asia,East Asia and Pacific,South Asia = US)

        try:
            country1 = country
            customer_details_data.org_country =fn.procedure_mapping("assets/mfa_worldbank_prj_countrycode.csv",country1)
            if customer_details_data.org_country == None:
                customer_details_data.org_country = 'US'
        except Exception as e:
            logging.info("Exception in org_country: {}".format(type(e).__name__))
            pass

#         # Onsite Field -//*[contains(text(),"Team Leader")]//following::p[1]
#         # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Team Leader")]//following::p[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://projects.worldbank.org/en/projects-operations/projects-list?os=0"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.CSS_SELECTOR," div.c14v1-body.c14v1-body-text.responsive-table.project-opt-table > div > table > tbody > tr"))).text
                rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, " div.c14v1-body.c14v1-body-text.responsive-table.project-opt-table > div > table > tbody > tr")))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tbody.ng-tns-c1-0 > tr")))[records]
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
                    time.sleep(5)
                    WebDriverWait(page_main, 60).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR," div.c14v1-body.c14v1-body-text.responsive-table.project-opt-table > div > table > tbody > tr"),page_check))
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
