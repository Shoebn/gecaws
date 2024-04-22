from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_powergridindia"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_powergridindia"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_powergridindia'
  
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.currency = 'INR'
    
    types_of_tenders = page_main.find_element(By.CSS_SELECTOR, "#b_gData > caption").text
    
#***************************************************************************************************************************
    if 'Published Tender(s) / प्रकाशित निविदा' in types_of_tenders:
        
        notice_data.script_name = 'in_powergridindia_spn'
        
        notice_data.notice_type = 4

        try:  #Thu, 15-Feb-2024 07:10 PM
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(6) ").text
            publish_date = re.findall('\d+-\w+-\d{4} \d+:\d+ [PMAMpmam]+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

        try:
            notice_data.related_tender_id  = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in related_tender_id : {}".format(type(e).__name__))
            pass

        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(4) > font').text
        except Exception as e:
            logging.info("Exception in notice_no : {}".format(type(e).__name__))
            pass

        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.replace(notice_data.notice_no,'').split('\n')[1].strip()
            notice_data.notice_title = notice_data.local_title
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        try: #07-Mar-2024
            contract_start_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text.split('/')[0].strip()
            contract_start_date = re.findall('\d+-\w+-\d{4} \d+:\d+ [PMAMpmam]+',contract_start_date)[0]
            notice_data.contract_start_date = datetime.strptime(contract_start_date,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
            pass

        try: #07-Mar-2024
            contract_end_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text.split('/')[1].strip()
            contract_end_date = re.findall('\d+-\w+-\d{4} \d+:\d+ [PMAMpmam]+',contract_end_date)[0]
            notice_data.contract_end_date = datetime.strptime(contract_end_date,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
            pass

        try:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        except:
            pass
        
        try:
            notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7) > a').get_attribute("href")
        except:
            pass
        
        try:                                 
            fn.load_page(page_details,notice_data.notice_url,80)
            logging.info(notice_data.notice_url)

            try:
                notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#b_p1 > fieldset').get_attribute("outerHTML")                     
            except:
                pass
            
            try: #07-Mar-2024
                document_purchase_start_time = page_details.find_element(By.XPATH, "//*[contains(text(),'Document Sale Start Date / दस्तावेज़ बिक्री प्रारंभ की तारीख')]//parent::tr/td[2]").text
                document_purchase_start_time = re.findall('\d+-\w+-\d{4}',document_purchase_start_time)[0]
                notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d-%b-%Y').strftime('%Y/%m/%d')
            except Exception as e:
                logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
                pass

            try: #07-Mar-2024
                document_purchase_end_time = page_details.find_element(By.XPATH, "//*[contains(text(),'Document Sale End Date / दस्तावेज़ बिक्री समाप्ति की तारीख')]//parent::tr/td[4]").text
                document_purchase_end_time = re.findall('\d+-\w+-\d{4}',document_purchase_end_time)[0]
                notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d-%b-%Y').strftime('%Y/%m/%d')
            except Exception as e:
                logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
                pass
            
            try:
                notice_data.class_title_at_source = page_details.find_element(By.XPATH, "//*[contains(text(),'Sector')]//parent::tr/td[2]").text
            except Exception as e:
                logging.info("Exception in class_title_at_source: {}".format(type(e).__name__))
                pass

            try:
                notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Description')]//parent::tr/td[2]").text
                notice_data.notice_summary_english = notice_data.local_description
            except Exception as e:
                logging.info("Exception in local_description: {}".format(type(e).__name__))
                pass

            try:
                notice_data.document_fee = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Fee / निविदा शुल्क')]//parent::tr/td[2]").text
            except Exception as e:
                logging.info("Exception in document_fee: {}".format(type(e).__name__))
                pass

            try:
                notice_data.earnest_money_deposit = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Emd / निविदा ई.एम.डी')]//parent::tr/td[2]").text
            except Exception as e:
                logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
                pass

            try:
                pre_bid_meeting_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Pre Bid Meeting Date / प्री-बिड मीटिंग तारीख')]//parent::tr/td[4]").text
                pre_bid_meeting_date = re.findall('\d+-\w+-\d{4}',pre_bid_meeting_date)[0]
                notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d-%b-%Y').strftime('%Y/%m/%d')
            except Exception as e:
                logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
                pass

            try: #keywords("Services=Service","Works=Works","Goods=Supply")
                notice_data.contract_type_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Category / निविदा श्रेणी')]//parent::tr/td[4]").text
                if 'Services' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Service'
                elif 'Works' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Works'
                elif 'Goods' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Supply'
            except Exception as e:
                logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
                pass

            try:  #Tue, 05-Mar-2024 03:00 PM
                notice_deadline = page_details.find_element(By.XPATH, "//*[contains(text(),'Bid Submission EndDate (Soft Copy) / बोली जमा करने की  अंतिम तिथि (सॉफ्ट कॉपी)')]//parent::tr/td[4]").text
                notice_deadline = re.findall('\d+-\w+-\d{4} \d+:\d+ [PMAMpmam]+',notice_deadline)[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.notice_deadline)
            except Exception as e:
                logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
                pass

            try:
                est_amount = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Value / निविदा मूल्य')]//parent::tr/td[4]").text
                est_amount = re.sub("[^\d\.\,]","",est_amount)
                notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
                notice_data.grossbudgetlc = notice_data.est_amount
            except Exception as e:
                logging.info("Exception in est_amount: {}".format(type(e).__name__))
                pass

            try:              
                customer_details_data = customer_details()
                customer_details_data.org_name = 'Power Grid Corporation of India Limited'
                customer_details_data.org_parent_id = 7767417 
                customer_details_data.org_language = 'EN'
                customer_details_data.org_country = 'IN'

                try:
                    customer_details_data.org_address = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Inviting Officer Address / निविदा आमंत्रण अधिकारी का पता')]//parent::tr/td[2]").text
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Inviting Officer Name & Designation / निविदा आमंत्रण अधिकारी का नाम और पदनाम')]//parent::tr/td[4]").text
                except Exception as e:
                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.org_state = page_details.find_element(By.XPATH, "//*[contains(text(),'State / राज्य')]//parent::tr/td[4]").text
                except Exception as e:
                    logging.info("Exception in org_state: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.postal_code = page_details.find_element(By.XPATH, "//*[contains(text(),'Pin Code / पिन कोड')]//parent::tr/td[4]").text
                except Exception as e:
                    logging.info("Exception in postal_code: {}".format(type(e).__name__))
                    pass

                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
            except Exception as e:
                logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
                pass
            
            try:              
                for single_record in page_details.find_elements(By.XPATH, "//*[contains(text(),'Tender Documents / निविदा दस्तावेज')]//following::tr")[1:]:
                    attachments_data = attachments()

                    attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute('href')
                    
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('.')[0].strip()

                    try:
                        attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text
                    except Exception as e:
                        logging.info("Exception in file_size: {}".format(type(e).__name__))
                        pass
                    try:
                        attachments_data.file_type = attachments_data.external_url.split(".")[-1].strip()
                    except Exception as e:
                        logging.info("Exception in file_type: {}".format(type(e).__name__))
                        pass

                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
            except Exception as e:
                logging.info("Exception in attachments: {}".format(type(e).__name__)) 
                pass
            
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            pass

#**************************************************************************************************************************
    
    elif 'Published Corrigendum(s)' in types_of_tenders:
        
        notice_data.script_name = 'in_powergridindia_amd'
        
        notice_data.notice_type = 16
        
        try:
            notice_data.related_tender_id  = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split('\n')[0].split('Tender ID:')[1].strip()
        except Exception as e:
            logging.info("Exception in related_tender_id : {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split('\n')[1].split('Ref No:')[1].strip()
        except Exception as e:
            logging.info("Exception in notice_no : {}".format(type(e).__name__))
            pass
        
        try:  #Fri, 16-Feb-2024 11:35 AM
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(4)").text
            publish_date = re.findall('\d+-\w+-\d{4} \d+:\d+ [PMAMpmam]+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return
        
        try:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        except:
            pass
        
        try:
            notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(7) > a').get_attribute("href")
        except:
            pass

        try:                                 
            fn.load_page(page_details,notice_data.notice_url,80)
            logging.info(notice_data.notice_url)

            try:
                notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#b_p1 > fieldset').get_attribute("outerHTML")                     
            except:
                pass
            
            try:
                notice_data.local_title = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Title')]//parent::tr/td[4]").text
                notice_data.notice_title = notice_data.local_title
            except Exception as e:
                logging.info("Exception in local_title: {}".format(type(e).__name__))
                pass
            
            try:
                notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Description')]//parent::tr/td[2]").text
                notice_data.notice_summary_english = notice_data.local_description
            except Exception as e:
                logging.info("Exception in local_description: {}".format(type(e).__name__))
                pass
            
            try:
                notice_data.document_fee = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Fee')]//parent::tr/td[2]").text
            except Exception as e:
                logging.info("Exception in document_fee: {}".format(type(e).__name__))
                pass
            
            try:
                est_amount = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Value')]//parent::tr/td[4]").text
                est_amount = re.sub("[^\d\.\,]","",est_amount)
                notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
                notice_data.grossbudgetlc = notice_data.est_amount
            except Exception as e:
                logging.info("Exception in est_amount: {}".format(type(e).__name__))
                pass

            try:
                notice_data.earnest_money_deposit = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender EMD')]//parent::tr/td[2]").text
            except Exception as e:
                logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
                pass
            
            try:
                pre_bid_meeting_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Pre Bid Meeting Date')]//parent::tr/td[4]").text
                pre_bid_meeting_date = re.findall('\d+-\w+-\d{4}',pre_bid_meeting_date)[0]
                notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d-%b-%Y').strftime('%Y/%m/%d')
            except Exception as e:
                logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
                pass

            try: #keywords("Services=Service","Works=Works","Goods=Supply")
                notice_data.contract_type_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Category')]//parent::tr/td[4]").text
                if 'Services' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Service'
                elif 'Works' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Works'
                elif 'Goods' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Supply'
            except Exception as e:
                logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
                pass
            
            try: #07-Mar-2024
                document_purchase_start_time = page_details.find_element(By.XPATH, "//*[contains(text(),'Document Sale Start Date')]//parent::tr/td[2]").text
                document_purchase_start_time = re.findall('\d+-\w+-\d{4}',document_purchase_start_time)[0]
                notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d-%b-%Y').strftime('%Y/%m/%d')
            except Exception as e:
                logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
                pass

            try: #07-Mar-2024
                document_purchase_end_time = page_details.find_element(By.XPATH, "//*[contains(text(),'Document Sale End Date')]//parent::tr/td[4]").text
                document_purchase_end_time = re.findall('\d+-\w+-\d{4}',document_purchase_end_time)[0]
                notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d-%b-%Y').strftime('%Y/%m/%d')
            except Exception as e:
                logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
                pass
            
            try:  #Tue, 05-Mar-2024 03:00 PM
                notice_deadline = page_details.find_element(By.XPATH, "//*[contains(text(),'Bid Submission End Date (Soft Copy)')]//parent::tr/td[4]").text
                notice_deadline = re.findall('\d+-\w+-\d{4} \d+:\d+ [PMAMpmam]+',notice_deadline)[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.notice_deadline)
            except Exception as e:
                logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
                pass
            
            try:
                document_opening_time = page_details.find_element(By.XPATH, "//*[contains(text(),'Bid Open Date')]//parent::tr/td[2]").text
                document_opening_time = re.findall('\d+-\w+-\d{4}',document_opening_time)[0]
                notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%b-%Y').strftime('%Y-%m-%d')
                logging.info(notice_data.document_opening_time)
            except Exception as e:
                logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
                pass
            
            try:
                notice_data.class_title_at_source = page_details.find_element(By.XPATH, "//*[contains(text(),'Sector')]//parent::tr/td[2]").text
            except Exception as e:
                logging.info("Exception in class_title_at_source: {}".format(type(e).__name__))
                pass
            
            try:              
                customer_details_data = customer_details()
                customer_details_data.org_name = 'Power Grid Corporation of India Limited'
                customer_details_data.org_parent_id = 7767417 
                customer_details_data.org_language = 'EN'
                customer_details_data.org_country = 'IN'

                try:
                    customer_details_data.org_address = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Inviting Officer Address')]//parent::tr/td[2]").text
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Inviting Officer Name & Designation')]//parent::tr/td[4]").text
                except Exception as e:
                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.org_state = page_details.find_element(By.XPATH, "//*[contains(text(),'State')]//parent::tr/td[4]").text
                except Exception as e:
                    logging.info("Exception in org_state: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.postal_code = page_details.find_element(By.XPATH, "//*[contains(text(),'Pin Code')]//parent::tr/td[4]").text
                except Exception as e:
                    logging.info("Exception in postal_code: {}".format(type(e).__name__))
                    pass

                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
            except Exception as e:
                logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
                pass
            
            try:              
                for single_record in page_details.find_elements(By.XPATH, "//*[contains(text(),'Uploaded Corrigendum Documents')]//following::tr")[1:]:
                    attachments_data = attachments()

                    attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute('href')
                    
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('.')[0].strip()

                    try:
                        attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text
                    except Exception as e:
                        logging.info("Exception in file_size: {}".format(type(e).__name__))
                        pass
                    try:
                        attachments_data.file_type = attachments_data.external_url.split(".")[-1].strip()
                    except Exception as e:
                        logging.info("Exception in file_type: {}".format(type(e).__name__))
                        pass

                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
            except Exception as e:
                logging.info("Exception in attachments: {}".format(type(e).__name__)) 
                pass
            
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            pass
            
#**************************************************************************************************************************
            
    elif 'Published AoC(s)' in types_of_tenders:
        
        notice_data.script_name = 'in_powergridindia_ca'
        
        notice_data.notice_type = 7        
            
        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in notice_no : {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.related_tender_id  = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split('Ref No:')[1].strip()
        except Exception as e:
            logging.info("Exception in related_tender_id : {}".format(type(e).__name__))
            pass
        
        try:#Thu, 25-Jan-2024 12:00 AM
            award_date2 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            award_date1 = re.findall('\d+-\w+-\d{4}',award_date2)[0]
            award_date = datetime.strptime(award_date1,'%d-%b-%Y').strftime('%Y/%m/%d')
            
            notice_data.publish_date = datetime.strptime(award_date1,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in award_date : {}".format(type(e).__name__))
            pass
        
        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return
        
        try:
            bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        except:
            pass
        
        try:
            address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        except:
            pass
        
        try:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        except:
            pass
        
        try:
            notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8) > a').get_attribute("href")
        except:
            pass

        try:                                 
            fn.load_page(page_details,notice_data.notice_url,80)
            logging.info(notice_data.notice_url)

            try:
                notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#b_p1 > fieldset').get_attribute("outerHTML")                     
            except:
                pass
                
            try:
                notice_data.local_title = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Title')]//parent::tr/td[4]").text
                notice_data.notice_title = notice_data.local_title
            except Exception as e:
                logging.info("Exception in local_title: {}".format(type(e).__name__))
                pass
            
            try:
                notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Description')]//parent::tr/td[2]").text
                notice_data.notice_summary_english = notice_data.local_description
            except Exception as e:
                logging.info("Exception in local_description: {}".format(type(e).__name__))
                pass
            
            try:              
                lot_details_data = lot_details()
                lot_details_data.lot_number = 1
                lot_details_data.lot_title = notice_data.local_title
                notice_data.is_lot_default = True
                lot_details_data.lot_description = notice_data.local_description
                award_details_data = award_details()

                award_details_data.bidder_name = bidder_name

                try:
                    award_details_data.address = address
                except:
                    pass
                
                try:
                    award_details_data.award_date = award_date
                except:
                    pass
                
                try:
                    grossawardvaluelc = page_details.find_element(By.XPATH, "//*[contains(text(),'Contract Value')]//parent::tr/td[2]").text
                    grossawardvaluelc = re.sub("[^\d\.\,]", "",grossawardvaluelc)
                    grossawardvaluelc = grossawardvaluelc.replace('.','').replace(',','.').strip()
                    award_details_data.grossawardvaluelc = float(grossawardvaluelc)
                except Exception as e:
                    logging.info("Exception in local_description: {}".format(type(e).__name__))
                    pass
                
                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)

                if lot_details_data.award_details != []:
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
            except Exception as e:
                logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
                pass
            
            try:              
                for single_record in page_details.find_elements(By.XPATH, "//*[contains(text(),'AoC Documents')]//following::tr")[1:]:
                    attachments_data = attachments()

                    attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute('href')
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('.')[0].strip()

                    try:
                        attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text
                    except Exception as e:
                        logging.info("Exception in file_size: {}".format(type(e).__name__))
                        pass
                    try:
                        attachments_data.file_type = attachments_data.external_url.split(".")[-1].strip()
                    except Exception as e:
                        logging.info("Exception in file_type: {}".format(type(e).__name__))
                        pass

                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
            except Exception as e:
                logging.info("Exception in attachments: {}".format(type(e).__name__)) 
                pass
            
            try:              
                customer_details_data = customer_details()
                customer_details_data.org_name = 'Power Grid Corporation of India Limited'
                customer_details_data.org_parent_id = 7767417 
                customer_details_data.org_language = 'EN'
                customer_details_data.org_country = 'IN'
                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
            except Exception as e:
                logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
                pass
            
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            pass
#**************************************************************************************************************************
    elif 'Published Amendment to AoC' in types_of_tenders:
        
        notice_data.script_name = 'in_powergridindia_amd'
        
        notice_data.notice_type = 16
        
        try:  #Tue, 30-Jun-2020 01:26 PM
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
            publish_date = re.findall('\d+-\w+-\d{4} \d+:\d+ [PMAMpmam]+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return
        
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_name = 'Power Grid Corporation of India Limited'
            customer_details_data.org_parent_id = 7767417 
            customer_details_data.org_language = 'EN'
            customer_details_data.org_country = 'IN'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in notice_no : {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.related_tender_id  = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split('Ref No:')[1].strip()
        except Exception as e:
            logging.info("Exception in related_tender_id : {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        except:
            pass
        
        try:
            notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7) > a').get_attribute("href")
        except:
            pass

        try:                                 
            fn.load_page(page_details,notice_data.notice_url,80)
            logging.info(notice_data.notice_url)

            try:
                notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#b_p1 > fieldset').get_attribute("outerHTML")                     
            except:
                pass
            
            try:
                notice_data.local_title = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Title')]//parent::tr/td[4]").text
                notice_data.notice_title = notice_data.local_title
            except Exception as e:
                logging.info("Exception in local_title: {}".format(type(e).__name__))
                pass
            
            try:
                notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Description')]//parent::tr/td[2]").text
                notice_data.notice_summary_english = notice_data.local_description
            except Exception as e:
                logging.info("Exception in local_description: {}".format(type(e).__name__))
                pass
        
            try:              
                lot_details_data = lot_details()
                lot_details_data.lot_number = 1
                lot_details_data.lot_title = notice_data.local_title
                notice_data.is_lot_default = True
                lot_details_data.lot_description = notice_data.local_description
                award_details_data = award_details()

                award_details_data.bidder_name = page_details.find_element(By.XPATH, "//*[contains(text(),'L1 Bidder Name')]//parent::tr/td[2]").text

                try:
                    award_details_data.address = page_details.find_element(By.XPATH, "//*[contains(text(),'L1 Bidder Address')]//parent::tr/td[4]").text
                except:
                    pass
                
                try:#Thu, 25-Jan-2024 12:00 AM
                    award_date2 = page_details.find_element(By.XPATH, "(//*[contains(text(),'Contract Date ')])[2]//parent::tr/td[4]").text
                    award_date1 = re.findall('\d+-\w+-\d{4}',award_date2)[0]
                    award_details_data.award_date = datetime.strptime(award_date1,'%d-%b-%Y').strftime('%Y/%m/%d')
                except Exception as e:
                    logging.info("Exception in award_date : {}".format(type(e).__name__))
                    pass
                
                try:
                    grossawardvaluelc = page_details.find_element(By.XPATH, "//*[contains(text(),'Contract Value')]//parent::tr/td[2]").text
                    grossawardvaluelc = re.sub("[^\d\.\,]", "",grossawardvaluelc)
                    grossawardvaluelc = grossawardvaluelc.replace('.','').replace(',','.').strip()
                    award_details_data.grossawardvaluelc = float(grossawardvaluelc)
                except Exception as e:
                    logging.info("Exception in local_description: {}".format(type(e).__name__))
                    pass
                
                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)

                if lot_details_data.award_details != []:
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
            except Exception as e:
                logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
                pass
            
            try:              
                for single_record in page_details.find_elements(By.XPATH, "//*[contains(text(),'Amendment to Contract Documents')]//following::tr")[1:]:
                    attachments_data = attachments()

                    attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute('href')
                    
                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('.')[0].strip()

                    try:
                        attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text
                    except Exception as e:
                        logging.info("Exception in file_size: {}".format(type(e).__name__))
                        pass
                    try:
                        attachments_data.file_type = attachments_data.external_url.split(".")[-1].strip()
                    except Exception as e:
                        logging.info("Exception in file_type: {}".format(type(e).__name__))
                        pass

                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
            except Exception as e:
                logging.info("Exception in attachments: {}".format(type(e).__name__)) 
                pass
            
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            pass
#**************************************************************************************************************************
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.local_title)+ str(notice_data.notice_url)
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
    urls = ["https://apps.powergrid.in/pgciltenders/u/view-published-tender.aspx","https://apps.powergrid.in/pgciltenders/u/view-published-corrigendum.aspx","https://apps.powergrid.in/pgciltenders/u/view-published-aoc.aspx","https://apps.powergrid.in/pgciltenders/u/view-published-aoc-corrigendum.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 180)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,10): 
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#b_gData > tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#b_gData > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#b_gData > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Next')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#b_gData > tbody > tr'),page_check))
                    time.sleep(5)
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except Exception as e:
            logging.info("No new record: {}".format(type(e).__name__))
            pass
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
