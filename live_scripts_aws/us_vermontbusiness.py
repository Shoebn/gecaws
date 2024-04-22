from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "us_vermontbusiness"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from selenium import webdriver
from gec_common import functions as fn
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_vermontbusiness"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'us_vermontbusiness'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.currency = 'USD'
    
    try:
        notice_type = page_main.find_element(By.CSS_SELECTOR, '#lblTitle').text
        if 'All Open Bids' in notice_type:
            notice_data.notice_type = 4
            notice_data.script_name = 'us_vermontbusiness_spn'
        elif 'Awards' in notice_type:
            notice_data.notice_type = 7
            notice_data.script_name = 'us_vermontbusiness_ca'
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' tr > td:nth-child(1) > a').text
        notice_data.notice_title = notice_data.local_title 
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        return
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, " tr > td:nth-child(2) > span:nth-child(2)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+ [pmamPMAM]+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td.label > span').text
    except Exception as e:
        logging.info("Exception in org_name: {}".format(type(e).__name__))
        pass
    
    try:
        notice_url_no = tender_html_element.find_element(By.CSS_SELECTOR, ' tr > td:nth-child(1) > a').get_attribute("outerHTML").split('BidID=')[1].split("',")[0].strip()
        notice_data.notice_url = 'https://www.vermontbusinessregistry.com/BidPreview.aspx?BidID='+notice_url_no
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        pass

    try:
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#form1 > table').get_attribute("outerHTML")                     
        except:
            pass
        
        try:
            publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Request Date:")]//following::span[1]').text
            publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+ [pmamPMAM]+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return
        
        try: 
            document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Open Date:")]//following::span[1]').text
            document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
            notice_data.document_opening_time = datetime.strptime(document_opening_time,'%m/%d/%Y').strftime('%Y-%m-%d')
        except Exception as e:
            logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
            pass
        
        try:
            est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Est. Dollar Value:")]//following::span[1]').text
            est_amount = re.sub("[^\d\.\,]", "",est_amount)
            notice_data.est_amount = float(est_amount.replace(',','').strip())
            notice_data.grossbudgetlc = notice_data.est_amount
        except Exception as e: 
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"RFQ Number:")]//following::span[1]').text
            if notice_data.notice_no == 'N/A' or notice_data.notice_no == '':
                notice_data.notice_no = notice_url_no
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Bid Type:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in document_type_Description: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Bid Description:")]//following::span[1]').text
            notice_data.notice_summary_english = notice_data.local_description
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'US'
            customer_details_data.org_language = 'EN'
            customer_details_data.org_name = org_name
            
            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, '#form1 > table > tbody > tr:nth-child(3) > td:nth-child(2) > table:nth-child(2) > tbody > tr:nth-child(2) > td').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__)) 
                pass 
            
            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Information:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__)) 
                pass 
        
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Phone:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__)) 
                pass
            
            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax:")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__)) 
                pass
            
            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email:")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__)) 
                pass 
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        
        try:
            notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"For additional information:")]//following::a[1]').get_attribute('href')
        except Exception as e:
            logging.info("Exception in additional_tender_url: {}".format(type(e).__name__)) 
            pass 
        
        try:
            for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Bid Attachments:")]//following::a'):
                attachments_data = attachments()

                attachments_data.file_name = single_record.text

                attachments_data.external_url = single_record.get_attribute("href")

                try:
                    attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                except:
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
        
        try:
            if notice_data.notice_type == 7:
                lot_details_data = lot_details() 
                lot_details_data.lot_title = notice_data.notice_title
                notice_data.is_lot_default = True
                lot_details_data.lot_title_english = lot_details_data.lot_title
                lot_details_data.lot_number = 1

                try:
                    award_details_data = award_details()

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Awardees")]//following::tr[1]/td[1]').text

                    try:
                        grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Awardees")]//following::tr[2]/td[2]').text
                        grossawardvaluelc = re.sub("[^\d\.\,]", "",grossawardvaluelc)
                        award_details_data.grossawardvaluelc = float(grossawardvaluelc.replace(',','').strip())
                    except Exception as e:
                        logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                        pass

                    try:
                        award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Awardees")]//following::tr[1]/td[2]').text
                        award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                        award_details_data.award_date = datetime.strptime(award_date,'%m/%d/%Y').strftime('%Y/%m/%d')
                    except Exception as e:
                        logging.info("Exception in award_date: {}".format(type(e).__name__))
                        pass

                    try:
                        award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"Awardees")]//following::tr[2]/td[1]').text
                    except Exception as e:
                        logging.info("Exception in address: {}".format(type(e).__name__))
                        pass

                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__))
            pass
        
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
page_main.maximize_window()
time.sleep(20)

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(options=options)
time.sleep(20)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.vermontbusinessregistry.com/"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url) 
        
        lst = [1,7]
        for index in lst:
            pp_btn = Select(page_main.find_element(By.CSS_SELECTOR,'#Table1 > tbody > tr:nth-child(3) > td:nth-child(2) > select'))
            pp_btn.select_by_index(index)
            time.sleep(5)

            try:
                for page_no in range(2,10):
                    page_check = WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#gvResults > tbody > tr > td > table > tbody'))).text
                    rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#gvResults > tbody > tr > td > table > tbody')))
                    length = len(rows)
                    for records in range(0,length-1):
                        tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#gvResults > tbody > tr > td > table > tbody')))[records]
                        extract_and_save_notice(tender_html_element)
                        if notice_count >= MAX_NOTICES:
                            break

                    try:   
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        WebDriverWait(page_main, 100).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#gvResults > tbody > tr > td > table > tbody'),page_check))
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
