from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "om_etendering_amd"
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
SCRIPT_NAME = "om_etendering_amd"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'om_etendering_amd'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'OM'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'OMR'
    notice_data.main_language = 'AR'
    notice_data.notice_type = 16
    
    try:
        notice_data.procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        if 'محلية' in notice_data.procurement_method:
            notice_data.procurement_method = 0
        elif 'عالمية' in notice_data.procurement_method:
            notice_data.procurement_method = 1
        else:
            notice_data.procurement_method = 2
    except:
        pass
        
    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_contract_type  = GoogleTranslator(source='auto', target='en').translate(notice_data.contract_type_actual)
        if 'Business quality' in notice_contract_type or 'Supplies and services - old' in notice_contract_type or 'Urban contracting and maintenance' in notice_contract_type or 'Information technology services' in notice_contract_type or 'Contracting - old' in notice_contract_type or 'Electromechanical, communications and maintenance contracting' in notice_contract_type or 'Ports, roads, bridges, railways, dams and maintenance contracting' in notice_contract_type or 'Pipeline networks and well drilling contracting' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Consulting work - old' in notice_contract_type or 'Training Works - Old' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'Supplies' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Consulting offices' in notice_contract_type:
            notice_data.notice_contract_type = 'Consultancy'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try: 
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(11)  a:nth-child(1)').get_attribute('onclick').split("('")[1].split("')")[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text

    try:
        notice_url = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"td:nth-child(11) > a:nth-child(1)")))
        page_main.execute_script("arguments[0].click();",notice_url)
        time.sleep(10)
        page_main.switch_to.window(page_main.window_handles[1])
        time.sleep(10)
        notice_url1 = page_main.current_url
        notice_data.notice_url = notice_url1
 
        try:
            notice_data.local_title = page_main.find_element(By.XPATH, '//*[contains(text(),"إسم المناقصة  باللغة العربية :")]//following::td[1]').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))

        
        try:
            publish_date = page_main.find_element(By.XPATH, '//*[contains(text(),"تاريخ طرح المناقصة :")]//following::td[1]').text
            notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
        
        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return
        
        try:
            notice_deadline = page_main.find_element(By.XPATH, '//*[contains(text(),"اخر موعد لتقديم العطاءات")]//following::td[1]').text
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass

        
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'OM'
            customer_details_data.org_language = 'AR'
            
            customer_details_data.org_name = org_name
            try:
                customer_details_data.org_address = page_main.find_element(By.XPATH,'//*[contains(text(),"الولايات :")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__)) 
                pass
                
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        
        try:
            document_opening_time = page_main.find_element(By.XPATH,'//*[contains(text(),"فتح العطاء المالي")]//following::td[1]').text
            document_opening_time = re.findall('\d+-\d+-\d{4}',document_opening_time)[0]
            notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%m-%Y').strftime('%Y-%m-%d')
            logging.info(notice_data.document_opening_time)
        except Exception as e:
            logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
            pass
    
        try:
            document_purchase_start_time = page_main.find_element(By.XPATH,'//*[contains(text(),"تاريخ بدء بيع مستند المناقصة")]//following::td[1]').text
            document_purchase_start_time = re.findall('\d+-\d+-\d{4}',document_purchase_start_time)[0]
            notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d-%m-%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Sale Close On
    # Onsite Comment -None

        try:
            document_purchase_end_time = page_main.find_element(By.XPATH,'//*[contains(text(),"تاريخ نهاية بيع مستند المناقصة")]//following::td[1]').text
            document_purchase_end_time = re.findall('\d+-\d+-\d{4}',document_purchase_end_time)[0]
            notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d-%m-%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
            pass

        try:
            notice_data.document_fee = page_main.find_element(By.XPATH,'//*[contains(text(),"رسوم المناقصه : ")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in document_fee: {}".format(type(e).__name__))
            pass

        try:
            notice_data.earnest_money_deposit = page_main.find_element(By.XPATH,'//*[contains(text(),"قيمة الضمان البنكي :")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
            pass

        
        try:
            notice_text = page_main.find_element(By.XPATH,'/html/body/form/div[2]/table').get_attribute('outerHTML')
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass

        try:
            clk=page_main.find_element(By.XPATH,'//*[contains(text(),"ملخص نطاق العمل ")]//following::td[1]/a').click()
            time.sleep(5)
        except:
            pass
        
        try:
            notice_data.local_description=page_main.find_element(By.XPATH,'/html/body/form/div/div[4]/table/tbody/tr/td').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
            time.sleep(5)
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass            
    
        try:
            try:
                clk=page_main.find_element(By.XPATH,"//input[@class='button small green']").click()
                time.sleep(5)
            except:
                clk=page_main.find_element(By.CSS_SELECTOR,"input.Primary-btn").click()
                time.sleep(5)
        except:
            pass
        
        
        try:
            page_main.close()
            page_main.switch_to.window(page_main.window_handles[0])
            time.sleep(5)
        except:
            pass
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
    
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'(//tr[@class="even gradeA"]|//tr[@class="odd gradeA"])[4]'))).text

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += notice_text
        notice_data.notice_text += notice_data.local_description
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass            
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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
    urls = ["https://etendering.tenderboard.gov.om/product/publicDash?viewFlag=InProcessTenders"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
#         clk=page_main.find_element(By.XPATH,'//*[@id="header"]/div[5]/div/div[1]/div[2]/div/table/tbody/tr[1]/td/a[4]/b').click()
#         time.sleep(20)
        
        try:
            for page_no in range(2,5): 
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'(//tr[@class="even gradeA"]|//tr[@class="odd gradeA"])[4]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//tr[@class="even gradeA"]|//tr[@class="odd gradeA"]')))
                length = len(rows)                                                                              
                for records in range(3,length-2):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//tr[@class="even gradeA"]|//tr[@class="odd gradeA"]')))[records]
                    extract_and_save_notice(tender_html_element)
                    
                    if notice_count >= MAX_NOTICES:
                        break


                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break


                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    page_check2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'(//tr[@class="even gradeA"]|//tr[@class="odd gradeA"])[4]'))).text
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'(//tr[@class="even gradeA"]|//tr[@class="odd gradeA"])[4]'),page_check2))
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