from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "us_alabamabuys_spn"
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


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_alabamabuys_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'us_alabamabuys_spn'
    notice_data.main_language = 'EN'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'USD'
    notice_data.procurement_method = 2
    

    notice_type = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(9)').text
    if 'Cancellation' in notice_type:
        notice_data.notice_type = 16
    else:
        notice_data.notice_type = 4

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        notice_data.notice_title = notice_data.local_title
        
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.strip()  
        if len(document_type_description)>3:
            notice_data.document_type_description = document_type_description
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text.strip() 
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.class_title_at_source = notice_data.category
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass    
     
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")   
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url 
   
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 
    except:
        try:
            notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'div.panel-content div#content').get_attribute("outerHTML")     
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass  
        
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.panel-content div#content').get_attribute("outerHTML")     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass  

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except:
        try:
            notice_data.notice_no = notice_data.notice_url.split('/')[-1]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass  
        
    try:
        publish_date = page_details.find_element(By.XPATH, '(//*[contains(text(),"Begin")]//following::span[1])[2]').text
        publish_date  = publish_date .split('(')[0]
        publish_date  = re.findall('\d+/\d+/\d+ \d+:\d+:\d+ [apAP][mM]', publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass    
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
        
    try:
        notice_deadline = page_details.find_element(By.XPATH, '(//*[contains(text(),"End")]//following::span[1])[2]').text
        notice_deadline  = notice_deadline .split('(')[0]
        notice_deadline  = re.findall('\d+/\d+/\d+ \d+:\d+:\d+ [apAP][mM]', notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass    
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Summary")]//following::p[1]').text
        notice_data.notice_summary_english = notice_data.local_description
    except:
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Summary")]//following::div[1]').text   
            notice_data.notice_summary_english = notice_data.local_description       
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass      
    try:
        customer_details_data = customer_details()
        customer_details_data.org_country = 'AZ'
        customer_details_data.org_language = 'EN'

        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(10)').text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass          
        
        try:
            firstname = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(11)').text
            lastname = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(12)').text
            customer_details_data.contact_person = firstname+' '+lastname
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass               
            
        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Officer Phone")]//following::p[1]').text  
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass              

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Officer Email")]//following::p[1]').text  
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass       
            
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass        
    
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR,'#body_x_tabc_rfp_ext_prxrfp_ext_x_proxy_rfp_201102185352_x_grid_grd > tbody > tr'):  

            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text
            try:
                file_type = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(3)').text
                attachments_data.file_type = file_type.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass        
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR,'div:nth-child(3) > div > ul > li > div > a').get_attribute("href")

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass     
    
    try:
        View_Quotation_Form_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"View Quotation Form")]')))  
        page_details.execute_script("arguments[0].click();",View_Quotation_Form_click)
        logging.info("View_Quotation_Form_click")
        time.sleep(10)
    except Exception as e:
        logging.info("Exception in View_Quotation_Form_click: {}".format(type(e).__name__)) 
        pass       
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.panel-content div#content').get_attribute("outerHTML")     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass  
    
    try:
        page_details.find_element(By.XPATH,'//*[@id="body_x_tabc_rfpitem_ext_prxrfpitem_ext_x_grid_26666_x_grdItems_grd"]/tbody/tr').text
        for single_record in page_details.find_elements(By.XPATH,'//*[@id="body_x_tabc_rfpitem_ext_prxrfpitem_ext_x_grid_26666_x_grdItems_grd"]/tbody/tr')[1:]:  

            lot_details_data = lot_details()
            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.XPATH,'td[3]').text
                lot_details_data.lot_number = int(lot_details_data.lot_actual_number)
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__)) 
                pass       

            lot_details_data.lot_title = single_record.find_element(By.XPATH,'td[6]').text

            try:
                lot_description = single_record.find_element(By.XPATH,'td[4]').text
                if len(lot_description)>4:
                    lot_details_data.lot_description = lot_description
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__)) 
                pass    

            try:
                lot_quantity = single_record.find_element(By.XPATH,'td[11]').text
                lot_details_data.lot_quantity = float(lot_quantity)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__)) 
                pass    

            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.XPATH,'td[12]').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__)) 
                pass    
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)  
    except:
        try:
            for single_record in page_details.find_elements(By.XPATH,'/html/body/form[1]/div[3]/div/main/div[2]/div[2]/div[4]/div/div[2]/table/tbody/tr/td/div/div[2]/div/div/div/table/tbody/tr[3]/td/div/div/div/div/div[2]/table/tbody/tr/td/div/div/div/div/div[1]/div/table/tbody/tr')[1:]:  

                lot_details_data = lot_details()
                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.XPATH,'td[3]').text
                    lot_details_data.lot_number = int(lot_details_data.lot_actual_number)
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__)) 
                    pass       

                lot_details_data.lot_title = single_record.find_element(By.XPATH,'td[5]').text

                try:
                    lot_description = single_record.find_element(By.XPATH,'td[6]').text
                    if len(lot_description)>4:
                        lot_details_data.lot_description = lot_description
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__)) 
                    pass    

                try:
                    lot_quantity = single_record.find_element(By.XPATH,'td[9]').text
                    lot_details_data.lot_quantity = float(lot_quantity)
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__)) 
                    pass    

                try:
                    lot_details_data.lot_quantity_uom = single_record.find_element(By.XPATH,'td[10]').text
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__)) 
                    pass    
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)

                try:
                    lot_next_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,"//i[contains(@class,'icon light fa-angle-right')]")))  
                    page_details.execute_script("arguments[0].click();",lot_next_click)
                    time.sleep(3)
                    logging.info("lot_next_click")

                    try:
                        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.panel-content div#content').get_attribute("outerHTML")     
                    except Exception as e:
                        logging.info("Exception in notice_text: {}".format(type(e).__name__))
                        pass  

                    for single_record in page_details.find_elements(By.XPATH,'/html/body/form[1]/div[3]/div/main/div[2]/div[2]/div[4]/div/div[2]/table/tbody/tr/td/div/div[2]/div/div/div/table/tbody/tr[3]/td/div/div/div/div/div[2]/table/tbody/tr/td/div/div/div/div/div[1]/div/table/tbody/tr')[1:]:  

                        lot_details_data = lot_details()

                        try:
                            lot_details_data.lot_actual_number = single_record.find_element(By.XPATH,'td[3]').text
                            lot_details_data.lot_number = int(lot_details_data.lot_actual_number)
                        except Exception as e:
                            logging.info("Exception in lot_actual_number: {}".format(type(e).__name__)) 
                            pass       

                        lot_details_data.lot_title = single_record.find_element(By.XPATH,'td[5]').text

                        try:
                            lot_description = single_record.find_element(By.XPATH,'td[6]').text
                            if len(lot_description)>4:
                                lot_details_data.lot_description = lot_description
                        except Exception as e:
                            logging.info("Exception in lot_description: {}".format(type(e).__name__)) 
                            pass    

                        try:
                            lot_quantity = single_record.find_element(By.XPATH,'td[9]').text
                            lot_details_data.lot_quantity = float(lot_quantity)
                        except Exception as e:
                            logging.info("Exception in lot_description: {}".format(type(e).__name__)) 
                            pass    

                        try:
                            lot_details_data.lot_quantity_uom = single_record.find_element(By.XPATH,'td[10]').text
                        except Exception as e:
                            logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__)) 
                            pass    

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                except Exception as e:
                    logging.info("Exception in lot_next_click: {}".format(type(e).__name__)) 
                    pass  
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) + str(notice_data.notice_url)  
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
    urls = ["https://alabamabuys.gov/page.aspx/en/rfp/request_browse_public"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
                
        for page_no in range(1,14):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="body_x_grid_grd"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="body_x_grid_grd"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="body_x_grid_grd"]/tbody/tr')))[records]
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
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#body_x_grid_PagerBtnNextPage > i")))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="body_x_grid_grd"]/tbody/tr'),page_check))
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