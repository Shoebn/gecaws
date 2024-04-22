from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "br_conlicitacao"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download
import subprocess
import json
import os
import gec_common.web_application_properties as application_properties

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "br_conlicitacao"
    
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
page_main = Doc_Download.page_details
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
    
    
    notice_data.main_language = 'PT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)
  
    notice_data.currency = 'BRL'
    notice_data.procurement_method = 2
    notice_data.notice_url = 'https://consulteonline.conlicitacao.com.br'
    
    
    
    if 'licitacao_id' in tender_html_element:
        notice_data.notice_type = 7

    try:
        local_title = tender_html_element["objeto"]
        if 'https' in local_title: 
            notice_data.local_title = local_title.split('https')[0].strip()
        elif 'www' in local_title:
            notice_data.local_title = local_title.split('www')[0].strip()
        else:
            notice_data.local_title = local_title
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in notice_title: {}".format(type(e).__name__))
        pass
    
    try:
        additional_tender_url = tender_html_element["objeto"]
        if 'www' in additional_tender_url:
            notice_data.additional_tender_url = 'https://'+ additional_tender_url.split('**')[-2].strip()
        elif 'https' in additional_tender_url:
            notice_data.additional_tender_url = additional_tender_url.split('*')[-2].strip()
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = str(tender_html_element["id"])
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        deadline = tender_html_element['datahora_prazo']
        if deadline == '' or deadline == None:
            deadline = tender_html_element['datahora_abertura']
        notice_deadline = re.findall('\d{4}-\d+-\d+ \d+:\d+:\d+',deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_type == 7: 
        notice_data.script_name = "br_conlicitacao_ca"
        try:
            publish_date = tender_html_element['data_fonte']
            publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
        
        # if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        #     return
        
        try:
            notice_data.related_tender_id = str(tender_html_element['licitacao_id'])
            notice_data.notice_url = 'https://consulteonline.conlicitacao.com.br/minhas_licitacoes/management/' + str(notice_data.related_tender_id)
        except Exception as e:
            logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
            pass
    else:
        notice_data.script_name = "br_conlicitacao_spn"
        notice_data.notice_type = 4
        try:
            notice_data.notice_url = 'https://consulteonline.conlicitacao.com.br/minhas_licitacoes/management/' + str(notice_data.notice_no)
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            pass
        try:
            notice_data.publish_date = published_date
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
        
        # if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        #     return
        
        try:
            related_tender_id = tender_html_element['edital']
            notice_data.related_tender_id = re.findall('\w+/\d+/\d+',related_tender_id)[0]
        except Exception as e:
            logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
            pass
        

    try:
        document_type_description = tender_html_element['objeto']
        if 'Licitação Eletrônica' in document_type_description or 'Licitação eletrônica' in document_type_description:
            notice_data.document_type_description = 'Licitação eletrônica'
        else:
            document_type_description_regex = re.findall('\*\s\w+\s\w+\s\*',document_type_description)[0]
            notice_data.document_type_description = document_type_description_regex.replace('*','')
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
        
    try:
        attach_data = tender_html_element['documento']
        for data in attach_data:
            attachments_data = attachments()
            external_url = subprocess.getoutput('curl -XGET https://consultaonline.conlicitacao.com.br' + str(data['url'])+' -H "x-auth-token:6818d1ac-1659-4f73-88a2-c4511b13342d" -o' +str(client_dwn_dir)+'/bidt.html')
            page_main.get(str(client_dwn_dir)+'/bidt.html')
            ex_url = page_main.find_element(By.CSS_SELECTOR,'body > a').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])            
            attachments_data.file_name = data['filename'] 
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.netbudgetlc =float(tender_html_element['valor_estimado'])
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
                                                   
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'BR'
        customer_details_data.org_language = 'PT'

        try:
            customer_info = tender_html_element['orgao']
        except:
            pass

        try:
            customer_data2 = tender_html_element['observacao']
        except:
            pass

        customer_details_data.org_name = customer_info['nome']
      

        try:
            org_address = customer_info['endereco']
            if 'www3' in org_address:
                pass
            else:
                customer_details_data.org_address = org_address
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass


        try:
            customer_details_data.org_city = customer_info['cidade']
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        try:
            phone_no = customer_info['telefone']
            phones = ''
            for phone in phone_no:
                phones += phone
                phones += ','
            org_phone = phones.rstrip(',')
            if org_phone == '':
                customer_details_data.org_phone = customer_data2.split('Telefone:')[1].split('\n')[0]
            else:
                customer_details_data.org_phone = org_phone
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass


        try:
            customer_details_data.postal_code = customer_info['codigo']
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = customer_data2.split('E-mail:')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        lot_data = tender_html_element['item']
        if 'Itens de Material' in lot_data:
            lot_number = 1
            lots = lot_data.split('Itens de Material\r\n----------------------------------------\r\n')[1]
            for each_lot in lots.split('----------'):
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number

                lot_details_data.lot_title = each_lot.split('-')[1].split('\n')[0].strip()
                try:
                    lot_details_data.lot_actual_number = each_lot.split('-')[0].strip()
                    if 'Grupos' in lot_details_data.lot_actual_number:
                        continue
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                except Exception as e:
                    logging.info("Exception in lot_title_english: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_description = each_lot.split('-')[1].split('\n')[1].split('Tratamento Diferenciado')[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                except Exception as e:
                    logging.info("Exception in lot_description_english: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_quantity = float(each_lot.split('Quantidade:')[1].split('\n')[0].strip())
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_quantity_uom = lot_data.split('fornecimento:')[1].split('\n')[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass
                if lot_details_data.lot_title != None and lot_details_data.lot_title != '':
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1
        elif 'Quantidade' in lot_data:
            lot_number = 1
            lots = lot_data.split('Código Item Unid.')[1]
            for each_lot in lots.split('\n')[1:]:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number

                lot_title = each_lot.split('-')[1:]
                lot_details_data.lot_title = ','.join(lot_title)

                try:
                    lot_details_data.lot_quantity = float(each_lot.split(' ')[-1].strip())
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_actual_number = each_lot.split('-')[0].split(' ')[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

                if lot_details_data.lot_title != None and lot_details_data.lot_title != '':
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1
                
        elif 'Código Item' in lot_data:
            lot_number = 1
            for each_lot in lot_data.split('Código Item:')[1:]:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                try:
                    lot_quantity = each_lot.split('Qtde:')[1].split('\n')[0]
                    if '.' in lot_quantity:
                        lot_details_data.lot_quantity = float(lot_quantity.replace('.','').replace(',','.'))
                    else:
                        lot_details_data.lot_quantity = float(lot_quantity.replace(',','.',1))
                except Exception as e:
                        logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                        pass

                lot_details_data.lot_title = each_lot.split('Descrição')[1]

                try:
                    lot_actual_number = each_lot.split('\n')[0]
                    if ':' in lot_actual_number:
                        lot_details_data.lot_actual_number = lot_actual_number.replace(':','').replace('\r','')
                    else:
                        lot_details_data.lot_actual_number = lot_actual_number
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass


                try:
                    lot_details_data.lot_quantity_uom = lot_data.split('UF:')[1].split('\n')[0].strip()
                except:
                    try:
                        lot_details_data.lot_quantity_uom = lot_data.split('Unidade de fornecimento:')[1]
                    except Exception as e:
                        logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                        pass

                if lot_details_data.lot_title != None and lot_details_data.lot_title != '':
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1

        elif 'Descrição' in lot_data:
            lot_number = 1
            each_lot = lot_data.split('\n')[1:]
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            lots = ','.join(each_lot)
            try:
                lot_details_data.lot_actual_number = re.findall('ID-[0-9]+',lots)[0]
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_title = each_lot[0].split(lot_details_data.lot_actual_number)[1].strip()
            
            if lot_details_data.lot_title != None and lot_details_data.lot_title != '':
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
            
        else:
            lot_number = 1
            for each_lot in lot_data.split('\n')[:-1]:

                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                try:
                    lot_details_data.lot_actual_number = each_lot.split(' - ')[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_title = each_lot.replace(lot_details_data.lot_actual_number,'').replace('-','').strip()

                if lot_details_data.lot_title != None and lot_details_data.lot_title != '':
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_text = json.dumps(tender_html_element)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
        
#     last_json.close() 
    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline)
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    # if duplicate_check_data[0] == False:
    #     return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body

folders_to_create = ['br_conlicitacao_down_file', 'br_conlicitacao_extract_file']

# Check if each folder exists, and create it if it doesn't
for folder in folders_to_create:
    folder_path = os.path.join(application_properties.TMP_DIR, folder)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created folder: {folder_path}")
    else:
        print(f"Folder already exists: {folder_path}")

# Now you can use the folder paths as needed
#download_path = os.path.join(application_properties.TMP_DIR, "br_conlicitacao_down_file")
#extract_path = os.path.join(application_properties.TMP_DIR, "br_conlicitacao_extract_file")

download_path = application_properties.TMP_DIR + "/br_conlicitacao_down_file/" 
extract_path =  application_properties.TMP_DIR + "/br_conlicitacao_extract_file/" 
client_json = '/' + 'cliente' + SCRIPT_NAME + "_" + datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
folder_name = '/' + SCRIPT_NAME + "_" + datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
client_dwn_dir = download_path + client_json
tmp_dwn_dir = extract_path + folder_name

if not os.path.exists(download_path):
    os.makedirs(download_path)
elif not os.path.exists(extract_path):
    os.makedirs(extract_path)
else:
    pass

os.makedirs(tmp_dwn_dir)
os.makedirs(client_dwn_dir)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    output = subprocess.getoutput('curl -XGET https://consultaonline.conlicitacao.com.br/api/filtros -H "x-auth-token:6818d1ac-1659-4f73-88a2-c4511b13342d" -o '+str(client_dwn_dir)+'/a.json')
    
    f = open(str(client_dwn_dir)+'/a.json')
    data = json.load(f)
    fst_id = data['filtros'][0]['id']
    f.close()

    output2 = subprocess.getoutput('curl -XGET https://consultaonline.conlicitacao.com.br/api/filtro/'+str(fst_id)+'/boletins?page=1 -H "x-auth-token:6818d1ac-1659-4f73-88a2-c4511b13342d" -o '+str(client_dwn_dir)+'/'+str(fst_id)+'.json')
    file = open(str(client_dwn_dir)+'/'+str(fst_id)+'.json')
    data = json.load(file)
    for secnd_id in data['boletins']:
        second_id = secnd_id['id']
        print(second_id)
        last_output = subprocess.getoutput('curl -XGET https://consultaonline.conlicitacao.com.br/api/boletim/'+str(second_id)+' -H "x-auth-token:6818d1ac-1659-4f73-88a2-c4511b13342d" -o '+str(tmp_dwn_dir)+'/'+str(second_id)+'.json')
        file_path = str(tmp_dwn_dir) +'/'+str(second_id)+'.json'
        print(file_path)
        with open(file_path, 'r', encoding='utf8') as data:
            last_json = json.load(data)
            pub_date = last_json['boletim']
            publ_date = pub_date['datahora_fechamento']
            publication_date = re.findall('\d{4}-\d+-\d+ \d+:\d+:\d+',publ_date)[0]
            published_date = datetime.strptime(publication_date,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
            if published_date is not None and published_date < threshold:
                break
                
            for tenders in last_json:
                if 'licitacoes' in tenders:
                    for tender_html_element in last_json['licitacoes']:
                        extract_and_save_notice(tender_html_element)
                        
                        if notice_count == 50:
                            output_json_file.copyFinalJSONToServer(output_json_folder)
                            output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                            notice_count = 0
                            
                elif 'acompanhamentos' in tenders:
                    for tender_html_element in last_json['acompanhamentos']:
                        extract_and_save_notice(tender_html_element)
                        
                        if notice_count == 50:
                            output_json_file.copyFinalJSONToServer(output_json_folder)
                            output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                            notice_count = 0
    file.close()
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
    # os.remove(tmp_dwn_dir)
    # os.remove(client_dwn_dir)
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
