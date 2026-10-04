"""Scrape the NEPSE floor sheet from merolagani.com and save it as a CSV.

Usage:
    python floorsheet_scraper.py                    # today's floor sheet
    python floorsheet_scraper.py -d 10/01/2026      # a specific date (mm/dd/yyyy)
    python floorsheet_scraper.py --show-browser     # watch the browser work
"""

import argparse
import sys
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://merolagani.com/Floorsheet.aspx"
DATE_FORMAT = "%m/%d/%Y"
TABLE_SELECTOR = "table.table-bordered.sortable"
NO_DATA_TEXT = "Could not find floorsheet matching the search criteria"

# Absolute XPaths break whenever the site changes its layout.
# If the scraper stops working, check these first.
DATE_INPUT_XPATH = "/html/body/form/div[4]/div[3]/div/div/div[1]/div[4]/input"
SEARCH_BUTTON_XPATH = "/html/body/form/div[4]/div[3]/div/div/div[2]/a[1]"

NUMERIC_COLUMNS = ["Quantity", "Rate", "Amount"]


def make_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    # Selenium 4.6+ downloads/finds the right chromedriver on its own.
    return webdriver.Chrome(options=options)


def search(driver, search_date):
    """Open the floor sheet page and search by date. Returns False if no data."""
    driver.get(URL)
    driver.find_element(By.XPATH, DATE_INPUT_XPATH).send_keys(search_date)
    driver.find_element(By.XPATH, SEARCH_BUTTON_XPATH).click()
    return NO_DATA_TEXT not in driver.page_source


def read_page_table(driver):
    """Return the rows of the table on the current page as a list of lists."""
    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.select_one(TABLE_SELECTOR)
    return [
        [cell.get_text(strip=True) for cell in row.find_all(["th", "td"])]
        for row in table.find_all("tr")
    ]


def scrape_all_pages(driver, timeout=20):
    """Click through every page of results and collect all rows."""
    rows, pages = [], 0
    while True:
        rows.extend(read_page_table(driver))
        pages += 1
        try:
            old_table = driver.find_element(By.CSS_SELECTOR, TABLE_SELECTOR)
            next_btn = driver.find_element(By.LINK_TEXT, "Next")
        except NoSuchElementException:
            break  # no "Next" link means last page
        driver.execute_script("arguments[0].click();", next_btn)
        try:
            # Wait for the old table to be replaced so we never read the same page twice.
            WebDriverWait(driver, timeout).until(EC.staleness_of(old_table))
        except TimeoutException:
            print(f"Page {pages + 1} didn't load in {timeout}s, stopping early.")
            break
    print(f"Scraped {pages} pages.")
    return rows


def clean(rows):
    """Turn raw rows into a tidy DataFrame with numeric columns."""
    header = rows[0]
    data = [row for row in rows if row != header]  # every page repeats the header
    df = pd.DataFrame(data, columns=header).drop_duplicates()
    df = df.drop(columns=["#"], errors="ignore")
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace(",", ""), errors="coerce")
    return df.reset_index(drop=True)


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape the NEPSE floor sheet.")
    parser.add_argument(
        "-d", "--date",
        default=datetime.today().strftime(DATE_FORMAT),
        help="date as mm/dd/yyyy (default: today)",
    )
    parser.add_argument("-o", "--output", help="output CSV path")
    parser.add_argument("--show-browser", action="store_true", help="don't run headless")
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        datetime.strptime(args.date, DATE_FORMAT)
    except ValueError:
        sys.exit("Date must be mm/dd/yyyy, e.g. 10/01/2026")

    output = args.output or f"data_{args.date.replace('/', '_')}.csv"
    start = datetime.now()

    driver = make_driver(headless=not args.show_browser)
    try:
        if not search(driver, args.date):
            sys.exit(f"No floor sheet found for {args.date}.")
        df = clean(scrape_all_pages(driver))
    finally:
        driver.quit()

    df.to_csv(output, index=False)
    print(f"Saved {len(df)} rows to {output} in {datetime.now() - start}.")


if __name__ == "__main__":
    main()
