# Automated Distance Estimator via Google Maps
Short Description:
Given a table with some addresses, this program performs web scrapping on Google Maps to estimate distances. The routes that were already searched, will not be searched again. Instead, they will be saved on 'all_entries.csv' for a later use.

Libraries used:
Selenium
BeautifulSoup
Pandas

Steps:
python -m venv my_env
pip install -r requirements.txt
Download chromedriver.exe from https://chromedriver.chromium.org/
Add chromedriver.exe to directory
pyinstaller --add-data "chromedriver.exe;." --onefile --windowed rechner.py
