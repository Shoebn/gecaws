from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_acquistinretepa_spn"
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
import gec_common.Doc_Download_VPN as Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_acquistinretepa_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_acquistinretepa_spn'
    
    notice_data.currency = 'EUR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.procurement_method = 2
    
    notice_data.main_language = 'IT'
    
    notice_data.notice_type = 4
    
    # Onsite Field -N.GARA
    # Onsite Field -also take notice_no from notice url
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.stato.borderElenco.nopadding.col-sm-1.ng-scope > div > p').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    # Onsite Field -AREA MERCEOLOGICA
    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(4) ').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p > a').get_attribute("href") 
    except:
        pass
    
    try:
        fn.load_page(page_details,notice_data.notice_url,180)
        logging.info(notice_data.notice_url)

    # Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ----"//*[@id="page-complete"]/div/div[1]/div[6]/div[1]/div[3]/div"
    # Onsite Comment -click on "div.height-99-sm" >>>>> take multiple data i.e there are multiple tabs....following is the selector u can use "div.col-sm-10.pull-right"   ref url  -https://www.acquistinretepa.it/opencms/opencms/scheda_bando.html?idBando=6efc4d172366ab6a"
        try:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#page-complete > div.ng-scope > div > div:nth-child(2) > div:nth-child(3) > div').get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

        try:
            popup_click = WebDriverWait(page_details, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.modal-title.semibold-24.col-sm-12.nopadding > div > div.col-sm-1.nopadding.voffset1 > button')))
            page_details.execute_script("arguments[0].click();",popup_click)
            time.sleep(5)
        except:
            pass
        
        try:
            notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, 'div.titoloiniziativa > h1').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' p.regular-18.ellipsis.responsiveText18.ng-binding.ng-scope').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        try:  
            CPV_click = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="categorie"]/button')))
            page_details.execute_script("arguments[0].click();",CPV_click)
            time.sleep(5)

            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-sm-4.nopadding.ng-binding'):

            # Onsite Field -CPV
            # Onsite Comment -click on "#categorie > button" to get data --- click on "cpv" botton to grab data

                cpvs_data = cpvs()
                cpv_code = single_record.text
                cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0]
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)

                try:
                    notice_data.cpv_at_source = re.findall('\d{8}',cpv_code)[0]
                except Exception as e:
                    logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
                    pass

                notice_data.cpv_at_source = 'CPV'

            CPV_close = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div/div/div[1]/div[2]')))
            page_details.execute_script("arguments[0].click();",CPV_close)
            time.sleep(3)
        except Exception as e:
            logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
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

        try:
            notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.titoloiniziativa.col-sm-9.col-xs-12 > h5').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass

    # #     # Onsite Comment -Appalto di servizi - Service, Appalto di forniture - Supply

        try:              
            customer_details_data = customer_details()
            # Onsite Field -STAZ. APPALTANTE
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-sm-12.col-lg-9.col-xs-12.nopadding > div:nth-child(3) > div > div > div:nth-child(6)').text
            customer_details_data.org_country = 'IT'
            customer_details_data.org_language = 'IT'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        try:
            lot_number = 1
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.boxLottiBando.col-sm-12.col-xs-12.nopadding.margin-top-20.ng-scope'):
                count_data = single_record.text
                count_data1 = count_data.count(single_record.text)
                if count_data1 == 1: 
                    try:
                        netbudgeteuro = page_details.find_element(By.XPATH, '//*[contains(text(),"VALORE")]').text
                        netbudgeteuro = re.sub("[^\d\.\,]","",netbudgeteuro)
                        notice_data.netbudgeteuro =float(netbudgeteuro.replace('.','').replace(',','.').strip())
                        notice_data.netbudgetlc = notice_data.netbudgeteuro
                    except:
                        pass
                
                lot_details_data = lot_details()
            # Onsite Comment -ref url -  "https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=23f8c8da3e2989d0"

                lot_details_data.lot_number = lot_number
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'div div div div div .text-left.ng-binding').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

            # Onsite Comment -ref url -  "https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=23f8c8da3e2989d0"
                try:
                    lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'div.nopadding.voffset > div').text
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

            # Onsite Field -CIG

                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'div > div.col-sm-8 div:nth-child(3)').text.split('CIG: ')[1]
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

            # Onsite Field -CIG

                try:
                    try:  
                        lot_netbudget = single_record.find_element(By.CSS_SELECTOR, 'div.borderR-sm.height80-sm.regular-16.ng-scope').text
                    except:
                        lot_netbudget = single_record.find_element(By.CSS_SELECTOR, 'span.semibold-18.ng-binding').text
                    lot_netbudget = re.findall('(\d[\d,.]*)',lot_netbudget)[0]
                    lot_netbudget = lot_netbudget.replace('.', '')
                    if ',' in lot_netbudget[-3]:
                        lot_netbudget = lot_netbudget.replace(',', '.')
                    lot_details_data.lot_netbudget = float(lot_netbudget)
                    lot_details_data.lot_netbudget_lc = lot_details_data.lot_netbudget
                except Exception as e:
                    logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                    pass

    # For now there is no criteria avaialble on site.
            # Onsite Field -None
            # Onsite Comment -ref url - "https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=414410144912b091"

        #         try:
        #             for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.ng-scope.borderAB-left'):
        #                 lot_criteria_data = lot_criteria()

        #                 # Onsite Field -None
        #                 # Onsite Comment -ref url - "https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=414410144912b091"

        #                 lot_criteria_data.lot_criteria_weight = page_details.find_element(By.CSS_SELECTOR, 'div.ng-scope.borderAB-left  div:nth-child(3) > div').text

        #                 # Onsite Field -None
        #                 # Onsite Comment -ref url - "https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=414410144912b091"

        #                 lot_criteria_data.lot_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'div.ng-scope.borderAB-left  div:nth-child(3) > div').text

        #                 lot_criteria_data.lot_criteria_cleanup()
        #                 lot_details_data.lot_criteria.append(lot_criteria_data)
        #         except Exception as e:
        #             logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
        #             pass

                try:
                    CPV_click = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="categorie"]/button')))
                    page_details.execute_script("arguments[0].click();",CPV_click)
                    time.sleep(5)

                    for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-sm-4.nopadding.ng-binding'):
                    # Onsite Field -CPV
                    # Onsite Comment -click on "#categorie > button" to get data --- click on "cpv" botton to grab data
                        lot_cpvs_data = lot_cpvs()
                        cpv_code = single_record.text
                        lot_cpvs_data.lot_cpv_code = re.findall('\d{8}',cpv_code)[0]
                        lot_cpvs_data.lot_cpvs_cleanup()
                        lot_details_data.lot_cpvs.append(lot_cpvs_data)
                    CPV_close = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div/div/div[1]/div[2]')))
                    page_details.execute_script("arguments[0].click();",CPV_close)
                    time.sleep(3)
                except:
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass


    # Onsite Comment -ref url - https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=237f17bd8cff12cc

        try:              
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#all-page > div:nth-child(3) > div > div > div.cosaAcquisti.col-sm-12.col-xs-12.nopadding.col-lg-9 > div:nth-child(5) > div:nth-child(2) > div'):
                attachments_data = attachments()
            # Onsite Field -DOCUMENTAZIONE DI GARA

                try:
                    attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'div > div  ').text.split('.')[-1]
                except:
                    pass

            # Onsite Field -DOCUMENTAZIONE DI GARA
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'strong.fontBlue.cursor.ng-binding').text
                

            # Onsite Field -DOCUMENTAZIONE DI GARA
                external_url = WebDriverWait(single_record, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'strong.fontBlue.cursor.ng-binding')))
                page_details.execute_script("arguments[0].click();",external_url)
                time.sleep(50)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, '#all-page > div:nth-child(3) > div > div > div.cosaAcquisti.col-sm-12.col-xs-12.nopadding.col-lg-9 > div:nth-child(5) > div:nth-child(2) > div a.ng-binding').get_attribute('href')
    except:
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)   
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments)
page_details = Doc_Download.page_details
 
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
        try:
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
