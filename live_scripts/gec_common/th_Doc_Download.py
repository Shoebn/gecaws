import os
import shutil
import time
import uuid
from datetime import datetime
import platform
import requests
import base64
import gec_common.web_application_properties as application_properties
from gec_common import functions as fn
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

def today_formatted():
    return datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


class Doc_Download:
    folder_name = None
    tmp_dwn_dir = None
    attachment_dir = None

    def __init__(self, script_name):
        system_name = platform.uname().system
        if 'Windows' in system_name:
            self.folder_name = '/' + script_name + "_" + today_formatted()
            tmp_dwn = application_properties.TMP_DIR + self.folder_name
            self.tmp_dwn_dir = tmp_dwn.replace('/',"\\")        
            attachment_dir = application_properties.NOTICE_ATTACHEMENTS_DIR + self.folder_name
            self.attachment_dir = attachment_dir.replace('/',"\\") 
        else:
            self.tmp_dwn_dir = application_properties.TMP_DIR + self.folder_name
            self.attachment_dir = application_properties.NOTICE_ATTACHEMENTS_DIR + self.folder_name
        os.makedirs(self.tmp_dwn_dir)
        os.makedirs(self.attachment_dir)
        self.experimental_options = {"prefs": {"download.prompt_for_download": False,"plugins.always_open_pdf_externally": True,"download.default_directory": self.tmp_dwn_dir}}
        arguments= ['ignore-certificate-errors','allow-insecure-localhost','--start-maximized','--headless']
        options = Options()
        for argument in arguments:
            options.add_argument(argument)
        for key, value in self.experimental_options.items():
            options.add_experimental_option(key, value)
        self.page_details = webdriver.Chrome(options=options)

    def latest_download_file(self):
        path = self.tmp_dwn_dir
        os.chdir(path)
        files = sorted(os.listdir(os.getcwd()), key=os.path.getmtime)
        newest = files[-1]
        return newest
        
            
    def switch_tab(self,url1):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response1 = requests.get(url1, headers=headers)


        # Ensure the request was successful
        response1.raise_for_status()
        response_data = response1.json()

        # Step 2: Extract the buildName2 value from the response
        buildName2 = response_data.get('data', {}).get('buildName2')
        if not buildName2:
            raise ValueError("Could not find buildName2 in the response.")

        # Step 3: Make an HTTP post call
        url2 = f"https://process5.gprocurement.go.th/egp-template-service/dant/view-pdf?templateId={buildName2}"
        response2 = requests.post(url2, headers=headers)

        # Ensure the request was successful
        response2.raise_for_status()
        response_data2 = response2.json()

        # Extract base64 string and convert it to a PDF
        base64_string = response_data2.get('data')
        if not base64_string:
            raise ValueError("Could not find data in the response.")

        # Convert base64 to bytes
        pdf_bytes = base64.b64decode(base64_string)
        new_file_name = str(uuid.uuid4())+'.pdf'
        # Write bytes to a PDF file. Set here the path you prefer!
        with open(self.attachment_dir + '/' + new_file_name, 'wb') as file:
            file.write(pdf_bytes)
            file.close()
        resource_url = application_properties.NOTICE_ATTACHMENTS_BASE_URL + self.folder_name + '/' + new_file_name
        return resource_url
        
    def switch_tabZip(self,url1):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response1 = requests.get(url1, headers=headers)

        # Ensure the request was successful
        response1.raise_for_status()
        response_data = response1.json()

        # Step 2: Extract the zipId value from the response
        zipId = response_data.get('data', {}).get('zipId')

        if not zipId:
            raise ValueError("Could not find zipId in the response.")
        
        url2 = f"https://process5.gprocurement.go.th/egp-upload-service/v1/downloadFileTest?fileId={zipId}"
        
        new_file_name = str(uuid.uuid4())+'.zip'
        newest_file_path = application_properties.NOTICE_ATTACHEMENTS_DIR + self.folder_name + '/' + new_file_name
        resource_url = application_properties.NOTICE_ATTACHMENTS_BASE_URL + self.folder_name + '/' + new_file_name

        try:
            # Download the zip file using the requests library
            response = requests.get(url2, headers=headers)
            response.raise_for_status()  # Check for HTTP errors

            with open(newest_file_path, 'wb') as f:
                f.write(response.content)

            print(f"Downloaded {new_file_name} successfully.")

        except requests.exceptions.RequestException as e:
            print(f"Error downloading {resource_url}: {e}")

        return resource_url
    def switch_tabZipAdj(self,url1):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response1 = requests.get(url1, headers=headers)

        # Ensure the request was successful
        response1.raise_for_status()
        response_data = response1.json()

        # Step 2: Extract the zipId value from the response
        zipId = response_data.get('data', {}).get('zipId')

        if not zipId:
            raise ValueError("Could not find zipId in the response.")
        
        url2 = f"https://process5.gprocurement.go.th/egp-upload-service/v1/downloadFileTest?fileId={zipId}"
        
        new_file_name = str(uuid.uuid4())+'.zip'
        newest_file_path = application_properties.NOTICE_ATTACHEMENTS_DIR + self.folder_name + '/' + new_file_name
        resource_url = application_properties.NOTICE_ATTACHMENTS_BASE_URL + self.folder_name + '/' + new_file_name

        try:
            # Download the zip file using the requests library
            response = requests.get(url2, headers=headers)
            response.raise_for_status()  # Check for HTTP errors

            with open(newest_file_path, 'wb') as f:
                f.write(response.content)

            print(f"Downloaded {new_file_name} successfully.")

        except requests.exceptions.RequestException as e:
            print(f"Error downloading {resource_url}: {e}")

        return resource_url
    def switch_tabprice(self,url1):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response1 = requests.get(url1, headers=headers)

        # Ensure the request was successful
        response1.raise_for_status()
        response_data = response1.json()

        # Step 2: Extract the zipId value from the response
        zipId = response_data.get('data', {}).get('zipFileId')

        if not zipId:
            raise ValueError("Could not find zipId in the response.")
        
        url2 = f"https://process5.gprocurement.go.th/egp-upload-service/v1/downloadFileTest?fileId={zipId}"
        
        
        new_file_name = str(uuid.uuid4())+'.zip'
        newest_file_path = application_properties.NOTICE_ATTACHEMENTS_DIR + self.folder_name + '/' + new_file_name
        resource_url = application_properties.NOTICE_ATTACHMENTS_BASE_URL + self.folder_name + '/' + new_file_name

        try:
            # Download the zip file using the requests library
            response = requests.get(url2, headers=headers)
            response.raise_for_status()  # Check for HTTP errors

            with open(newest_file_path, 'wb') as f:
                f.write(response.content)

            print(f"Downloaded {new_file_name} successfully.")

        except requests.exceptions.RequestException as e:
            print(f"Error downloading {resource_url}: {e}")

        return resource_url
        
    def switch_tabwinner(self,url1):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response1 = requests.get(url1, headers=headers)


        # Ensure the request was successful
        response1.raise_for_status()
        response_data = response1.json()

        # Step 2: Extract the buildName2 value from the response
        buildName2 = response_data.get('data', {}).get('templateId')
        if not buildName2:
            raise ValueError("Could not find buildName2 in the response.")

        # Step 3: Make an HTTP post call
        url2 = f"https://process5.gprocurement.go.th/egp-template-service/dwnt/view-pdf-file?templateId={buildName2}"
        
        return url2

    def response_contains_data(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response1 = requests.get(url, headers=headers)
        
        response1.raise_for_status()

        parsed_response = response1.json().get('data', {})

        result = parsed_response is not None

        return result

    def file_download(self):
        while True:
            time.sleep(5)
            newest_file = self.latest_download_file()
            if not ("crdownload" in newest_file or ".tmp" in newest_file):
                break
        file_name = str(uuid.uuid4())
        new_file_name = newest_file.split(".")[-2] +'.'+ newest_file.split(".")[-1]
        new_file_name = file_name+'.'+new_file_name.replace('#','')
        newest_file_path = self.tmp_dwn_dir + '/' + newest_file
        new_file_path = self.tmp_dwn_dir + '/' + new_file_name
        os.rename(newest_file_path, new_file_path)
        resource_url = application_properties.NOTICE_ATTACHMENTS_BASE_URL + self.folder_name + '/' + new_file_name
        shutil.move(new_file_path, self.attachment_dir)
        return resource_url, new_file_name
