from gec_common.gecclass import *
import logging
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
import gec_common.Doc_Download


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_arbinjneco_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'USD'

    notice_data.main_language = 'EN'

    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    if url == urls[0] and 'njstart' in url:
        notice_data.script_name = 'us_njstart_spn'
    if url == urls[1] and 'arbuy' in url:
        notice_data.script_name = 'us_arkansas_spn'
    if url == urls[2] and 'bidbuy' in url:
        notice_data.script_name = 'us_bidbuy_spn'
    if url == urls[3] and 'nevadaepro' in url:
        notice_data.script_name = 'us_nevadae_spn'
    if url == urls[4] and 'commbuys' in url:
        notice_data.script_name = 'us_commbuys_spn'

    time.sleep(3)
    
    try:
        notice_data.local_title = WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(7)'))).text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        if related_tender_id != '' and len(related_tender_id) > 1:
            notice_data.related_tender_id = related_tender_id
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    try:  
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        contact_person = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except:
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > form > table > tbody'))).get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_text = page_details.find_element(By.CSS_SELECTOR, 'body > form > table > tbody').text
    except:
        pass

    try:  
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Available Date")]//following::td[1]').text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+ [apAP][mM]',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:  
        document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Bid Opening Date:")]//following::td[1]').text
        document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%m/%d/%Y').strftime('%Y-%m-%d')
        logging.info(notice_data.document_opening_time)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Bulletin Desc:")]//following::td[1]').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:  
        tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Blanket/Contract Begin Date:")]//following::td[1]').text
        tender_contract_start_date = re.findall('\d+/\d+/\d{4}',tender_contract_start_date)[0]
        notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.tender_contract_start_date)
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass
    
    try:  
        tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Blanket/Contract End Date:")]//following::td[1]').text
        tender_contract_end_date = re.findall('\d+/\d+/\d{4}',tender_contract_end_date)[0]
        notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.tender_contract_end_date)
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass
    
    try:  
        pre_bid_meeting_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Pre Bid Conference:")]//following::td[1]').text
        pre_bid_meeting_date = re.findall('\d+/\d+/\d{4}',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%m/%d/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.pre_bid_meeting_date)
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Retainage")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        
        customer_details_data.org_country = 'US'
        customer_details_data.org_currency = 'USD'
        customer_details_data.org_language = 'EN'

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Organization:")]//following::td[1]').text
        try:
            customer_details_data.contact_person = contact_person
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        try:
            org_address1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Department:")]//following::td[1]').text
            org_address2 = page_details.find_element(By.XPATH, '//*[contains(text(),"Location:")]//following::td[1]').text                                     
            customer_details_data.org_address = org_address1+' '+org_address2
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        try:
            org_phone1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Info Contact")]//following::td[1]').text
            try: 
                phone_pattern = re.compile(r"[(]\d{3}[)-.\s]?\d{3}[-.\s]?\d{4}")
                org_phone = phone_pattern.findall(org_phone1)[0]
                customer_details_data.org_phone = org_phone 
            except:
                try:
                    phone_pattern = re.compile(r"\d{3}[-.\s]?\d{3}[-.\s]?\d{4}")
                    org_phone = phone_pattern.findall(org_phone1)[0]
                    customer_details_data.org_phone = org_phone
                except:
                    phone_pattern = re.compile(".\d+.+\d+")
                    org_phone = phone_pattern.findall(org_phone1)[0]
                    customer_details_data.org_phone = org_phone
        except:
            try:
                org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Ship-to Address:")]//following::td[1]').text.split("Phone:")[1].split("\n")[0].strip()
                count_zero = 0
                for i in org_phone:
                    if i == '0':
                        count_zero +=1
                    else:
                        pass
                if count_zero >=9:
                    pass
                else:
                    customer_details_data.org_phone = org_phone
            except:
                try:
                    org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Bill-to Address:")]//following::td[1]').text.split("Phone:")[1].split("\n")[0].strip()
                    customer_details_data.org_phone = org_phone
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass
                                                      
        try:
            org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Info Contact")]//following::td[1]').text
            email_regex = re.compile(r"[\w\.-]+@[\w\.-]+")
            customer_details_data.org_email = email_regex.findall(org_email)[0]
        except:
            try:
                org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Ship-to Address:")]//following::td[1]').text.split("Email:")[1].split("\n")[0]
                email_regex = re.compile(r"[\w\.-]+@[\w\.-]+")
                org_email1 = email_regex.findall(org_email)[0]
                if org_email1.isalnum() or org_email1.isalpha():
                    customer_details_data.org_email = org_email1
                else:
                    pass
            except:
                try:
                    org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Bill-to Address:")]//following::td[1]').text.split("Email:")[1].split("\n")[0]
                    email_regex = re.compile(r"[\w\.-]+@[\w\.-]+")
                    customer_details_data.org_email = email_regex.findall(org_email)[0]
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass

        customer_details_data.org_country = 'US'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
                                                      
    try:
        lot_number = 1
        lot_text = notice_text.split("Item #")
        for single_record in lot_text[1:]:
            lot_title = single_record.split("Qty Unit")[0].split("\n")[2].strip()
            if len(lot_title) > 1 :
                lot_details_data = lot_details()
                lot_details_data.lot_title = lot_title
                lot_details_data.lot_number = lot_number
            
                try:
                    lot_quantity1 = single_record.split("Total Cost")[1].split('Manufacturer:')[0]
                    lot_quantity = re.findall("\d+.\d+",lot_quantity1)[0]
                    lot_details_data.lot_quantity = float(lot_quantity)
                except:
                    pass

                try:
                    lot_quantity_uom = single_record.split(lot_quantity)[1].split("\n")[0].strip()
                    if lot_quantity_uom != '#':
                        lot_details_data.lot_quantity_uom = lot_quantity_uom
                except:
                    pass
                lot_number += 1
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"File Attachments:")]//following::a'):
            attachments_data = attachments()

            attachments_data.file_name = single_record.text

            external_url = single_record.click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url= (str(file_dwn[0]))
            
            attachments_data.file_type = attachments_data.external_url.split(".")[-1]
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments)
page_details = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.njstart.gov/bso/view/search/external/advancedSearchBid.xhtml?openBids=true',"https://arbuy.arkansas.gov/bso/view/search/external/advancedSearchBid.xhtml?openBids=true","https://www.bidbuy.illinois.gov/bso/view/search/external/advancedSearchBid.xhtml?openBids=true",
    "https://nevadaepro.com/bso/view/search/external/advancedSearchBid.xhtml?openBids=true","https://www.commbuys.com/bso/view/search/external/advancedSearchBid.xhtml?openBids=true"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
                                                                                                             
        for page_no in range(1,10):#10
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="bidSearchResultsForm:bidResultId_data"]/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bidSearchResultsForm:bidResultId_data"]/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bidSearchResultsForm:bidResultId_data"]/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#bidSearchResultsForm\:bidResultId_paginator_bottom > span.ui-paginator-next.ui-state-default.ui-corner-all > span')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                time.sleep(10)
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="bidSearchResultsForm:bidResultId_data"]/tr'),page_check))
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