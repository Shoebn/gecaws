from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cn_cnbidding_ca"
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
import gec_common.Doc_Download
from selenium.webdriver.support.ui import Select


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cn_cnbidding_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'cn_cnbidding_ca'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'CNY'

    notice_data.main_language = 'ZH'

    notice_data.procurement_method = 2

    notice_data.notice_type = 7

    try:
        notice_data.document_type_description = '中标公告'
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        document_opening_time1 = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
        document_opening_time = re.findall(r'\d{4}-\d+-\d+',document_opening_time1)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time, '%Y-%m-%d').strftime('%Y-%m-%d')
    except:
        pass
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        publish_date = re.findall(r'\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date, '%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(1) a").get_attribute('href')
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        pass
    
    fn.load_page(page_details,notice_data.notice_url,80)

    
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, "//*[contains(text(),'招标编号：')]//parent::li").text.split('招标编号：')[1]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    
    
    try:              
        customer_details_data = customer_details()
        
        customer_details_data.org_name = org_name

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"代理机构地址：")]//parent::span').text.split('代理机构地址：')[1].split('\n')[0]
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '/html/body/div[7]/div[1]/div/div[2]').text.split('联系人（业务）：')[1].split('\n')[0]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '/html/body/div[7]/div[1]/div/div[2]').text.split('Emai：')[1].split('\n')[0]
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '/html/body/div[7]/div[1]/div/div[2]').text.split('联系电话：')[1].split('\n')[0]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        customer_details_data.org_country = 'CN'
        customer_details_data.org_language = 'ZH'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


    try:
        lot_details_data = lot_details() 
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = notice_data.notice_title

        award_details_data = award_details()
        award_details_data.bidder_name =  page_details.find_element(By.XPATH, '//*[contains(text(),"最终中标商")]//parent::li').text.split('最终中标商：')[1]
        try:
            award_details_data.address = page_details.find_element(By.XPATH, '/html/body/div[7]/div[1]/div/div[2]').text.split('供应商地址：')[1].split('\n')[0]
        except:
            pass
        try:
            award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"评标结果公示日期：")]//parent::li').text.split('评标结果公示日期：')[1]
            award_details_data.award_date = datetime.strptime(award_date, '%Y-%m-%d').strftime('%Y/%m/%d')
        except:
            pass


        award_details_data.award_details_cleanup()
        lot_details_data.award_details.append(award_details_data)
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except:
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.XPATH, '/html/body/div[7]/div[1]/div/div[2]').get_attribute('outerHTML')
    except:    
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
          
    detail_url = "http://www.cnbidding.com/user/login.php "
    fn.load_page(page_details, detail_url, 50)
    user_name = page_details.find_element(By.XPATH,'//*[@id="UserName"]').send_keys('akanksha3')
    password = page_details.find_element(By.CSS_SELECTOR,'#loginform > ul > li:nth-child(2) > input').send_keys('Ak@123456')
    clk=page_details.find_element(By.CSS_SELECTOR,'#zt')
    page_details.execute_script("arguments[0].click();",clk)
    time.sleep(5)
    
    login_btn=page_details.find_element(By.XPATH,'//*[@id="loginbt"]')
    page_details.execute_script("arguments[0].click();",login_btn)
    time.sleep(5)

    url= "http://www.cnbidding.com/successbid/search.php"
    fn.load_page(page_main, url, 50)
    logging.info('----------------------------------')
    logging.info(url)
    try:
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div:nth-child(7) > div.fl.sidebar_w > div > div.table_1 > table > tbody tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div:nth-child(7) > div.fl.sidebar_w > div > div.table_1 > table > tbody tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div:nth-child(7) > div.fl.sidebar_w > div > div.table_1 > table > tbody tr')))[records]
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
                next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'body > div:nth-child(7) > div.fl.sidebar_w > div > div.table_1 > table > tbody tr'),page_check))
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
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
