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
from gec_common import functions as fn
import gec_common.Doc_Download
from selenium.webdriver.support.ui import Select


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_maryland_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'us_maryland_spn'
    

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'USD'
    

    notice_data.main_language = 'EN'
    

    notice_data.procurement_method = 2

    notice_data.notice_type = 7
    


    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        publish_date = re.findall(r'\d+/\d+/\d{4} \d+:\d+:\d+ [apAP][Mm]',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date, '%m/%d/%Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        cpv_codes = fn.CPV_mapping("assets/us_maryland_spn_cpv.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except:
        pass

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(8)").text
    except:
        pass
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3) a").get_attribute('href')
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        pass
    logging.info(notice_data.notice_url)
    
    try:
        deadline_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Due / Close Date (EST)")]//following::div[1]/div/input').get_attribute('value')
        try:
            deadline_date = re.findall(r'\w+ \d+ \d{4}  \d+:\d+[apAP][Mm]',deadline_date)[0]
        except:
            try:
                deadline_date = re.findall(r'\w+  \d+ \d{4}  \d+:\d+[apAP][Mm]',deadline_date)[0]
            except:
                try:
                    deadline_date = re.findall(r'\w+ \d+ \d{4} \d+:\d+[apAP][Mm]',deadline_date)[0]
                except:
                    pass
        notice_data.notice_deadline = datetime.strptime(deadline_date, '%b %d %Y %I:%M%p').strftime('%Y/%m/%d %H:%M:%S')
    except:
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Solicitation Summary")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass


    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Solicitation Summary")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.XPATH,'/html/body/form[1]/div[3]/div/main/div[2]/div[2]/div[3]/div/div[2]/table/tbody/tr/td/div/div[1]/div/div/div/table').get_attribute('outerHTML')
    except:  
        pass
        
    try:              
        customer_details_data = customer_details()
        
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(9)").text

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Officer / Buyer")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '(//*[contains(text(),"Email")])[2]//following::div[1]/div/input').get_attribute('value')
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#body_x_tabc_rfp_ext_prxrfp_ext_x_prxDoc_x_grid_grd > tbody > tr'):
            file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text

            for single_record1 in single_record.find_elements(By.CSS_SELECTOR, 'td:nth-child(3) ul li.li-file-upload.file_uploaded'):
                attachments_data = attachments()
                attachments_data.file_name = file_name
                attachments_data.external_url = single_record1.find_element(By.CSS_SELECTOR, 'a').get_attribute('href') 
                try:
                    attachments_data.file_type = single_record1.find_element(By.CSS_SELECTOR, 'a span').text.split('.')[-1]
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try: 
        clk=page_details.find_element(By.XPATH,"//li[@id='body_x_tabc_containerTab_partrfpitem_ext']").click()
        time.sleep(5)
        lot_number=1
        for single_record in page_details.find_elements(By.XPATH, '/html/body/form[1]/div[3]/div/main/div[2]/div[2]/div[3]/div/div[2]/table/tbody/tr/td/div/div[4]/div/div/div/table/tbody/tr[3]/td/div/div/div/div/div[2]/table/tbody/tr/td/div/div/div/div/div[1]/div/table/tbody/tr')[1:]:        
            lot_details_data = lot_details()
            lot_details_data.lot_number=lot_number
            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(3)').text
            except:
                pass

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(5)').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)


            try:
                lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            except:
                pass

            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(9)").text
            except:
                pass

            try:
                lot_details_data.lot_quantity = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(8)").text
            except:
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except:
        try:
            
            clk=page_details.find_element(By.XPATH,'//*[@id="body_x_tabc_containerTab_partrfpitem_fin_ext"]/span').click()
            time.sleep(5)

            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#body_x_tabc_rfpitem_fin_ext_prxrfpitem_fin_ext_x_grid_67192_x_grdItems_grd > tbody tr')[1:]:        
                lot_details_data = lot_details()
                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(3)').text
                except:
                    pass

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(5)').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)


                try:
                    lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
                    lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                except:
                    pass

                try:
                    lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(9)").text
                except:
                    pass

                try:
                    lot_details_data.lot_quantity = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(8)").text
                except:
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
  
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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
    urls = ["https://emma.maryland.gov/page.aspx/en/rfp/request_browse_public"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        for page_no in range(2,10):
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
                next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="body_x_grid_grd"]/tbody/tr'),page_check))
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
