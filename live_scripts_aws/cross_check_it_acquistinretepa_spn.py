
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cross_check_it_acquistinretepa_spn"
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
SCRIPT_NAME = "cross_check_it_acquistinretepa_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "cross_check_output"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = cross_check_output()
    
    notice_data.script_name = 'it_acquistinretepa_spn'
    notice_data.notice_type = 4

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.stato.borderElenco.nopadding.col-sm-1.ng-scope > div > p').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass


    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p > a').get_attribute("href") 
    except:
        pass
    
    try:
        fn.load_page(page_details,notice_data.notice_url,180)
        logging.info(notice_data.notice_url)

        try:
            popup_click = WebDriverWait(page_details, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.modal-title.semibold-24.col-sm-12.nopadding > div > div.col-sm-1.nopadding.voffset1 > button')))
            page_details.execute_script("arguments[0].click();",popup_click)
            time.sleep(5)
        except:
            pass
        
        try:
            notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, 'div.titoloiniziativa > h1').text
        except Exception as e:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' p.regular-18.ellipsis.responsiveText18.ng-binding.ng-scope').text
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        try:
            publish_date = page_details.find_element(By.XPATH, '(//*[contains(text(),"Data di pubblicazione del bando")])[2]//following::p[1]').text
            publish_date1,time1 = publish_date.split('\n')
            publish_date= f'{publish_date1} {time1}'
            publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except:
            try:
                publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'div.stato.borderElenco.nopadding.col-sm-2 > div > div > font > font').text
                publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
                publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.publish_date)
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

        try:
            notice_deadline = page_details.find_element(By.XPATH, '(//*[contains(text(),"ultimo ricezione offerte")]//following::div/div/div/div[2]/p)[3]').text
            notice_deadline1,time1 = notice_deadline.split('\n')
            notice_deadline= f'{notice_deadline1} {time1}'
            notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, 'div.stato.nopadding.noBorderElenco.text-center.col-sm-2 > div > div > font > font').text
                notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
                try:
                    notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
                    notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    notice_deadline = re.findall('\w+ \d+ \d{4}',notice_deadline)[0]
                    notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d %Y').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.notice_deadline)
            except Exception as e:
                logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
                pass
            
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass

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
    urls = ["https://www.acquistinretepa.it/opencms/opencms/vetrina_bandi.html?filter=AB#!#post_call_position"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            clk=page_main.find_element(By.XPATH,'//*[@id="cookie_accept"]').click()
            time.sleep(5)
        except:
            pass
        try:
            clk=page_main.find_element(By.CSS_SELECTOR,'#strumento_AB')
            page_main.execute_script("arguments[0].click();",clk)
            time.sleep(10)
        except:
            pass
        
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#page-complete > div > div.row > div.col-xs-12.nopadding.hidden-xs.ng-scope > div.col-sm-12.col-lg-9.col-xs-12.nopadding > div:nth-child(3) > div > div'))).text
        
        for page_no in range(2,50):#50
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#page-complete > div > div.row > div.col-xs-12.nopadding.hidden-xs.ng-scope > div.col-sm-12.col-lg-9.col-xs-12.nopadding > div:nth-child(3) > div > div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#page-complete > div > div.row > div.col-xs-12.nopadding.hidden-xs.ng-scope > div.col-sm-12.col-lg-9.col-xs-12.nopadding > div:nth-child(3) > div > div')))
            length = len(rows)                                                                              
            for records in range(0,length-3): # length-3                                                              
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#page-complete > div > div.row > div.col-xs-12.nopadding.hidden-xs.ng-scope > div.col-sm-12.col-lg-9.col-xs-12.nopadding > div:nth-child(3) > div > div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#page-complete > div > div.row > div.col-xs-12.nopadding.hidden-xs.ng-scope > div.col-sm-12.col-lg-9.col-xs-12.nopadding > div:nth-child(3) > div > div'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Done cross checked total notice which has to be downloaded {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)    
