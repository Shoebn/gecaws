#check comments for additional changes
#1)for bidder name
# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []

from gec_common.gecclass import *
import logging
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
import functions as fn
from functions import ET
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cn_gzswbc_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'cn_gzswbc_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'ZH'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'CNY'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.text > a > span > span').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split notice_no from title.

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.text > a > span > span').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split notice_no from notice_url.

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.text > a').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.time").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.text > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'section.list-section').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -“六、代理服务收费标准及金额：=6. Agency service charging standards and amounts:” >>  “收费金额：=Amount charged:”
    # Onsite Comment -1.split after “收费金额：=Amount charged:”.		2.ref_url:"http://www.gzswbc.com/winBid/20231108/906842094084030464.html".

    try:
        notice_data.document_cost = page_details.find_element(By.CSS_SELECTOR, 'section.list-section').text
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -“成交金额：=Transaction amount:”
    # Onsite Comment -1.split after “成交金额：=Transaction amount:”		2.ref_url:”http://www.gzswbc.com/winBid/20231103/905132143733112832.html”.

    try:
        notice_data.est_amount = page_details.find_element(By.CSS_SELECTOR, 'section.list-section').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -“成交金额：=Transaction amount:”
    # Onsite Comment -1.split after “成交金额：=Transaction amount:”		2.ref_url:”http://www.gzswbc.com/winBid/20231103/905132143733112832.html”.

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.CSS_SELECTOR, 'section.list-section').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in None.find_elements(By.None, 'None'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'CN'
            customer_details_data.org_language = 'ZH'
            customer_details_data.org_name = 'Guangzhou Shunwei Tendering and Procurement Co., Ltd.'
            customer_details_data.org_parent_id = '7785927'
            customer_details_data.org_address = 'Rooms B501-B505 and B512-B525, No. 205, Huanshi Middle Road, Yuexiu District, Guangzhou City, Guangdong Province'
            customer_details_data.org_phone = '020-83592216-819'
            customer_details_data.org_email = 'gzswbc08@163.com'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    


#format-1 for lot_details.    
#ref_url:"http://www.gzswbc.com/winBid/20231108/906842094084030464.html"
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'section.list-section'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.text > a > span > span').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'section.list-section'):
                    award_details_data = award_details()
		
                    # Onsite Field -None
                    # Onsite Comment -split after "三、成交信息=3. Bid winning"   >>   "供应商名称：=Name of the winning supplier for Procurement Package 1:"

                    award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, 'section.list-section').text
			
                    # Onsite Field -None
                    # Onsite Comment -split after "三、成交信息=3. Bid winning"   >> "供应商地址：=Purchasing package 1 supplier address:"

                    award_details_data.address = page_details.find_element(By.CSS_SELECTOR, 'section.list-section').text
			
                    # Onsite Field -None
                    # Onsite Comment -split after "三、成交信息=3. Bid winning"   >>  "成交金额：=Winning bid amount for procurement package 1:"

                    award_details_data.grossawardvaluelc = page_details.find_element(By.CSS_SELECTOR, 'section.list-section').text
			
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



#format-2 for lot_details.
#ref_url:"http://www.gzswbc.com/winBid/20231103/905132143733112832.html"
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'section.list-section'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.text > a > span > span').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'section.list-section'):
                    award_details_data = award_details()
		
                    # Onsite Field -None
                    # Onsite Comment -1."div.text-part-text > table:nth-child(18) > tbody > tr:nth-child(2) > td" in this field "通过=pass" is written then pass bidder_name from “div.text-part-text > table:nth-child(18) > tbody > tr:nth-child(1) > td” from this fields

                    award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, 'div.text-part-text > table:nth-child(18) > tbody > tr:nth-child(1) > td').text

			
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
    


# Onsite Field -None
# Onsite Comment -format-3)ref_url:"http://www.gzswbc.com/winBid/20231109/907344871302365184.html"

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.modal-body > div:nth-child(5)'):
            lot_details_data = lot_details()


        # Onsite Field -"品目号=Item number"
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'div.text-part-text > table:nth-child(7) > tbody > tr > td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass


        # Onsite Field -"采购标的=Purchasing object"
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div.text-part-text > table:nth-child(7) > tbody > tr > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass



        # Onsite Field -"规格型号=Specifications and models"
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = page_details.find_element(By.CSS_SELECTOR, 'div.text-part-text > table:nth-child(7) > tbody > tr > td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass


        # Onsite Field -"数量（单位 =Quantity (unit)"
        # Onsite Comment -1.here "1.00(台)" take "1.00" in lot_quantity.

            try:
                lot_details_data.lot_quantity = page_details.find_element(By.CSS_SELECTOR, 'div.text-part-text > table:nth-child(7) > tbody > tr > td:nth-child(6)').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass



        # Onsite Field -"数量（单位 =Quantity (unit)"
        # Onsite Comment -1.here "1.00(台)" take "台" in lot_quantity_uom.

            try:
                lot_details_data.lot_quantity_uom = page_details.find_element(By.CSS_SELECTOR, 'div.text-part-text > table:nth-child(7) > tbody > tr > td:nth-child(6)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass

        # Onsite Field -"总价(元)=Total price (yuan)"
        # Onsite Comment -

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, 'div.text-part-text > table:nth-child(7) > tbody > tr > td:nth-child(8)').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
	
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["http://www.gzswbc.com/winBid/index.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="content-ul"]/li'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="content-ul"]/li')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="content-ul"]/li')))[records]
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
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="content-ul"]/li'),page_check))
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