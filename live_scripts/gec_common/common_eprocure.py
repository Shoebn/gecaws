import base64
import logging
import os
import re
import shutil
import time
from zipfile import ZipFile

import jsons
import pandas as pd
import pytesseract
from PIL import Image, ImageFilter
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from xlsx2html import xlsx2html
import gec_common.Doc_Download as Doc_Download
import gec_common.OutputJSON as OutputJSON
import gec_common.web_application_properties as application_properties
from gec_common.gecclass import *


title_list = ['Regarding Uploaded Document','Please Refer To','Refer To Tender Document','Refer Tender Document','Mentioned In The Tender Document','Per Nit Document','Per Tender Document','Per Bid Document','Per The Attached Document','Per Attached Document','Can Be Seen In The Tender Documents','Pls Refer Tender','As Per Nit','As Per Boq','As Per Title','As Per Td','As Per Approval','As Per Dnit','Per the Boq','Per Boq Attached','Per Nit Document','Per Tender Abstract','As Per Enit','Per Tender Details','As Per Enclosed Annexure','Per Enclosed Annexure','As Per Annexure','As Per Schedule','As Per the Schedule','As Per Enquiry','As Per Attached Specification','As Above']

def read_catpcha_text(img):
    imgSrc = img.replace('data:image/png;base64,', '').replace('%0A', '').strip()
    imgData = base64.b64decode(imgSrc)
    filename = 'captcha.png'
    with open(filename, 'wb') as f:
        f.write(imgData)
    im = Image.open("captcha.png")
    im = im.filter(ImageFilter.MedianFilter())
    im = im.point(lambda x: 0 if x < 140 else 255)
    captcha_text = pytesseract.image_to_string(im, lang='eng')
    captcha_text = captcha_text.replace(' ', '').upper()
    captcha_text = re.sub('[\W_]+', '', captcha_text)
    return captcha_text


def captcha_image(page_main,keyword=None, doc=None):
    MAX_LOAD_DRIVER_ATTEMPTS = 10
    for loop_counter in range(1, MAX_LOAD_DRIVER_ATTEMPTS + 1):
        try:
            img = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR ,'#captchaImage'))).get_attribute('src')
            captcha_text = read_catpcha_text(img)
            captcha = page_main.find_element(By.CSS_SELECTOR,'#captchaText')
            captcha.clear()
            captcha.send_keys(captcha_text)
            time.sleep(1)
            if keyword is None and doc is None: #spn corri
                WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#Submit'))).click()
                table_data = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="table"]')))
            elif keyword is not None and doc is None: # ca
                page_main.find_element(By.CSS_SELECTOR ,'#Keyword').clear()     
                page_main.find_element(By.CSS_SELECTOR ,'#Keyword').send_keys(keyword)     
                WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#Search'))).click()
                table_data = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="table"]')))
            elif doc is not None:
                WebDriverWait(page_main, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#Submit'))).click()
                WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.LINK_TEXT, doc)))
            else:
                continue            
            break
        except Exception as e:
            if loop_counter == MAX_LOAD_DRIVER_ATTEMPTS:
                raise e
            else:
                pass
                

def convert_excel_to_html(new_file_name,attachment_dir):
    f_name =  new_file_name.replace(".zip","")
    extract_path = application_properties.TMP_DIR + '/' + f_name 
    new_file_name = attachment_dir + '/' + new_file_name
    with ZipFile(new_file_name, 'r') as zObject:
        zObject.extractall(path=extract_path)
        zObject.close()
    excel_files = os.listdir(extract_path)
    for excel_file in excel_files:
        excel_file = extract_path + '/' + excel_file
        html__output_file = application_properties.TMP_DIR + '/' + 'output.html'
        if excel_file.endswith('.xlsx'):
            df = pd.read_excel(excel_file)
            df.replace({r'[^\x00-\x7F]+':''}, regex=True, inplace=True)
            xlsx2html(excel_file,html__output_file)
        if excel_file.endswith('.xls'):
            df = pd.read_excel(excel_file)
            df.replace({r'[^\x00-\x7F]+':''}, regex=True, inplace=True)
            excel_file= excel_file.replace('.xls','.xlsx')
            df.to_excel(excel_file, index= False)
            xlsx2html(excel_file,html__output_file)
        else:
            notice_text = ''
    notice_text = ''
    notice_text += '</br></br></br>' 
    notice_text += 'Excel Extraction Data :'
    HTMLFile = open(html__output_file, "r",encoding="utf-8")
    index = HTMLFile.read()
    S = BeautifulSoup(index, 'lxml')
    notice_text += S.prettify()
    shutil.rmtree(extract_path)
    return notice_text

def eprocure(script_name,domain_url,org_state=None):
    NOTICE_DUPLICATE_COUNT = 0
    MAX_NOTICES_DUPLICATE = 4
    MAX_NOTICES = 2000
    notice_count = 0
    previous_scraping_log_check = fn.previous_scraping_log_check(script_name)
    output_json_folder = "jsonfile"
    documentDownloader = Doc_Download.Doc_Download(script_name)
    output_json_file = OutputJSON.OutputJSON(script_name)
                   
    def extract_and_save_notice_spn(tender_html_element, output_json_file, documentDownloader):
        global notice_data
        global page_details
        notice_data = tender()
        notice_data.script_name = str(script_name) + str('_spn')
        notice_data.currency = 'INR'
        performance_country_data = performance_country()
        performance_country_data.performance_country = 'IN'
        notice_data.performance_country.append(performance_country_data)
        
        notice_data.procurement_method = 2
        notice_data.main_language = "EN"
        notice_data.notice_type = 4
        notice_data.document_type_description = 'Open Tender'

        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text                                           
            publish_date = re.findall('\d+-\w+-\d{4} \d+:\d+ [apAP][mM]',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except:
            pass   

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return


        if 'Corrigendums' in url:
            notice_data.notice_type = 16
            notice_data.script_name = str(script_name) + str('_amd')
        

        try:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
            notice_deadline = re.findall('\d+-\w+-\d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            pass
        
        try:
            document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text                           
            document_opening_time = re.findall('\d+-\w+-\d{4}',document_opening_time)[0]
            notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%b-%Y').strftime('%Y-%m-%d')
        except:
            pass

        try:
            notice_data.notice_url = WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'a'))).get_attribute('href')
            if ("&session=T" in notice_data.notice_url):
                notice_data.notice_url = notice_data.notice_url.replace('&session=T', '')
            logging.info(notice_data.notice_url)
            page_details=documentDownloader.page_details
            fn.load_page(page_details, notice_data.notice_url, 100)
        except:
            pass
            
        try:
            Reference_number = page_details.find_element(By.XPATH,"//*[contains(text(),'Tender Reference Number')]//following::td[1]").text
            notice_no = page_details.find_element(By.XPATH,"//*[contains(text(),'Tender ID')]//following::td[1]").text
            notice_data.notice_no = str(Reference_number)+str(notice_no)
        except:
            pass

        try:
            notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Type")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
            pass

        try:
            notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Category")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
            pass
            
        try:
            notice_data.notice_title = page_details.find_element(By.XPATH,"//*[contains(text(),'Title')]//following::td[1]").text
            if len(notice_data.notice_title) <= 5 or notice_data.notice_title in title_list:
                notice_data.notice_title = page_details.find_element(By.XPATH,"//*[contains(text(),'Work Description')]//following::td[1]").text
            notice_data.local_title = notice_data.notice_title
        except:
            pass
        
        try:
            notice_data.local_description = page_details.find_element(By.XPATH,"//*[contains(text(),'Work Description')]//following::td[1]").text
            if len(notice_data.local_description) <= 5 or notice_data.local_description in title_list:
                notice_data.local_description = page_details.find_element(By.XPATH,"//*[contains(text(),'Title')]//following::td[1]").text
            notice_data.notice_summary_english = notice_data.local_description
        except:
            pass
            
        try:
            customer_details_data = customer_details()

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Organisation Chain")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass


            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Inviting Authority')]//following::tr/td/table/tbody/tr[2]/td[2]").text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
            
            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Inviting Authority')]//following::tr/td/table/tbody/tr[1]/td[2]").text                                           
            except:
                pass

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Pincode")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
            customer_details_data.org_state = org_state
            customer_details_data.org_country = 'IN'
            customer_details_data.org_language = 'EN'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        try:
            netbudgetlc = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Value in')]//following::td").text
            notice_data.netbudgetlc = float(re.sub("[^\d\.]", "", netbudgetlc))
            notice_data.est_amount = notice_data.netbudgetlc
        except:
            pass


        try:
            document_purchase_start_time = page_details.find_element(By.XPATH,"//*[contains(text(),'Document Download / Sale Start Date')]//following::td").text                                        
            document_purchase_start_time = re.findall('\d+-\w+-\d{4} \d+:\d+',document_purchase_start_time)[0]
            notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d-%b-%Y %H:%M').strftime('%Y/%m/%d')
        except:
            pass

        
        try:
            document_purchase_end_time = page_details.find_element(By.XPATH,"//*[contains(text(),'Document Download / Sale End Date')]//following::td").text                                         
            document_purchase_end_time = re.findall('\d+-\w+-\d{4} \d+:\d+',document_purchase_end_time)[0]
            notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d-%b-%Y %H:%M').strftime('%Y/%m/%d')
        except:
            pass

        try:
            pre_bid_meeting_date = page_details.find_element(By.XPATH,"//*[contains(text(),'Pre Bid Meeting Date')]//following::td").text
            pre_bid_meeting_date = re.findall('\d+-\w+-\d{4}',pre_bid_meeting_date)[0]
            notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d-%b-%Y').strftime('%Y/%m/%d')
        except:
            pass

        try:
            document_cost = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Fee in ₹')]//following::td").text
            if '.' in document_cost:
                document_cost = document_cost.split('.')[0]
            notice_data.document_cost = float(re.sub("[^\d]", "",document_cost ))
        except:
            pass

        try:
            earnest_money_deposit = page_details.find_element(By.XPATH, "//*[contains(text(),'EMD Amount in ₹')]//following::td").text
            notice_data.earnest_money_deposit = re.sub("[^\d\.]", "",earnest_money_deposit)
        except:
            pass

        try:
            contract_duration = page_details.find_element(By.XPATH, "//*[contains(text(),'Bid Validity(Days)')]//following::td[1]").text
            notice_data.contract_duration = 'Bid Validity(Days) '+str(contract_duration)
        except:
            pass

        try:
            notice_data.notice_contract_type = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Category')]//following::td").text
        except:
            pass

        try:
            WebDriverWait(page_details, 20).until(EC.presence_of_element_located((By.LINK_TEXT, 'Tendernotice_1.pdf'))).click()
        except:
            pass    

        try:
            WebDriverWait(page_details, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR ,'#captchaImage'))).get_attribute('src')
            captcha_image(page_details,None,'Tendernotice_1.pdf')
            WebDriverWait(page_details, 20).until(EC.presence_of_element_located((By.LINK_TEXT, 'Tendernotice_1.pdf'))).click()
        except:
            pass

        try:
            file_dwn = documentDownloader.file_download()
            attachments_data = attachments()
            attachments_data.file_name = 'Tendernotice_1'
            attachments_data.file_type = 'pdf'
            attachments_data.external_url = str(file_dwn[0])
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
        except:
            pass

        try:
            notice_data.category = page_details.find_element(By.XPATH, "//*[contains(text(),'Product Category')]//following::td[1]").text
            cpv_list = fn.CPV_mapping('assets/eprocure_CPV_mapping.csv',notice_data.category)
            for cpv in cpv_list:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = cpv
                notice_data.cpvs.append(cpvs_data)
        except:
            pass

        try:
            notice_data.notice_text += page_details.find_element(By.XPATH,'//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody').get_attribute('outerHTML')
        except:
            pass
          

        try:
            WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.LINK_TEXT, 'Download as zip file'))).click()
            zip_dwn = documentDownloader.file_download()
            attachments_data = attachments()
            attachments_data.file_name = 'Download as zip file'
            attachments_data.file_type = 'zip'
            attachments_data.external_url = str(zip_dwn[0])
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
        except:
            pass

        notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
        duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(script_name,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
        NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
        if duplicate_check_data[0] == False:
            return
        notice_data.tender_cleanup()
        output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
        logging.info('----------------------------------')
        
    def extract_and_save_notice_ca(tender_html_element, output_json_file, documentDownloader):
        global notice_data
        global page_details
        notice_data = tender()
        notice_data.script_name = str(script_name) + str('_ca')
        notice_data.currency = 'INR'
        performance_country_data = performance_country()
        performance_country_data.performance_country = 'IN'
        notice_data.performance_country.append(performance_country_data)
        
        notice_data.procurement_method = 2
        notice_data.main_language = "EN"
        notice_data.notice_type = 7
        notice_data.document_type_description = 'Results of Tenders'
        notice_data.notice_url = domain_url+'/app?page=ResultOfTenders&service=page'
        
        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text                                           
            publish_date = re.findall('\d+-\w+-\d{4} \d+:\d+ [apAP][mM]',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date )
        except:
            pass   

        if notice_data.publish_date  is not None and notice_data.publish_date  < threshold:
            return

        try:
            notice_data.notice_title = tender_html_element.find_element(By.CSS_SELECTOR,"td:nth-child(4) a").text.strip()
            notice_data.local_title = notice_data.notice_title
        except:
            pass

        try:
            notice_data.notice_no =  tender_html_element.find_element(By.CSS_SELECTOR,"td:nth-child(4)").text.split("\n")[1].strip()
        except:
            pass  
            
        customer_details_data = customer_details()

        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR," td:nth-child(5)").text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_state = org_state
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)

        try:
            WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.XPATH, '/html/body/div/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr[9]/td/table/tbody/tr/td/table/tbody/tr/td[6]/a[2]'))).click()
            file_dwn = documentDownloader.file_download()
            attachments_data = attachments()
            attachments_data.file_name = 'AOC Document'
            attachments_data.external_url = str(file_dwn[0])
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
        except:
            pass 

        try:
            clk = tender_html_element.find_element(By.CSS_SELECTOR,"td:nth-child(4) a").click()
            page_main.switch_to.window(page_main.window_handles[1])
            try:
                netbudgetlc = page_main.find_element(By.XPATH, "//*[contains(text(),'Contract Value :')]//following::td").text
                notice_data.netbudgetlc = float(re.sub("[^\d\.]", "", netbudgetlc))
                notice_data.est_amount = notice_data.netbudgetlc
            except:
                pass
            lot_details_data = lot_details()
            lot_details_data.lot_number = 1
            lot_details_data.lot_title  = notice_data.notice_title
            lot_details_data.lot_description  = notice_data.notice_title
            lot_details_data.lot_title_english  = notice_data.notice_title
            notice_data.is_lot_default = True
            lot_details_data.lot_description_english  = notice_data.notice_title
            lot_details_data.lot_netbudget_lc = notice_data.netbudgetlc
            for single_record in page_main.find_elements(By.XPATH,'//*[@id="bidTableView"]/tbody/tr')[2:]:
                try:
                    award_details_data = award_details()
                    netawardvaluelc = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
                    award_details_data.netawardvaluelc = float(re.sub("[^\d\.]", "", netawardvaluelc))
                    
                    award_details_data.bidder_name =  single_record.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
                    
                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            try:
                notice_data.notice_text +=  page_main.find_element(By.XPATH, '//*[@id="aocSummaryForm"]/table/tbody/tr[3]/td/table').get_attribute('outerHTML')
            except:
                pass

            page_main.switch_to.window(page_main.window_handles[0])
        except:
            pass
        notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_title) 
        duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(script_name,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
        NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
        if duplicate_check_data[0] == False:
            return
        notice_data.tender_cleanup()
        output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
        logging.info('----------------------------------')
    #-----------------------------------main body
    try:
        arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost']
        page_main = fn.init_chrome_driver(arguments)
        page_details = fn.init_chrome_driver(arguments)
        th = date.today() - timedelta(1)
        threshold = th.strftime('%Y/%m/%d')
        logging.info("Scraping from or greater than: " + threshold)
        urls = [domain_url+'/app?page=FrontEndAdvancedSearch&service=page',
        domain_url+'/app?page=FrontEndAdvancedSearch&&service=page',
        domain_url+'/app?page=FrontEndLatestActiveCorrigendums&service=page',
        domain_url+'/app?page=ResultOfTenders&service=page']
        for url in urls:
            logging.info(url)
            logging.info('----------------------------------')
            if 'ResultOfTenders' not in url:   
                fn.load_page(page_main, url)
                if "FrontEndAdvancedSearch&service=page" in url:            
                    status = Select(page_main.find_element(By.NAME, 'TenderType'))
                    status.select_by_index(1)
                    time.sleep(2)
                if 'FrontEndAdvancedSearch&&service=page' in url:
                    status = Select(page_main.find_element(By.NAME, 'TenderType'))
                    status.select_by_index(2)
                    time.sleep(2)
                try:
                    captcha_image(page_main)
                    for page_no in range(2,400):
                        page_check = WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr[6]'))).text
                        for tender_html_element in WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH,'//*[@id="table"]/tbody'))).find_elements(By.CSS_SELECTOR, 'tr')[1:-1]:
                            extract_and_save_notice_spn(tender_html_element,output_json_file,documentDownloader)
                            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                                break
                            notice_count += 1  
                            if notice_count == 50:
                                output_json_file.copyFinalJSONToServer(output_json_folder)
                                output_json_file = OutputJSON.OutputJSON(script_name)
                                notice_count = 0
                        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                            break
                        try:           
                            next_page = WebDriverWait(page_main, 5).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                            page_main.execute_script("arguments[0].click();",next_page)
                            logging.info("Next page")
                            WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr[6]'),page_check))
                            try:
                                captcha_image(page_main)
                            except:
                                pass
                        except:
                            logging.info("No next page")
                            break
                except:
                    pass
                
            elif 'ResultOfTenders' in url:
                keywords = ['Construction','Supply','Maintenance','Repair','Procurement', 'empanelment', 'renovation', 'consultancy']
                page_main.quit()
                page_main = documentDownloader.page_details
                fn.load_page(page_main, url)
                for keyword in keywords:
                    try:
                        captcha_image(page_main,keyword)
                        page_check = WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr[9]/td/table/tbody/tr/td/table/tbody/tr[2]'))).text
                        for tender_html_element in WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH,'//*[@id="table"]/tbody'))).find_elements(By.CSS_SELECTOR, 'tr')[1:-1]:
                            extract_and_save_notice_ca(tender_html_element,output_json_file,documentDownloader)
                            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                                break
                            notice_count += 1
                    except:
                        pass
        logging.info("Finished processing. Scraped {} notices".format(notice_count))
    except Exception as e:
        raise e
        logging.info("Exception:"+str(e))
    finally:
        page_main.quit()
        page_details.quit() 
        output_json_file.copyFinalJSONToServer(output_json_folder)
