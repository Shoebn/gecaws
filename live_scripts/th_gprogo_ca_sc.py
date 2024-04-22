import subprocess

python_scripts = ["th_gprogo.py", "cross_check_th_gprogo.py"]

for script in python_scripts:
    try:
        print("python "+ script+" 5 3 1 1")
        subprocess.run("python "+ script+" 5 3 1 1", check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running the script '{script}': {e}")
