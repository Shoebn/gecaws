from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "pl_platformaeb_ca"
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


# ---------------------------------------------------------------------------------------------------------------------

# -- Note : 
#         1) Page_details are not avaialble in source
#         2) for lot details go to "Awarding procedure item" and click on "+" for more lot_details
#         3) some tender details don't have attachments, while others include attachment details.


# ---------------------------------------------------------------------------------------------------------------------

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "pl_platformaeb_ca"
Doc_Download = gec_common.Doc_Download_ingate.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'pl_platformaeb_ca'

    notice_data.main_language = 'PL'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PL'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'PLN'
   
    notice_data.notice_type = 7
    
    notice_data.procurement_method = 2
    
    # Onsite Field -Awarding procedure no
    # Onsite Comment -None

    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        if notice_no !='' and len(notice_no) > 1 :
            notice_data.notice_no = notice_no
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Publication date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        publish_date = re.findall('\d{4}-\d+-\d+ \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
        
    try:
        related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        if related_tender_id !='' and len(related_tender_id) > 1 :
            notice_data.related_tender_id = related_tender_id
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'PL'
        customer_details_data.org_country = 'PL'
    # Onsite Field -Sponser's company
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text

    # Onsite Field -Ordering party
    # Onsite Comment -None

        try:
            org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
            if org_address != '' and len(org_address) > 1:
                customer_details_data.org_address = org_address
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
    # Onsite Field -None
    # Onsite Comment -when you click on notice url it will pass into page main
    try:
        notice_url_click = WebDriverWait(tender_html_element,150).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'img.x-action-col-icon.x-action-col-0')))
        page_main.execute_script("arguments[0].click();",notice_url_click)
        time.sleep(10)
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)


        try:
            notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'div.x-window-body > div > div').get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')


    # Onsite Field -Awarding procedure item
    # Onsite Comment -None
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.x-grid-row-expander'):
            single_record.click()
            time.sleep(2)
            
        try:         
            lot_number = 1
            for single_record in page_main.find_elements(By.CSS_SELECTOR, 'td.x-grid-cell-rowbody'):
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
            # Onsite Field -Awarding procedure item
            # Onsite Comment -None                                                      

                lot_details_data.lot_title = single_record.text.split("Awarding procedure item description")[1].split("\n")[0].strip()
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                
            # Onsite Field -Quantity
            # Onsite Comment -click on "+" button to open lot details,
               
                try:                                                                      
                    lot_details_data.lot_quantity = single_record.text.split("Quantity")[1].split("\n")[0]
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

                # Onsite Field -Unit
                # Onsite Comment -click on "+" button to open lot details,

                try:
                    lot_details_data.lot_quantity_uom = single_record.text.split("Unit")[1].split("\n")[0]
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Bids to the awarding procedure
            # Onsite Comment -note : in the award_details kidnly take only "Rank position: 1" data  , split the first line  below data after "Bidder's data"

                try:
                    for single_record1 in page_main.find_elements(By.XPATH, '//*[contains(text(),"Bids to the awarding procedure")]//following::table/tbody'):
                        if lot_details_data.lot_title in single_record1.text:
                            award_details_data = award_details()

                        # Onsite Field -Bidder's data
                        # Onsite Comment -None                                                 

                            award_details_data.bidder_name = single_record1.text.split("Bidder's data")[1].split("\n")[1]
                            # Onsite Field -Bidder's data
                            # Onsite Comment -None
                            try:
                                award_details_data.address = single_record1.text.split(award_details_data.bidder_name)[1].split("\n")[1]
                            except:
                                pass

                            # Onsite Field -split the numeric data after "Total"
                            # Onsite Comment -None
                            try:
                                netawardvaluelc = single_record1.text.split("Total")[1].split("PLN")[0]
                                netawardvaluelc = re.sub("[^\d\.\,]","",netawardvaluelc)
                                award_details_data.netawardvaluelc =float(netawardvaluelc.replace('.','').replace(',','').strip())
                                award_details_data.grossawardvaluelc = award_details_data.netawardvaluelc
                            except:
                                pass

                            award_details_data.award_details_cleanup()
                            lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass
                
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
        
        try:         
            lot_details_data = lot_details()
            lot_details_data.lot_number = 1
            # Onsite Field -Awarding procedure item
            # Onsite Comment -None                                                      

            lot_details_data.lot_title = notice_data.local_title
            notice_data.is_lot_default = True
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                
            try:
                award_details_data = award_details()

                    # Onsite Field -Bidder's data
                    # Onsite Comment -None
                    
                award_details_data.bidder_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Nazwa")]//following::span[2]').text
                # Onsite Field -split the numeric data after "Total"
                # Onsite Comment -None
                
                try:
                    netawardvaluelc = page_main.find_element(By.XPATH, '//*[contains(text(),"Razem:")]//following::span[1]').text
                    netawardvaluelc = re.sub("[^\d\.\,]","",netawardvaluelc)
                    award_details_data.netawardvaluelc =float(netawardvaluelc.replace('.','').replace(',','').replace(' ','').strip())
                    award_details_data.grossawardvaluelc = award_details_data.netawardvaluelc
                except:
                    pass

                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
            if lot_details_data.award_details !=[]:
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass

    # Onsite Field -None
    # Onsite Comment -note : Some tender details don't have attachments, while others include attachment details.

        try:              
            for single_record in page_main.find_elements(By.CSS_SELECTOR, ' table > tbody > tr.x-grid-row.undefined'):
                attachments_data = attachments()
            # Onsite Field -Name
            # Onsite Comment -note : Some tender details don't have attachments, while others include attachment details.

                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text

            # Onsite Field -Size
            # Onsite Comment -note : Some tender details don't have attachments, while others include attachment details.

                try:
                    attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                except Exception as e:
                    logging.info("Exception in file_size: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Attachments to publication
            # Onsite Comment -note : Some tender details don't have attachments, while others include attachment details.

                external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(7) img').click()
                time.sleep(5)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url= (str(file_dwn[0]))
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

        close = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CLASS_NAME,'x-tool-close')))
        page_main.execute_script("arguments[0].click();",close)
        time.sleep(2)
        try:
            WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/table/tbody/tr')))
        except:
            pass
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details 
page_main.maximize_window()
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://platforma.eb2b.com.pl/auction-result-publication.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        accept_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#button-1014-btnEl')))
        page_main.execute_script("arguments[0].click();",accept_click)
        time.sleep(2)

        try:
            for page_no in range(1,4):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/table/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[2]/div[2]/div[2]/div/div/div[2]/div/div[3]/div/div/div[7]/em")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[2]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/table/tbody/tr[2]'),page_check))
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
