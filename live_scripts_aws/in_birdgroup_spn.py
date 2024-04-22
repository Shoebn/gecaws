from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_birdgroup_spn"
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
SCRIPT_NAME = "in_birdgroup_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_birdgroup_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'INR'
 
    notice_data.main_language = 'EN'
    
    notice_data.procurement_method = 0
      
    notice_data.notice_url = 'https://www.birdgroup.co.in/omdc-current-tenders-2/'
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'THE ORISSA MINERALS DEVELOPMENT COMPANY LIMITED (OMDC)'
        customer_details_data.org_parent_id = '7786586'
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
  
    format_tender = page_main.find_element(By.CSS_SELECTOR, 'body > div > div > div > div:nth-child(3) > div.col-sm-8 > div > div.panel-heading').text
    
    # Formate 1 [ Iron Ores]
    
    if " Iron Ores" in format_tender:
        
        try:
            notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            if " Corrigendum" in notice_type:
                notice_data.notice_type = 16 
            else:
                notice_data.notice_type = 4
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#dataTables-example  tr > td:nth-child(1)').text.split("\n")[0].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

    #     # Onsite Field -Auction Description
    #     # Onsite Comment -None

        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#dataTables-example tr > td:nth-child(2)').text
            notice_data.notice_title = notice_data.local_title
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

    #     # Onsite Field -Auction Date & Time
    #     # Onsite Comment -Note:Splite front of "E-Auction start" date

        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "#dataTables-example tr > td:nth-child(3)").text
            publish_date_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
            publish_date_time = re.findall('\d+:\d+',publish_date)[0]
            publish_datetime =publish_date_date+' '+publish_date_time
            notice_data.publish_date = datetime.strptime(publish_datetime,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

        try:
            notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
        except:
            pass

    #     # Onsite Field -Auction Date & Time >> Click here for E-Auction Link
    #     # Onsite Comment -None
    
        try:
            notice_data.additional_tender_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(3) > p > a').get_attribute("href")
        except Exception as e:
            logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
            pass

    # # Onsite Field -Online Forward Auction Notice No.
    # # Onsite Comment -None

        try:              
            for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td:nth-child(1) > p > a'):
                attachments_data = attachments()

                file_name = single_record.get_attribute('href')
                if "uploads" in file_name:
                    attachments_data.file_name = file_name.split("uploads/")[1].split(".pdf")[0].strip()
                else:
                    attachments_data.file_name = file_name.split("TenderEntry/")[1].split(".aspx")[0].strip()

            # Onsite Field -Online Forward Auction Notice No.
            # Onsite Comment -Note:as a attachment  skip the below hyperlink "Click here for E-Auction details" from the field name "Online Forward Auction Notice No." .Other than above take all the documents as a attachment

                attachments_data.external_url = single_record.get_attribute('href')

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
#*********************************************************************************************************************
    elif "Manganese Ores" in format_tender:
        
        notice_data.notice_type = 4
                
        # Formate 2 [Maganese Ore]
# Note:Click the "table > tbody > tr > td:nth-child(2) > a" "Maganese Ore" and grab the data
        
    # Onsite Field -Online Forward Auction Notice No.
    # Onsite Comment -None

        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#dataTables-example tr > td:nth-child(1)').text.split("\n")[0].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Auction Description
    # Onsite Comment -None

        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#dataTables-example tr > td:nth-child(2)').text
            notice_data.notice_title = notice_data.local_title
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Auction Date & Time
    # Onsite Comment -None

        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "#dataTables-example tr > td:nth-child(3)").text
            publish_date_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
            publish_date_time = re.findall('\d+:\d+:\d+',publish_date)[0]
            publish_datetime = publish_date_date+' '+publish_date_time
            notice_data.publish_date = datetime.strptime(publish_datetime,'%d-%m-%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return
    
        try:
            notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
        except:
            pass

    # Onsite Field -Online Forward Auction Notice No.
    # Onsite Comment -None

        try:
            notice_data.additional_tender_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(1) > p > a').get_attribute("href") 
        except Exception as e:
            logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
            pass
        
#*********************************************************************************************************************
  # Formate 3 [Miscellaneos/Open Tenders]  
# Note:Click the "table > tbody > tr > td:nth-child(4) > a" "Miscellaneos/Open Tenders" and grab the data

    elif "Miscellaneous" in format_tender:
        
        try:
            notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            if " Corrigendum" in notice_type:
                notice_data.notice_type = 16 
            else:
                notice_data.notice_type = 4
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

        # Onsite Field -Tender Notice No
        # Onsite Comment -Note:If tender notice no is blank than pass this "tr > td:nth-child(1)"

        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > p:nth-child(1)').text
            if notice_data.notice_no == "":
                notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(1)').text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

        # Onsite Field -Tender Notice No
        # Onsite Comment -None

        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(2) > p:nth-child(2)").text
            publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

        # Onsite Field -Tender Description
        # Onsite Comment -None

        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
            notice_data.notice_title = notice_data.local_title
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        # Onsite Field -Due Date & time Of Submission
        # Onsite Comment -Note:if the attachment name with "click here to view Corrigendum' than the notice type will be 16 and take 2nd date as a deadline

        try:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(4)").text
            notice_deadline_date = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
            notice_deadline_time = re.findall('\d+:\d+',notice_deadline)[0]
            notice_deadline_datetime=notice_deadline_date+' '+notice_deadline_time
            notice_data.notice_deadline = datetime.strptime(notice_deadline_datetime,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass

        try:
            notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
        except:
             pass
            
         # Onsite Field -Tender Notice No
    # Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td:nth-child(2) > p > a'):
            attachments_data = attachments()
        # Onsite Field -Tender Notice No
        # Onsite Comment -Note:split only file_name , for ex :"OMDC-Tender-for-hiring-one-light-vehicle-18-05-2023.pdf , here take only"OMDC-Tender-for-hiring-one-light-vehicle-18-05-2023"

            attachments_data.file_name = single_record.get_attribute('href').split("uploads/")[1].split(".pdf")[0].strip()

            try:
                attachments_data.file_type = single_record.get_attribute('href').split(".")[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

        # Onsite Field -Tender Notice No
        # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
        
#***********************************************************************************************************************

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.birdgroup.co.in/omdc-current-tenders-2/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        lit = [0,1,3]
        for no in lit:
            format1 = page_main.find_elements(By.CSS_SELECTOR, '#omdc_cur_hori_menu > table > tbody > tr > td > a')[no]
            format1.click()
            time.sleep(5)
            try:
                for page_no in range(2,20):
                    page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'//*[@id="dataTables-example"]/tbody/tr'))).text
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dataTables-example"]/tbody/tr')))
                    length = len(rows)
                    for records in range(0,length):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dataTables-example"]/tbody/tr')))[records]
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
                        WebDriverWait(page_main, 80).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="dataTables-example"]/tbody/tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
