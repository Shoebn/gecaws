# import subprocess

# python_scripts = ["json_import.py", "cubeRM_export.py", "cube_schema_validator.py","Cube_ftp_upload.py","dg_old_export.py","dg_old_ftp_upload.py"] #,"dg3_export.py","dg3_ftp_upload.py"

# for script in python_scripts:
#     try:
#         subprocess.run(["python3", script], check=True)
#     except subprocess.CalledProcessError as e:
#         print(f"Error running the script '{script}': {e}")
