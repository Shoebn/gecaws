from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "th_kkuac_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "th_kkuac_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'th_kkuac_ca'
    
    notice_data.main_language = 'TH'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TH'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'THB'
    
    notice_data.procurement_method = 2
   
    notice_data.notice_type = 7
    
    notice_data.document_type_description = 'ประกาศผู้ชนะเสนอราคา/ได้รับคัดเลือก(Announcement of bidder/selected winners)'
    
    # Onsite Field -ชื่อประกาศ(Announcement name)
    # Onsite Comment -None
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -วันที่ประกาศ(announcement date)
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.text-right.hidden-xs").text
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -ชื่อประกาศ(Announcement name)
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -in page_details click on "//*[contains(text()," ประกาศผู้ชนะเสนอราคา/ได้รับคัดเลือก")]".we have to take data only from that table.
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#view-type-5 > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -ประกาศผู้ชนะเสนอราคา/ได้รับคัดเลือก >> เลขที่โครงการ(Announcement of bidder/selected winners >> project number)
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, '#section5 tbody > tr:nth-child(6) > td').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -ประกาศผู้ชนะเสนอราคา/ได้รับคัดเลือก >> งบประมาณ(Announcement of bidder/selected winners >> budget)
    # Onsite Comment -None
    try:
        notice_data.est_amount = float(re.findall('\d*', page_details.find_element(By.CSS_SELECTOR, '#section5 tbody > tr:nth-child(5) > td').text.replace(',',''))[0])
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
 
    try:
        customer_details_data = customer_details()
        customer_details_data.org_name = 'KHON KAEN UNIVERSITY'
        customer_details_data.org_parent_id = '7498885'
        customer_details_data.org_country = 'TH'
        customer_details_data.org_language = 'TH'
    # Onsite Field -ชื่อประกาศ	(Announcement name)
    # Onsite Comment -None

        try:
            org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div:nth-child(2)').text
            customer_details_data.org_address = GoogleTranslator(source='auto', target='en').translate(org_address)
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -ประกาศผู้ชนะเสนอราคา/ได้รับคัดเลือก >> ชื่อผู้ประกาศ(Announcement of bidder/selected winners >> Announcer name)
    # Onsite Comment -None

        try:
            contact_person = page_details.find_element(By.CSS_SELECTOR, '#section4 tbody > tr:nth-child(15) > td').text
            customer_details_data.contact_person = GoogleTranslator(source='auto', target='en').translate(contact_person)
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -ประกาศผู้ชนะเสนอราคา/ได้รับคัดเลือก >> หมายเลขโทรศัพท์(Announcement of bidder/selected winners >> phone number)
    # Onsite Comment -None

        try:
            org_phone = page_details.find_element(By.CSS_SELECTOR, '#section4 tbody > tr:nth-child(14) > td').text
            if 'ต่อ' in org_phone:
                customer_details_data.org_phone = org_phone.split('ต่อ')[0]
            else:
                customer_details_data.org_phone = org_phone
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
    
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
   
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1

        # Onsite Field -ชื่อประกาศ	(Announcement name)
        # Onsite Comment -None

        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = notice_data.notice_title

        try:
            award_details_data = award_details()

            # Onsite Field -ผู้ชนะเสนอราคา(bid winner)
            # Onsite Comment -None

            bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td.hidden-xs.text-left').text
            award_details_data.bidder_name = GoogleTranslator(source='auto', target='en').translate(bidder_name)
    
            # Onsite Field -รายชื่อผู้ชนะการเสนอราคา(List of bid winners)
            # Onsite Comment -None
            try:  
                award_details_data.grossawardvaluelc = float(re.findall('\d*', page_details.find_element(By.XPATH, '//*[contains(text(),"รายชื่อผู้ชนะการเสนอราคา")]//following::td[3]').text.replace(',',''))[0])
            except:
                try:            
                    award_details_data.grossawardvaluelc = float(re.findall('\d*', page_details.find_element(By.XPATH, '//*[@id="w10"]/table/tbody/tr/td[2]').text.replace(',',''))[0])
                except:
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
  
    try:              
        attachments_data = attachments()
        # Onsite Field -ประกาศผู้ชนะเสนอราคา/ได้รับคัดเลือก >> ไฟล์ประกาศ(Announcement of bidder/selected winners >> declaration file)
        # Onsite Comment -None

        file_name = page_details.find_element(By.CSS_SELECTOR, '#section5 table > tbody > tr > td > div > div.col-md-9').text.split('.')[0]
        if file_name.isalpha():
            attachments_data.file_name = GoogleTranslator(source='auto', target='en').translate(file_name)
        else:
            attachments_data.file_name = file_name
        attachments_data.file_description =attachments_data.file_name
        
        # Onsite Field -ประกาศผู้ชนะเสนอราคา/ได้รับคัดเลือก >> ไฟล์ประกาศ(Announcement of bidder/selected winners >> declaration file)
        # Onsite Comment -None

        try:
            attachments_data.file_size = page_details.find_element(By.CSS_SELECTOR, '#section5 table > tbody > tr > td > div > div.col-md-3').text
        except Exception as e:
            logging.info("Exception in file_size: {}".format(type(e).__name__))
            pass
    
        # Onsite Field -ประกาศผู้ชนะเสนอราคา/ได้รับคัดเลือก >> ไฟล์ประกาศ(Announcement of bidder/selected winners >> declaration file)
        # Onsite Comment -split file_type.eg., "ขอบเขตของงาน(TOR)และรายละเอียดคุณลักษณะเฉพาะ ครุภัณฑ์การศึกษา.pdf" here take only ".pdf" in file_type.

        try:
            attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, '#section5 table > tbody > tr > td > div > div.col-md-9').text.split('.')[-1]
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass
    
        # Onsite Field -ประกาศผู้ชนะเสนอราคา/ได้รับคัดเลือก >> ไฟล์ประกาศ(Announcement of bidder/selected winners >> declaration file)
        # Onsite Comment -None

        attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#section5 table > tbody > tr > td >div > div > a').get_attribute('href')
        
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://procurement.kku.ac.th/t/bidders"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,8):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="w1"]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="w1"]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="w1"]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="w1"]/table/tbody/tr'),page_check))
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
