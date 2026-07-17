import datetime
import time 
import requests
import io
import tempfile 
import csv
import difflib 
import os 
import json
import zipfile
import pandas as pd
from pathlib import Path

##TODO: 
## - Put in logging at various levels, controlled by env vars

def create_temp_file():
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".xlsx", delete=False) as temp_file:
        global path
        path = Path(temp_file.name)
        temp_file.write(get_excel_file())
        print(f"Placed Premium Bond Winnings Excel sheet at {path}. Exists: {path.exists()}")

#Downloading premium Bonds Winning Sheet
def get_excel_file():
    months_dict: dict[int, str] = {
    1: "january", 2: "february", 3: "march", 4: "may", 5: "april", 6: "june",
    7: "july", 8: "august", 9: "september", 10: "october", 11: "november", 12: "december"
    }
    month: int = datetime.date.today().month
    year: int = datetime.date.today().year
    excel_url: str = f"https://www.nsandi.com/files/asset/xlsx/prize-{months_dict[month]}-{year}.xlsx" ##insert current month dynamically
    print(f"Attempting to download {months_dict[month]}s Premium Bond winngs sheet...")

    try:
        response = requests.get(excel_url, timeout=10) ##Add stream=True to handle large files
        ##TODO: 
        ## - Put in retry logic with jitter in case of 503 errors
        response.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.Timeout) as err:
        raise requests.exceptions.HTTPError(f"There has been an error in the request to {excel_url}.\nError: {err} ")
    
    raw_bytes = response.content ##response.iter_content() can be used to fetch the content in chunks
    excel_data = io.BytesIO(raw_bytes)
    data_frame = pd.read_excel(excel_data, skiprows=2) ##Skip first 2 as not headers #type: ignore 
    ##TODO:
    ## - test logic here if skip rows 2 is somehow not headers - that is a good test
    data_frame = data_frame.dropna(how="all", axis=1) ##Drop all columns which are empty
    data_frame.columns = [
            str(col).lower().replace(" ", "_").strip() for col in data_frame.columns ##Normalize and clean up column names
    ]
    data_frame["area"] = [
            str(value).lower().replace(" ", "_").strip() for value in data_frame["area"] ##Normalize and clean up column names
    ]
    csv_text = data_frame.to_csv(index=False) ##Convert to csv without indexed rows
    return csv_text

def check_if_winner():
    ##TODO:
    ## - Break up the function into smaller more manageable chunks
    with open(path, mode="r", encoding="utf-8") as file:
        pb_area: str | None = os.getenv("PB_AREA")
        pb_date_of_purchase: str | None = os.getenv("PB_DATE_OF_PURCHASE") ## 2021-09-11
        pb_val_of_bond: str | None = os.getenv("PB_VAL_OF_BOND") ## 50000

        ##TODO:
        ## - Check to make sure any of the environment variables are present and not None! Use try except if its None (raise value error)
        ## - Make the variable names more obvious to those who may not know the context of premium bonds

        csv_dict_reader = csv.DictReader(file)
        raw_area_codes: list[str | None] = [row.get("area") for row in csv_dict_reader]
        ##TODO:
        ## - Check to make sure the list does not contain None! Use try except if its None (raise value error)
        unique_area_codes = set(raw_area_codes)

        print(f"Resolved Value for PB_AREA: {pb_area}\nResolved Value for PB_DATE_OF_PURCHASE: {pb_date_of_purchase}\nResolved Value for PB_VAL_OF_BOND: {pb_val_of_bond}")

        print(f"Finding the closest matching area codes as per your PB_AREA environment variable: {os.getenv("PB_AREA")}...")

        try:
            area_matches: list[str] = difflib.get_close_matches(pb_area, unique_area_codes, n=3, cutoff=0.6) #type: ignore #Returns 3 since London has 3 sections for example so will check date, amount for all of them
            print(f"The closest matching area codes as per your PB_AREA environment variable are: {area_matches}")
            # time.sleep(3)
        except TypeError as err:
            raise TypeError(f"Erroor: {err}. The environment variable PB_AREA must be a str. Got {os.getenv("PB_AREA")}")
        
        file.seek(0) ##Set pointer back to start

        winning_matches_results: list[dict[str, str]] = [holding for holding in csv_dict_reader if holding["val_of_bond"] == pb_val_of_bond and holding["area"] in area_matches and holding["dt_of_pur"] == pb_date_of_purchase]

        if winning_matches_results: ##Defaults to false if empty
            message = f"Congratulations, you have {len(winning_matches_results)} potentially matching wins!"
            print(message)
            pretty_printed_result = json.dumps(winning_matches_results, indent=2)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", delete=False) as temp_file:
                temp_file.write(pretty_printed_result)
                results_path = Path(temp_file.name)

            zip_file_name: str = "results.zip"
            with zipfile.ZipFile(zip_file_name, mode="w" ) as zip_file:
                zip_file.write(results_path)

            if os.getenv("GITHUB_OUTPUT") != None: ##GitHub stores the environment variable for us on GitHub runners
                with open(os.getenv("GITHUB_OUTPUT"), "a") as file:
                    file.write(f"RESULTS_PATH={zip_file_name}\n")
                    file.write(f"MESSAGE={message}\n")
                    file.write(f"CREATE_ARTIFACT=True\n")

        else:
            message = f"Unfortunately, there are no matches for you this month!"
            print(message)
            if os.getenv("GITHUB_OUTPUT") != None:
                with open(os.getenv("GITHUB_OUTPUT"), "a") as file:
                    file.write(f"MESSAGE={message}\n")

def cleanup():
    ##Cleanup
    if path.exists():
        print(f"{path} exists hence deleting...") ##Should be in logs instead
        path.unlink()
        print(f"Does {path} exist? {path.exists()}\nCleanup finished!") ##Should be in logs instead

create_temp_file()
check_if_winner()
cleanup()

            

##How to know if you've won premium bonds?

##total v holding = amount in premium bonds

## area = {area_code}

##Find area code, make a set of values added into a list

##Add duplicate code to functions to follow Dont Repeat Yourself (DRY). Add return statements to the functions

