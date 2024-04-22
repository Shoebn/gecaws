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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_ehawaii_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------

# Note : when you click on table row it will pass into detail_page ,  for Navigate to the detail_page click on the "tr.ng-star-inserted" field if the  message is appear that  
#        "You are leaving HANDS and proceeding to the HIePRO State of Hawaii eProcurement website." or any other  popup for 
#        another website is displayed, then click on the "Cancel" button  (note : do not click on "tr > td:nth-child(5) a"   for detail_page)

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------


def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'us_ehawaii_ca'
    
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
    

    notice_data.currency = 'USD'
    
    notice_data.notice_type = 7
    
    notice_data.procurement_method = 2
    
    notice_data.document_type_description = "Contract Awards"
    
    # Onsite Field -Solicitation #
    # Onsite Comment -if notice_no is not available in "Solicitation #" then split the number from notice_url
    time.sleep(5)
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Category
    # Onsite Comment -Replace the  following keywords with given respective keywords ('Services = service' , 'Goods = supply' , 'Goods & Services   = service' , 'Construction = Works' , 'Health and Human Services = service' , 'Professional Services = service' , 'Hybrid (combo of 2 or more categories) = service')

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
        if 'Services' in notice_contract_type or 'Goods & Services' in notice_contract_type or 'Health and Human Services' in notice_contract_type or 'Professional Services' in notice_contract_type or 'and' in notice_contract_type or '&' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        if 'Goods' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        if 'Construction' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Category
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = notice_contract_type
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except:
        pass
    
    try:
        org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9)').text
    except:
        pass
    
    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text

    bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
    
    try:
        award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except:
        pass
    
    try:
        grossawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except:
        pass
    
    notice_url_click = tender_html_element
    page_main.execute_script("arguments[0].click();",notice_url_click)
    time.sleep(5)
    
    try:
        ok = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.modal-footer > button.btn.btn-primary')))
        page_main.execute_script("arguments[0].click();",ok)
        time.sleep(5)
        page_main.switch_to.window(page_main.window_handles[1])
        time.sleep(5)
        notice_url = page_main.current_url
        if 'vendorlogin' in notice_url:
            page_main.close()
            page_main.switch_to.window(page_main.window_handles[0])
            return
        notice_data.notice_url = notice_url
        logging.info(notice_data.notice_url)
        try:
            notice_no1 = notice_data.notice_no
            if notice_no1 ==" " or notice_no1 == '--':
                notice_data.notice_no = re.findall("\d+",notice_data.notice_url)[0]

        except:
            pass

        try:
            notice_data.notice_text += WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#body-container > main > div.tab-content'))).get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
            
        

        try:
            notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Award Description")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

        # Onsite Field -Description
        # Onsite Comment -split the data from detail_page

        try:
            notice_data.notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Award Description")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass


        # Onsite Field -contract start date
        # Onsite Comment -None

        try:
            tender_contract_start_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Contract Start Date")]//following::dd[1]').text
            tender_contract_start_date = re.findall('\d+/\d+/\d{4}',tender_contract_start_date)[0]
            notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
            pass

        # Onsite Field -Contract End Date
        # Onsite Comment -None

        try:
            tender_contract_end_date = page_main.find_element(By.XPATH, '//*[contains(text(),"End Date / Delivery Date")]//following::dd[1]').text
            tender_contract_end_date = re.findall('\d+/\d+/\d{4}',tender_contract_end_date)[0]
            notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
            pass


        try:
            customer_details_data = customer_details()

            customer_details_data.org_name = org_name

            customer_details_data.org_country = 'US'
            customer_details_data.org_language = 'EN'

            try:
                customer_details_data.org_city = org_city
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Contact Person")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Phone")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"Email")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        
        try:
            lot_number = 1
            for single_record in page_main.find_elements(By.CSS_SELECTOR,'div.line_item_details'):
                single_record_text = single_record.get_attribute('outerHTML')
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number

                lot_details_data.lot_title = single_record_text.split('<dt>Title</dt>')[1].split('<dd>')[1].split('</dd>')[0].strip()


                try:
                    lot_quantity = single_record_text.split('<dt>Quantity</dt>')[1].split('<dd>')[1].split('</dd>')[0].strip()
                    lot_details_data.lot_quantity = float(lot_quantity)
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_quantity_uom = single_record_text.split('<dt>Unit of Measure</dt>')[1].split('<dd>')[1].split('</dd>')[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_description = single_record_text.split('<dt>Description</dt>')[1].split('<dd>')[1].split('</dd>')[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass
            
                try:
                    lot_grossbudget_lc = single_record_text.split('>Total Price</dt>')[1].split('<dd>')[1].split('</dd>')[0].strip()
                    lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                    lot_details_data.lot_grossbudget_lc  =float(lot_grossbudget_lc.replace(',','').strip())
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass

                try:
                    for single_record in page_main.find_elements(By.XPATH, '//*[@class="table-responsive"]//td[1]'):
                        cpv_code = single_record.get_attribute('outerHTML')
                        cpv_code_regex = re.findall('\d{6}',cpv_code)[0]
                        cpv_codes_list = fn.procedure_mapping("assets/naics-codes.csv",cpv_code_regex)
                        split_data = cpv_codes_list.split('#')
                        cpv_at_source = ''
                        for each_cpv in split_data:
                            cpvs_data = cpvs()
                            cpvs_data.cpv_code = each_cpv
                            cpv_at_source += each_cpv
                            cpv_at_source += ','
                            cpvs_data.cpvs_cleanup()
                            notice_data.cpvs.append(cpvs_data)
                        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
                        notice_data.class_codes_at_source = notice_data.cpv_at_source
                except Exception as e:
                    logging.info("Exception in cpvs: {}".format(type(e).__name__))
                    pass
        
                try:
                    lot_cpv_code = re.findall('\d{6}',single_record_text)
                    lot_class_codes_at_source = ''
                    for single_record in lot_cpv_code:
                        lot_class_codes_at_source += single_record
                        lot_class_codes_at_source +=','
                        lot_cpv_code = fn.procedure_mapping("assets/naics-codes.csv",single_record.strip())
                        split_data = lot_cpv_code.split('#')
                        lot_cpv_at_source = ''
                        for each_cpv in split_data:
                            lot_cpvs_data = lot_cpvs()
                            lot_cpvs_data.lot_cpv_code = each_cpv
                            lot_cpv_at_source += each_cpv
                            lot_cpv_at_source += ','
                            lot_cpvs_data.lot_cpvs_cleanup()
                            lot_details_data.lot_cpvs.append(lot_cpvs_data)
                        lot_details_data.lot_cpv_at_source = lot_cpv_at_source.rstrip(',')
                    lot_details_data.lot_class_codes_at_source = lot_class_codes_at_source.rstrip(',')
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass
                
                try:
                    contract_start_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Contract Start Date")]//following::dd[1]').text
                    contract_start_date = re.findall('\d+/\d+/\d{4}',contract_start_date)[0]
                    lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%m/%d/%Y').strftime('%Y/%m/%d')
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass

                try:
                    contract_end_date = page_main.find_element(By.XPATH, '//*[contains(text(),"End Date / Delivery Date")]//following::dd[1]').text
                    contract_end_date = re.findall('\d+/\d+/\d{4}',contract_end_date)[0]
                    lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%m/%d/%Y').strftime('%Y/%m/%d')
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__))
            pass
        Amendments = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Amendments')))
        page_main.execute_script("arguments[0].click();",Amendments)
        
        notice_data.notice_text += WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="tabs-3"]'))).get_attribute("outerHTML")
        
        Instructions = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Instructions')))
        page_main.execute_script("arguments[0].click();",Instructions)
        
        notice_data.notice_text += WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#instructions > fieldset'))).get_attribute("outerHTML")
        page_main.close()
        page_main.switch_to.window(page_main.window_handles[0])
    except:
        notice_data.notice_url = page_main.current_url
        try:
            notice_no1 = notice_data.notice_no
            if notice_no1 ==" " or notice_no1 == '--':
                notice_data.notice_no = re.findall("\d+",notice_data.notice_url)[0]

        except:
            pass

        try:
            notice_data.notice_text += WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div > div > tabset'))).get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

        try:
            notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

        # Onsite Field -Description
        # Onsite Comment -split the data from detail_page

        try:
            notice_data.notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass


        # Onsite Field -contract start date
        # Onsite Comment -None

        try:
            tender_contract_start_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Start Date")]//following::td[1]').text
            tender_contract_start_date = re.findall('\d+/\d+/\d{4}',tender_contract_start_date)[0]
            notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
            pass

        # Onsite Field -Contract End Date
        # Onsite Comment -None

        try:
            tender_contract_end_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Contract End Date")]//following::td[2]').text
            tender_contract_end_date = re.findall('\d+/\d+/\d{4}',tender_contract_end_date)[0]
            notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
            pass

        # Onsite Field -Total Contract Value
        # Onsite Comment -None

        try:
            grossbudgetlc = page_main.find_element(By.XPATH, '//*[contains(text(),"Total Contract Value")]//following::td[1]').text
            grossbudgetlc = re.sub("[^\d\.\,]","",grossbudgetlc)
            notice_data.grossbudgetlc = float(grossbudgetlc.replace(",",'').strip())
            notice_data.est_amount = notice_data.grossbudgetlc
        except Exception as e:
            logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
            pass

    # Onsite Field -Attachment(s)
    # Onsite Comment -None

        try:              
            attachments_data = attachments()
        # Onsite Field -Attachment(s)
        # Onsite Comment -split only file name for exmaple "Award letter.PDF" , here take only "Award letter"
            attachments_data.file_name = page_main.find_element(By.CSS_SELECTOR, 'tr:nth-child(13) > td > span > a').text

        # Onsite Field -Attachment(s)
        # Onsite Comment -split only file type  for exmaple "Award letter.PDF" , here take only "PDF"

            try:
                attachments_data.file_type = page_main.find_element(By.CSS_SELECTOR, 'tr:nth-child(13) > td > span > a').text.split(".")[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

        # Onsite Field -Attachment(s)
        # Onsite Comment -None

            attachments_data.external_url = page_main.find_element(By.CSS_SELECTOR, 'tr:nth-child(13) > td > span > a').get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
        time.sleep(5)
        try:
            lot_details_data = lot_details()
        # Onsite Field -Title
        # Onsite Comment -take a lot_title as a local_title

            lot_details_data.lot_title = notice_data.local_title
            notice_data.is_lot_default = True
            lot_details_data.lot_number = 1

            award_details_data = award_details()

            # Onsite Field -Date Awarded
            # Onsite Comment -None 
            try:
                award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%m/%d/%Y').strftime('%Y/%m/%d')
            except:
                pass

            # Onsite Field -Date Awarded
            # Onsite Comment -None
            try:

                grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                award_details_data.grossawardvaluelc = float(grossawardvaluelc.replace(",",'').strip())
            except:
                pass

            # Onsite Field -Awardee
            # Onsite Comment -None

            award_details_data.bidder_name = bidder_name

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass

        try:
            customer_details_data = customer_details()

            customer_details_data.org_name = org_name

            customer_details_data.org_country = 'US'
            customer_details_data.org_language = 'EN'

            try:
                customer_details_data.org_city = org_city
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass

            try:
                Contact_Information = WebDriverWait(page_main, 30).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="body-container"]/main/app-award-details/div[1]/app-awards-gsc/div/div/tabset/ul/li[2]/a')))
                page_main.execute_script("arguments[0].click();",Contact_Information)
            except:
                try:
                    Contact_Information = WebDriverWait(page_main, 30).until(EC.element_to_be_clickable((By.XPATH,'/html/body/app-root/div/main/app-award-details/div[1]/app-awards-pro/div/div/tabset/ul/li[2]/a')))
                    page_main.execute_script("arguments[0].click();",Contact_Information)
                except:
                    pass

            try:
                customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Contact Person")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass


            try:
                customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Phone")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass


            try:
                customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"E-mail")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        page_main.execute_script("window.history.go(-1)")
        time.sleep(5)

        
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
 
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tr.ng-star-inserted'))).text
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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
    urls = ["https://hands.ehawaii.gov/hands/awards"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(1,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tr.ng-star-inserted'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr.ng-star-inserted')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr.ng-star-inserted')))[records]
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
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search_results"]/div/div[2]/div/button[2]')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'tr.ng-star-inserted'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)