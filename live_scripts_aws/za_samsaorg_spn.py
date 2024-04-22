from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "za_samsaorg_spn"
log_config.log(SCRIPT_NAME)
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "za_samsaorg_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'za_samsaorg_spn'
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ZA'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'ZAR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y/%m/%d %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').get_attribute('href')
        fn.load_page(page_details,notice_data.notice_url,120)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try: 
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="ms-belltown-table"]/div[3]/div/div/div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in page_details_notice_text2: {}".format(type(e).__name__))
        pass
     
    try:
        publish_date = page_details.find_element(By.XPATH, "//a[contains(@href, 'Documents')]").text
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, "//*[contains(text(),'PART A')]//following::strong[1]|//th").text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_no = page_details.find_element(By.XPATH,"//*[contains(text(),'BID NUMBER')]//following::tr[1]/td[1]|(//*[contains(text(),'REF NUMBER')])[3]").text
        if ':' in notice_no:
            notice_data.notice_no = notice_no.split(':')[1].strip()
        else:
            notice_data.notice_no = notice_no
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'DESCRIPTION')]/following::td[1]").text
        if "LOCATION OF THE SAMSA HEAD OFFICE" in local_description:
            notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'DESCRIPTION')]/following::td[4]").text
            notice_data.notice_summary_english = notice_data.local_description
        else:
            notice_data.local_description = local_description
            notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    
    try:
        for single_record in page_details.find_elements(By.XPATH, "//a[contains(@href, 'Documents')]"):
            
            attachments_data = attachments()

            try:
                attachments_data.file_type = single_record.text.split('.')[-1].strip()
            except:
                pass
            
            attachments_data.file_name = single_record.text.split(attachments_data.file_type)[0].strip()
            
            attachments_data.external_url = single_record.get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)

    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        data = page_details.find_element(By.XPATH,'(//tr[@class="ms-rteTableOddRow-4"]|//tr[@class="ms-rteTableEvenRow-4"])[7]').text
        if data !='':
            customer_details_data = customer_details()
            customer_details_data.org_country = 'ZA'
            customer_details_data.org_language = 'EN'
            customer_details_data.org_name = "SOUTH AFRICAN MARITIME SAFETY AUTHORITY (SAMSA)"
            customer_details_data.org_parent_id = 7723936
            for single_record in page_details.find_elements(By.XPATH,'//tr[@class="ms-rteTableOddRow-4"]|//tr[@class="ms-rteTableEvenRow-4"]')[6:]:
            
                try:
                    contact_person = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                    if contact_person == "CONTACT PERSON":
                        customer_details_data.contact_person = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text

                    if customer_details_data.contact_person is None:
                        customer_details_data.contact_person = contact_person
                except:
                    pass
            
                try:
                    org_phone = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                    if org_phone == "TELEPHONE NUMBER":
                        customer_details_data.org_phone = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                except:
                    pass
                
                try:
                    org_email = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                    if org_email == "E-MAIL ADDRESS":
                        customer_details_data.org_email = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('/n')[0].strip()
                except:
                    pass
            
            try:
                org_phone = page_details.find_element(By.XPATH, '''//*[contains(text(),"Tel")]//following::td[1]''').text.strip()
                if org_phone.replace(' ','').isdigit():
                    customer_details_data.org_phone = org_phone
            except:
                pass

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '''(//*[contains(text(),"Email")])[2]//following::td[1]''').text
            except:
                pass

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '''//*[contains(text(),"LOCATION OF THE SAMSA HEAD OFFICE")]//following::td[4]|//*[contains(text(),"DELIVERY ADDRESS")]//following::td[1]''').text
            except:
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    try:
        clk_contact_person = page_details.find_element(By.XPATH,'//*[contains(text(),"CONTACT PERSON")][2]').text
        data = page_details.find_element(By.XPATH,'(//tr[@class="ms-rteTableOddRow-4"]|//tr[@class="ms-rteTableEvenRow-4"])[7]').text
        if data !='' and clk_contact_person !='':
            customer_details_data = customer_details()
            customer_details_data.org_country = 'ZA'
            customer_details_data.org_language = 'EN'
            customer_details_data.org_name = "SOUTH AFRICAN MARITIME SAFETY AUTHORITY (SAMSA)"
            customer_details_data.org_parent_id = 7723936
            for single_record in page_details.find_elements(By.XPATH,'//tr[@class="ms-rteTableOddRow-4"]|//tr[@class="ms-rteTableEvenRow-4"]')[6:]:

                try:
                    contact_person = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                    if contact_person == "CONTACT PERSON":
                        customer_details_data.contact_person = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                        if customer_details_data.contact_person is None:
                            customer_details_data.contact_person = contact_person
                except:
                    pass
            
                try:
                    org_phone = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                    if org_phone == "TELEPHONE NUMBER":
                        customer_details_data.org_phone = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                except:
                    pass
                
                try:
                    org_email = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                    if org_email == "E-MAIL ADDRESS":
                        customer_details_data.org_email = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.split('/n')[0].strip()
                except:
                    pass

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '''//*[contains(text(),"LOCATION OF THE SAMSA HEAD OFFICE")]//following::td[4]|//*[contains(text(),"DELIVERY ADDRESS")]//following::td[1]''').text
            except:
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        contact_person = page_details.find_element(By.XPATH, '((//*[contains(text(),"Tel")])[1]/preceding-sibling::div)[3]').text
        if contact_person != '':
            customer_details_data = customer_details()

            customer_details_data.contact_person = contact_person
            try:
                if customer_details_data.contact_person !='':
                    try:
                        customer_details_data.org_address = page_details.find_element(By.XPATH, '''//*[contains(text(),"LOCATION OF THE SAMSA HEAD OFFICE")]//following::td[4]|//*[contains(text(),"DELIVERY ADDRESS")]//following::td[1]''').text
                    except:
                        pass
                    customer_details_data.org_name = "SOUTH AFRICAN MARITIME SAFETY AUTHORITY (SAMSA)"
                    customer_details_data.org_parent_id = 7723936
                    try:
                        customer_details_data.org_phone = page_details.find_element(By.XPATH, '''(//*[contains(text(),"Tel")])[1]''').text.split('Tel')[1].split('\n')[0].strip()
                    except:
                        pass
                    try:
                        customer_details_data.org_email = page_details.find_element(By.XPATH, '''(//*[contains(text(),"Email")])[2]''').text.split('Email')[1].split('\n')[0].strip()
                    except:
                        pass
                    customer_details_data.org_country = 'ZA'
                    customer_details_data.org_language = 'EN'
            except:
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_deadline) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
    urls = ["https://www.samsa.org.za/Pages/Current-TendersBids.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url) 
        
        num = 1
        for page_no in range(1,3):
            page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'//*[@id="onetidDoclibViewTbl0"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="onetidDoclibViewTbl0"]/tbody/tr')))
            length = len(rows)
            
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="onetidDoclibViewTbl0"]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            try:   
                next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.XPATH,'(//*[@class="ms-bottompaging"]//a)['+str(num)+']')))
                page_main.execute_script("arguments[0].click();",next_page)
                num +=1
                logging.info("Next page")
                WebDriverWait(page_main, 80).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="onetidDoclibViewTbl0"]/tbody/tr'),page_check))
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
