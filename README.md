NEPSE Floor Sheet Scraper
Scrapes the daily NEPSE floor sheet from merolagani.com and saves it as a clean CSV. It goes through every page of results, removes duplicate rows, and converts the number columns so you can use the data right away.
What you get
A CSV with one row per transaction: transaction number, symbol, buyer, seller, quantity, rate and amount. `Quantity`, `Rate` and `Amount` are numeric (commas removed).
Setup
You need Python 3.9+ and Google Chrome installed.
```bash
git clone https://github.com/murlijha2025/Nepse_Data_Scraping.git
cd Nepse_Data_Scraping
pip install -r requirements.txt
```
Selenium 4.6+ handles chromedriver automatically, so there's no manual driver download.
Usage
```bash
# today's floor sheet
python floorsheet_scraper.py

# a specific date (mm/dd/yyyy)
python floorsheet_scraper.py -d 10/01/2026

# custom output file, with the browser visible
python floorsheet_scraper.py -d 10/01/2026 -o floorsheet.csv --show-browser
```
Default output file is `data_<mm_dd_yyyy>.csv`.
Option	What it does
`-d`, `--date`	Date as `mm/dd/yyyy` (default: today)
`-o`, `--output`	Output CSV path
`--show-browser`	Run Chrome visibly instead of headless
Known limitations
It only works on days the market was open. If there's no data, it exits with a message.
The page elements are found with absolute XPaths. If merolagani changes its layout, update `DATE_INPUT_XPATH` and `SEARCH_BUTTON_XPATH` at the top of the script.
A full day can be hundreds of pages, so a run takes a few minutes.
Notes
This scrapes a public website. Check the site's terms before using the data for anything beyond personal analysis, and don't hammer it with repeated runs.
Dependencies
`selenium`, `beautifulsoup4`, `pandas`
