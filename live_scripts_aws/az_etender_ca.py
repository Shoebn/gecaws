from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "az_etender_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "az_etender_ca"
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
    notice_data.script_name = 'az_etender_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'AZ'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AZ'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'AZN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7


#after opening the url select "Tamamlanmış=Complete" in given selector "span.select2-selection__rendered".

    
    # Onsite Field -Satınalma predmeti
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='az', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    # Onsite Field -Yekunlaşma tarixi
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(6) > app-tooltip > div:nth-child(2) > p ").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)  a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
#     # Onsite Field -None
#     # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'app-competition-detail > main').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
#     # Onsite Field -Müsabiqənin nömrəsi:
#     # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Müsabiqənin nömrəsi:")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
             
            # Onsite Field -ÜSL kod (kateqoriya):
            # Onsite Comment -1.take only number.

    try:
        cpvs_data = cpvs()
        cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"ÜSL kod (kateqoriya):")]//following::div[1]').text
        cpv_regex1 = re.compile(r'\d{8}')
        cpv_code = cpv_regex1.findall(cpv_code)
        for cpv in cpv_code:
            cpvs_data.cpv_code =cpv
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'AZ'
        customer_details_data.org_language = 'AZ'
    # #         # Onsite Field -Satınalan təşkilatın adı
    # #         # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div > div.text > app-tooltip > div:nth-child(2) > p').text
    # #         # Onsite Field -Satınalan təşkilatın VÖEN-i:
    # #         # Onsite Comment -None

        try:
            customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Satınalan təşkilatın VÖEN-i:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
            pass

    # #         # Onsite Field -None
    # #         # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Satınalan təşkilatın ünvanı:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # #         # Onsite Field -None
    # #         # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'section.section__6 > div.container > div:nth-child(2) > div:nth-child(1)').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # #         # Onsite Field -None
    # #         # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'section.section__6 > div.container > div:nth-child(2) > div:nth-child(3)').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # #         # Onsite Field -None
    # #         # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'section.section__6 > div.container > div:nth-child(2) > div:nth-child(4)').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    try:
        if 'bal' in  page_details.find_element(By.CSS_SELECTOR, 'app-competition-detail > main').text:
            try:              
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'section.section__5'):
                    tender_criteria_data = tender_criteria()
                # Onsite Field -None
                # Onsite Comment -1.here "Qiymət təklifi: 80 bal" take only "Qiymət təklifi" in title.

                    tender_criteria_data.tender_criteria_title = single_record.find_element(By.CSS_SELECTOR, 'div.inner__page__mini__title.mb-8.mt-16').text.split(':')[0]
                    if 'Qiymət' in tender_criteria_data.tender_criteria_title:
                        tender_criteria_data.tender_criteria_title = 'price'
                        tender_criteria_data.tender_is_price_related = True
                    if 'Texniki' in tender_criteria_data.tender_criteria_title:
                        tender_criteria_data.tender_criteria_title = 'Technical'
                
                # Onsite Field -None
                # Onsite Comment -1.here "Qiymət təklifi: 80 bal" take only "80" in weight.

                    try:
                        tender_criteria_data.tender_criteria_weight =int(single_record.find_element(By.CSS_SELECTOR, 'div.inner__page__mini__title.mb-8.mt-16').text.split(':')[1].split('bal')[0])
                    except Exception as e:
                        logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                        pass

                    tender_criteria_data.tender_criteria_cleanup()
                    notice_data.tender_criteria.append(tender_criteria_data)
            except Exception as e:
                logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
                pass
    except:
        pass
    
    try: 
        lot=page_details.find_element(By.CSS_SELECTOR, 'body > app-root > app-competition-detail > main').text
        if 'Hamısına bax' not in lot:
            
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > app-root > app-competition-detail > main > section.section__2 > div > table > tbody > tr'):            
                lot_details_data = lot_details()
    #         # Onsite Field -№
    #         # Onsite Comment -None

                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1)').text
                    lot_details_data.lot_number = int(single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1)')).text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

    #         # Onsite Field -Başlıq
    #         # Onsite Comment -None

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                lot_details_data.lot_title_english = GoogleTranslator(source='az', target='en').translate(lot_details_data.lot_title)
               

    #         # Onsite Field -Açıqlama
    #         # Onsite Comment -None

                try:
                    lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(3) > app-tooltip > div:nth-child(2) > p').text
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

    #         # Onsite Field -Miqdar
    #         # Onsite Comment -None

                try:
                    lot_details_data.lot_quantity = page_details.find_element(By.CSS_SELECTOR, ' td:nth-child(4)').text
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

    #         # Onsite Field -Ölçü vahidi
    #         # Onsite Comment -None

                try:
                    lot_details_data.lot_quantity_uom = page_details.find_element(By.CSS_SELECTOR, ' td:nth-child(6)').text
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

    #         # Onsite Field -None
    #         # Onsite Comment -None

                try:
                    award_details_data = award_details()

                    # Onsite Field -None
                    # Onsite Comment -None

                    award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(4) > app-tooltip > div.tooltip > p').text
                    # Onsite Field -Təklifin qiyməti
                    # Onsite Comment -None

                    award_details_data.grossawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > app-tooltip > p').text.split(' AZN')[0]
                    award_details_data.grossawardvaluelc =float(award_details_data.grossawardvaluelc.replace('.','').replace(',','.'))

                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)

        else:
            url_1 = notice_data.notice_url.split("detail/")[1].strip()  
            url1 ="https://etender.gov.az/main/competition/products/"+str(url_1)
            fn.load_page(page_details1,url1,90)
            time.sleep(10)
            
            for single_record1 in page_details1.find_elements(By.CSS_SELECTOR, 'body > app-root > app-competition-product > main > section > div > table > tbody > tr'):
                lot_details_data = lot_details()
        #         # Onsite Field -№
        #         # Onsite Comment -None

                try:
                    lot_details_data.lot_actual_number = single_record1.find_element(By.CSS_SELECTOR, ' td:nth-child(1)').text
                    lot_details_data.lot_number = int(single_record1.find_element(By.CSS_SELECTOR, ' td:nth-child(1)')).text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

        #         # Onsite Field -Başlıq
        #         # Onsite Comment -None

                lot_details_data.lot_title = single_record1.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                lot_details_data.lot_title_english = GoogleTranslator(source='az', target='en').translate(lot_details_data.lot_title)
               
        #         # Onsite Field -Açıqlama
        #         # Onsite Comment -None

                try:
                    lot_details_data.lot_description = single_record1.find_element(By.CSS_SELECTOR, ' td:nth-child(3) > app-tooltip > div:nth-child(2) > p').text
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

        #         # Onsite Field -Miqdar
        #         # Onsite Comment -None

                try:
                    lot_details_data.lot_quantity = single_record1.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

        #         # Onsite Field -Ölçü vahidi
        #         # Onsite Comment -None

                try:
                    lot_details_data.lot_quantity_uom = single_record1.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass


                try:
                    award_details_data = award_details()
                    award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(4) > app-tooltip > div.tooltip > p').text
                    # Onsite Field -Təklifin qiyməti
                    # Onsite Comment -None

                    award_details_data.grossawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > app-tooltip > p').text.split(' AZN')[0]
                    award_details_data.grossawardvaluelc =float(award_details_data.grossawardvaluelc.replace('.','').replace(',','.'))


                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
    except:
        pass

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://etender.gov.az/main/competitions/1/0"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        
        clk=page_main.find_element(By.XPATH,'//*[@id="select2-0"]/div[2]/div[1]/div').click()
        clk=page_main.find_element(By.XPATH,'//*[@id="select2-0-option-2"]').click()
        time.sleep(10)
        
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/app-competitions/main/section/div/div[2]/div/app-table/div[1]/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH,'/html/body/app-root/app-competitions/main/section/div/div[2]/div/app-table/div[1]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH,'/html/body/app-root/app-competitions/main/section/div/div[2]/div/app-table/div[1]/div/table/tbody/tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/app-root/app-competitions/main/section/div/div[2]/div/app-table/div[1]/div/table/tbody/tr'),page_check))
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
