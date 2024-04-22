from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "gr_eprocurement_spn"
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
import gec_common.Doc_Download_ingate
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

#Note:Open the site than click on "Αναζήτηση" this keyword than grab the data

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "gr_eprocurement_spn"
Doc_Download = gec_common.Doc_Download_ingate.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'gr_eprocurement_spn'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GR'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'

    notice_data.main_language = 'EL'

    notice_data.procurement_method = 2

    notice_data.notice_type = 4
    
    notice_data.notice_url = url
    # Onsite Field -Ημ/νία Δημοσίευσης στο Portal
   # Onsite Comment -Note:Grab also time..    If publish_date is not available than take a threshold
    notice_data.notice_text += tr.get_attribute("innerHTML")
    try: 
        publish_date = WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#pc1\:t1\:'+str(tender_html_element)+'\:c9'))).get_attribute("innerHTML")
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except:
        try:
            WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.ID, 'pc1:t1::scroller')))
            html.send_keys(Keys.PAGE_DOWN)
            time.sleep(10)            
            publish_date = WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#pc1\:t1\:'+str(tender_html_element)+'\:c9'))).get_attribute("innerHTML")
            publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
     # Onsite Field -Καταληκτική Ημ/νία Υποβολών
     # Onsite Comment -Note:Grab also time

    try:
        notice_deadline = page_main.find_element(By.CSS_SELECTOR, '#pc1\:t1\:'+str(tender_html_element)+'\:c1 span').get_attribute("innerHTML")
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:              
    # Onsite Field -Κωδικός CPV
    # Onsite Comment -Note:Splite after "Κωδικός CPV" this keyword
        cpv_code1 = page_main.find_element(By.CSS_SELECTOR, '#pc1\:t1\:'+str(tender_html_element)+'\:c7 span').get_attribute("innerHTML")
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
        category = page_main.find_element(By.CSS_SELECTOR,'#pc1\:t1\:'+str(tender_html_element)+'\:c3').get_attribute("innerHTML")
        if category != "" and len(category) > 1:
            notice_data.category = category
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = page_main.find_element(By.CSS_SELECTOR,'#pc1\:t1\:'+str(tender_html_element)+'\:cl1').get_attribute("innerHTML")
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
    # Onsite Field -Αναθέτουσα Αρχή/Αναθέτων Φορέας
    # Onsite Comment -None
        customer_details_data.org_name = page_main.find_element(By.CSS_SELECTOR, '#pc1\:t1\:'+str(tender_html_element)+'\:c8').get_attribute("innerHTML")
        
        customer_details_data.org_country = 'GR'
        customer_details_data.org_language = 'EL'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try: 
        est_amount = page_main.find_element(By.CSS_SELECTOR,'#pc1\:t1\:'+str(tender_html_element)+'\:it1\:\:content').get_attribute("innerHTML")
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.netbudgeteuro = notice_data.est_amount
        notice_data.netbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass    
    
    try:
        local_title = page_main.find_element(By.CSS_SELECTOR, '#pc1\:t1\:'+str(tender_html_element)+'\:c5 span').get_attribute("innerHTML")
        if local_title != "" and len(local_title) > 1:
            notice_data.local_title = local_title
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_url = page_main.find_element(By.CSS_SELECTOR, 'a#pc1\:t1\:'+str(tender_html_element)+'\:cl1')
        page_main.execute_script("arguments[0].click();",notice_url)
        time.sleep(3)

    #     # Onsite Field -Συνοπτικός Τίτλος
    #     # Onsite Comment -None

        
        try:
            notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Τίτλος/Αντικείμενο:")]').text.split("Τίτλος/Αντικείμενο:")[1].strip()
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

    #     # Onsite Field -Τίτλος/Αντικείμενο
    #     # Onsite Comment -None

        try:
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass


        try:
            notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#pt1 > table > tbody > tr').get_attribute("outerHTML")                     
        except:
            pass


    # # Onsite Field -None
    # # Onsite Comment -Note:Click on "Συνημμένα Αρχεία" this tab than grab the data
        try:
            attachment_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/form/div/div[1]/div[4]/div[1]/div[2]/div[2]/div[2]/div[1]/a')))
            page_main.execute_script("arguments[0].click();",attachment_clk)
            time.sleep(3)
            for single_record in page_main.find_elements(By.CSS_SELECTOR,'#t1\:\:db > table > tbody > tr'):
                attachments_data = attachments()
            # Onsite Field -Όνομα Αρχείου
            # Onsite Comment -Note:Don't take file extention

                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text

            # Onsite Field -Όνομα Αρχείου
            # Onsite Comment -Note:Take only file extention

                try:
                    attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split(".")[-1].strip()
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Περιγραφή
            # Onsite Comment -None

                try:
                    file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                    if file_description != "" and len(file_description) > 1:
                        attachments_data.file_description = file_description
                except Exception as e:
                    logging.info("Exception in file_description: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Αρχεία
            # Onsite Comment -Note:Click on "Λήψη" this button

                external_url = WebDriverWait(single_record, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'td:nth-child(4) > span > button')))
                page_main.execute_script("arguments[0].click();",external_url)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

        page_main.execute_script("window.history.go(-1)")
        time.sleep(5)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.local_title) 
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

    url = 'https://nepps-search.eprocurement.gov.gr/actSearch/faces/active_search_main.jspx'
    logging.info('----------------------------------')
    logging.info(url)
    fn.load_page(page_main, url)
    search = page_main.find_element(By.ID,'qryId1::search').click()
    time.sleep(3)
    page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.xv0.xvd.xv0 div:nth-child(2) table tbody tr'))).get_attribute('_afrrk')

    page_main.set_window_size(1920, 1080)
    page_main.execute_script("document.body.style.zoom='5%'")
    time.sleep(5)
    
    try:
        rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.xv0.xvd.xv0 div:nth-child(2) table tbody tr')))
        length = len(rows)
        logging.info(length)
        for records in range(1,length):
            tr = WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'div.xv0.xvd.xv0 div:nth-child(2) table tbody tr')))[records]
            tender_html_element = tr.get_attribute('_afrrk')
            logging.info(tender_html_element)
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break
    except:
        logging.info('No new record')
        pass

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
