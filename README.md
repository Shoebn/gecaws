# gecscraping
Steps to run python script in machine.

1 .First of all ,need to git clone the gecscraping respository in a machine's user.
  
  go to  cmd > 
  enter the command = git clone https://github.com/globalecontent/gecscraping.git.
  It will ask for a verification  code in a browser.
  code will be found in inbox of github registered emailid.
  
  After verification, gecscraping folder  will be downloaded .
  
2. in gecscraping folder there is two folders, live scripts and raw scripts. we are using live scripts to get output json.
   So before the executing the script,need to do some modification in web_apllication_properties.py file.
   .web_apllication_properties file is in gec_common folder in live scripts.
   
   in web_apllication_properties , there is total 3 configurations.
   comment -For Windows Server and -For Linux Server block of code.
   make sure For Local Windows Server configuration is uncommented.
   
   Moreover need to change a path as per your machine,and have to create a folders accoringly. 
   
   
   
3.To run the script, go to cmd ,
 -->cd gecscraping/live_scripts .
 Then write the name of then script want to run.
 -->python fr_boamp_ca.py

It will generate a output as json file which can be find in jsonfile folder.
  
