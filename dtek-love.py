from playwright.sync_api import sync_playwright
import json
import re
import sys
import argparse

parser = argparse.ArgumentParser(description="My script with optional arguments")
parser.add_argument("-url", type=str, default="https://www.dtek-krem.com.ua/ua/shutdowns", help="Webpage URL")
parser.add_argument("-gpv", type=str, help="Your GPV number only (1.1|1.2...)")
parser.add_argument("-test", type=str, default="false", help="run tests (true/yes|anything else is false))")
parser.add_argument("-tomorrow", type=str, default="false", help="run tests (true/yes|anything else is false))")
args = parser.parse_args()

URL = args.url
gpv = args.gpv
test = args.test.lower() in ("true", "yes")
tomorrow = args.test.lower() in ("true", "yes")
one_day = 86400

def extract_schedule(page_content):
    match = re.search(r"DisconSchedule\.fact\s*=\s*(\{.*\}\s*);?", page_content, re.DOTALL)
    if not match:
        raise ValueError("Could not find DisconSchedule.fact in the page")
    
    data_str = match.group(1)
    data_json = json.loads(data_str)
    return data_json

def find_and_print_gpv(data, gpv_key, tomorrow):
    timestamp = data["today"]  # or pick any timestamp you want
    if tomorrow:
        timestamp += one_day
    schedule = data["data"][str(timestamp)].get(gpv_key)

    result_string = ""
    if schedule:
        print(f"{gpv_key}:")
        prev_status = "yes"
        prev_hour = "00"
        for hour, status in schedule.items():
            # new range starts
            if prev_status == "yes" or prev_status == "first":
                if status != "yes":
                    result_string += f"{int(prev_hour):02}"
                    if status == "no":
                        result_string += ":00"
                    if status == "first":
                        result_string += f":00-{int(prev_hour):02}:30|->|"
                    if status == "second":
                        result_string += ":30"
            # any range ends
            elif prev_status == "no" or prev_status == "second":
                if status == "yes":
                    result_string +=f"-{int(prev_hour):02}:00|->|"
                elif status == "first":
                    result_string += f"-{int(prev_hour):02}:30|->|"
                elif status == "second":
                    result_string += f"-{int(prev_hour):02}:00|->|{int(prev_hour):02}:30"
                    
            prev_status = status
            prev_hour = hour
        if prev_status == "no" or prev_status == "second":
            result_string += f"-{int(prev_hour):02}:00"
        if result_string.endswith("|->|"):
            result_string = result_string[:-4]
        print(result_string)
    else:
        print(f"{gpv_key} not found for timestamp {timestamp}")
        
def run_test():
    with open("test.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    find_and_print_gpv(data, "GPVtest", False)
    
if test:
    run_test()

if gpv is not None:
    with sync_playwright() as p:
        
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL)
        
        content = page.content()
        #with open("dump.html", "w", encoding="utf-8") as f:
        #   f.write(content)
        
        schedule_data = extract_schedule(content)
        find_and_print_gpv(schedule_data, f"GPV{gpv}",tomorrow)
        
        browser.close()