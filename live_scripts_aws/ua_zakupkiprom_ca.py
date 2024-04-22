from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ua_zakupkiprom_ca"
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
import gec_common.Doc_Download_ingate as Doc_Download


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 20000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "ua_zakupkiprom_ca"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
    
    notice_data.main_language = 'UA'
    notice_data.currency = 'UAH'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'UA'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.notice_type = 7
    
    notice_data.procurement_method = 2
    notice_data.script_name = "ua_zakupkiprom_ca"
    
    notice_data.procurement_method = 2
        
    try:
        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.zkb-list__main-block > div.qa_title_item > a > span').text
        if len(local_title)< 5:
            return
        else:
            notice_data.local_title = local_title
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass   
    
    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, ' div.zkb-list__side-block > div.zkb-list__side-gap.qa_price').text
        if "без ПДВ" in est_amount:
            est_amount = re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount =float(est_amount.replace('.','').replace(',','').strip())
            notice_data.netbudgetlc =notice_data.est_amount
        else:
            est_amount = re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount =float(est_amount.replace('.','').replace(',','').strip())
            notice_data.grossbudgetlc =notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    notice_data.document_type_description = "Procurement plans"
    
    try:
        clk = tender_html_element.find_element(By.CSS_SELECTOR, "button.zkb-company-bubble.h-button-reset").click()
        time.sleep(5)
    except:
        pass
        
    try:
        contact_person = tender_html_element.find_element(By.CSS_SELECTOR, ' div.zkb-popup__body > div.h-mb-8').text
    except Exception as e:
        logging.info("Exception in contact_person: {}".format(type(e).__name__))
        pass
    
    
    try:
        org_email = tender_html_element.find_element(By.CSS_SELECTOR, ' div.zkb-popup__body > a:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in org_email: {}".format(type(e).__name__))
        pass
    
    try:
        org_phone = tender_html_element.find_element(By.CSS_SELECTOR, ' div.zkb-popup__body > a:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in org_phone: {}".format(type(e).__name__))
        pass
    
    try:
        close = tender_html_element.find_element(By.CSS_SELECTOR, "button.zkb-company-bubble.h-button-reset").click()
        time.sleep(5)
    except:
        pass
        
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.zkb-list__heading.qa_title_link').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -Basic Information
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, ' div.zkb-layout > main').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
        
    try:
        publish_date = page_details.find_element(By.XPATH, '''//*[contains(text(),"Дата підписання:")]//following::span[1]''').text
        try:
            publish_date = GoogleTranslator(source='ukrainian', target='en').translate(publish_date)
            publish_date1 = '2024'+' '+publish_date
            publish_date3 = re.findall('\d{4} \w+ \d+ \d+:\d+',publish_date1)[0]
            notice_data.publish_date = datetime.strptime(publish_date3,'%Y %B %d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                publish_date = GoogleTranslator(source='ukrainian', target='en').translate(publish_date)
                publish_date = re.findall('\w+ \d+ \d{4} \d+:\d+',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%B %d %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            except:
                publish_date = GoogleTranslator(source='ukrainian', target='en').translate(publish_date)
                publish_date = re.findall('\w+. \d+ \d{4} \d+:\d+',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%b. %d %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        tender_quantity = ''
        for single_record in page_details.find_elements(By.CSS_SELECTOR, ' section:nth-child(2) > table > tbody > tr')[1:]:
            tender_quantity += single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text
            tender_quantity += ','
        notice_data.tender_quantity = tender_quantity.rstrip(',')
    except Exception as e:
        logging.info("Exception in tender_quantity: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"ID контракту:")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    try:
        local_description = ''
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'p.h-mb-10.h-break-word'):
            local_description += single_record.text
            local_description += ' '
        notice_data.local_description = local_description.rstrip(' ')
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description[:4500]) 
    except:
        pass

     
    try:              
        customer_details_data = customer_details()
        # Onsite Field -Organization
        # Onsite Comment -None

        customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'div.zkb-layout > main').text.split("Інформація про замовника")[1].split("Назва:")[1].split("Код ЄДРПОУ:")[0].strip()

        
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '(//*[contains(text(),"Адреса:")])[2]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        try:
            org_website = page_details.find_element(By.XPATH, '(//*[contains(text(),"Веб сайт:")])[2]//following::span[1]').text
            if "Не вказано" in org_website:
                pass
            else:
                customer_details_data.org_website = org_website
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.contact_person = contact_person
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
    

        try:
            customer_details_data.org_email = org_email
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_phone = org_phone
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        
        customer_details_data.org_country = 'UA'
        customer_details_data.org_language = 'UA'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        class_title_at_source = ''
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.zkb-purchase-label__item.zkb-purchase-label_theme_light-blue.zkb-purchase-label_type_with_indent'):
            class_title_at_source_data = single_record.text
            class_title_at_source += re.split(": \d{8}-\d+", class_title_at_source_data)[1]
            class_title_at_source += ','
        notice_data.class_title_at_source = class_title_at_source.rstrip(',')
    except:
        pass

    
    try:
        class_codes_at_source = ''
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.zkb-purchase-label__item.zkb-purchase-label_theme_light-blue.zkb-purchase-label_type_with_indent'):
            class_codes_at_source_data = single_record.text
            class_codes_at_source += re.findall('\d{8}-\d+',class_codes_at_source_data)[0]
            class_codes_at_source += ','
        notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')
    except:
        pass
    
    notice_data.class_at_source = 'CPV'
    
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, ' div.zkb-purchase-label__item.zkb-purchase-label_theme_light-blue.zkb-purchase-label_type_with_indent'):
            cpv_code = single_record.text
            cpvs_data = cpvs()
            cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0]
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass
    
    try:
        cpv_at_source = ''
        for single_record in page_details.find_elements(By.CSS_SELECTOR, ' div.zkb-purchase-label__item.zkb-purchase-label_theme_light-blue.zkb-purchase-label_type_with_indent'):
            cpv_code = single_record.text
            cpv_at_source += re.findall('\d{8}',cpv_code)[0]
            cpv_at_source += ','
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    
    try:              
        lot_details_data = lot_details()
        # Onsite Field -Title
        # Onsite Comment -None
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_number = 1
        
        try:

            # Onsite Field -Supplier
            # Onsite Comment -None

            bidder_name = page_details.find_element(By.XPATH, '//*[@id="move-page-up"]/div[1]/main/div/div[2]/div/div[3]/div[2]/div[2]/span').text
            award_details_data = award_details()
            award_details_data.bidder_name = bidder_name
            award_details_data.address = page_details.find_element(By.XPATH, '(//*[contains(text(),"Адреса:")])[1]//following::span[1]').text
            # Onsite Field -Award date
            # Onsite Comment -None

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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tr.zkb-table-list__row.zkb-files.qa_file_list'):
            attachments_data = attachments()
            
            file_name = single_record.find_element(By.CSS_SELECTOR, ' div.zkb-files__name').text.split(".")[0].strip()
            if len(file_name)>1:
                attachments_data = attachments()
                attachments_data.file_name = file_name

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' div.zkb-files__name > a').get_attribute('href')

                try:
                    attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                except:
                    pass

                try:
                    attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, ' div.zkb-files__name').text.split(".")[-1].strip()
                except:
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
    
    
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d %H:%M:%S')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://zakupivli.pro/gov/contracts'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,500):#20
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/main/div/ul/li'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/main/div/ul/li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/main/div/ul/li')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_count == 50:
                        output_json_file.copyFinalJSONToServer(output_json_folder)
                        output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                        notice_count = 0
                        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                        
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/main/div/ul/li'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
        except:
            logging.info('No new record')
            break
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
