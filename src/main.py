import csv
import datetime
import difflib
import io
import json
import logging
import logging.config
import os
import random
import tempfile
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests
import yaml

log_level = os.getenv("LOG_LEVEL", "DEBUG")
config_path =(Path(__file__).parent.parent / "logging/declarative-config.yaml").resolve()
with open(config_path, "r") as config_file:
    yaml_config = yaml.safe_load(config_file)
yaml_config["handlers"]["console"]["level"] = log_level
logging.config.dictConfig(yaml_config)
logger = logging.getLogger(__name__)

def main():
    area, purchase_date, bond_value = env_vars_init(os.getenv("PB_AREA"), os.getenv("PB_DATE_OF_PURCHASE"), os.getenv("PB_VAL_OF_BOND"))
    path = create_temp_file()
    response = get_file()
    data_frame = create_data_frame(response)
    processed_data_frame = process_data_frame(data_frame)
    convert_to_csv(processed_data_frame, path)
    area_matches = init_winnings_check(path, area, purchase_date, bond_value)
    results_path = check_if_winner(area_matches, path, area, purchase_date, bond_value)
    cleanup(path, results_path)

def env_vars_init(area_code: str | None, date_of_purchase: str | None, val_of_bond: str | None) -> tuple[str | None, str | None, str | None]:
    if area_code is None or date_of_purchase is None or val_of_bond is None:
        msg = f"One of the required environment variables is not set. Got... PB_AREA: {area_code}, PB_DATE_OF_PURCHASE: {date_of_purchase}, PB_VAL_OF_BOND: {val_of_bond}"
        logger.critical(msg)
        raise ValueError(msg)
    pb_area = area_code
    pb_date_of_purchase = date_of_purchase ## 2021-09-11
    pb_val_of_bond = val_of_bond ## 50000

    logger.info(f"""Resolved Value for required env vars is: PB_AREA: {pb_area}, PB_DATE_OF_PURCHASE: {pb_date_of_purchase}, PB_VAL_OF_BOND: {pb_val_of_bond}""")
    return(pb_area, pb_date_of_purchase, pb_val_of_bond) 

def create_temp_file():
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as temp_file:

        path = Path(temp_file.name)

        logger.info(f"Placed Premium Bond Winnings Excel sheet at {path}.")

        return path

## Downloading premium Bonds Winning Sheet
def get_file(max_retries: int =3):
    months_dict: dict[int, str] = {
    1: "january", 2: "february", 3: "march", 4: "april", 5: "may", 6: "june",
    7: "july", 8: "august", 9: "september", 10: "october", 11: "november", 12: "december"
    }
    month: int = datetime.date.today().month
    year: int = datetime.date.today().year
    excel_url: str = f"https://www.nsandi.com/files/asset/xlsx/prize-{months_dict[month]}-{year}.xlsx" ##insert current month dynamically
    logger.info(f"Attempting to download {months_dict[month]}s Premium Bond winngs sheet...")
    delay: int = 1
    for attempt in range(1, max_retries + 1):
        logger.info(f"Attempt {attempt} / {max_retries}")
        try:
            response = requests.get(excel_url, timeout=10)
            response.raise_for_status() ##Raise any HTTP Errors as exceptions
            return response
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as err:
            if err.response is not None and err.response.status_code < 500:
                msg = f"Failed with client error code {err.response.status_code}. Skipping retry."
                logger.exception(msg)
                raise requests.exceptions.HTTPError(msg)
            else:
                jitter = random.uniform(-0.1 * delay, 0.1 * delay)
                # delay = 1 -> jitter [-0.1, 0.1] -> 0.9 and 1.1s
                # delay = 2 -> jitter [-0.2, 0.2] -> 1.8 and 2.2s
                # delay = 4 -> jitter [-0.4, 0.4] -> 3.6 and 4.4s
                #...
                wait = min(delay * 2, 30) + jitter
                if err.response is not None:
                    logger.critical(f"Failed with server error code {err.response.status_code}. Retrying in {wait:.2f}s")
                else:
                    logger.critical(f"Got empty response from Server: {err.response}. Retrying in {wait:.2f}s")
                time.sleep(wait)
                delay = min(delay * 2, 30)
    else:
        msg = f"All {max_retries} attempts failed"
        logger.critical(msg)
        raise RuntimeError(msg)
        
def create_data_frame(response: requests.Response) -> pd.DataFrame: 
    raw_contents: bytes = response.content
    excel_data: io.BytesIO = io.BytesIO(raw_contents) 
    data_frame: pd.DataFrame = pd.read_excel(excel_data, skiprows=2) ##Skip first 2 as not headers
    if data_frame.empty:
        msg = "DataFrame is empty"
        logger.critical(msg)
        raise RuntimeError(msg)
    return data_frame

def process_data_frame(data_frame: pd.DataFrame) -> pd.DataFrame:
    data_frame = data_frame.dropna(how="all", axis=1) ##Drop all columns which are empty
    data_frame.columns = [str(col).lower().replace(" ", "_").strip() for col in data_frame.columns] ##Normalize and clean up column names.. remove white spaces, replace spaces with underscores and make lower case
    data_frame["area"] = [str(value).lower().replace("  ", " ").replace(" ", "_").strip() for value in data_frame["area"]] ##Normalize and clean up area names.. remove white spaces, replace spaces with underscores, replace double spaces with single spaces and make lower case
    ##TODO    
    ##Vectorize the above
    processed_data_frame = data_frame ##Create new var now the DF is processed

    expected_column_headers = ["prize_value", "winning_bond_no.", "total_v_of_holding", "area", "val_of_bond", "dt_of_pur"] #Check if headers are in the trimmed down intended headers row, notably data_frame.columns
    missing_cols = [col for col in expected_column_headers if col not in data_frame.columns]
    if missing_cols:
        msg = f"Excel sheet is missing required columns: {missing_cols}. Got: {data_frame.columns}"
        logger.critical(msg)
        raise KeyError(msg)

    return processed_data_frame
##Up to here on Tests - Need to test in the csv bit for if the contents of the file is a csv
def convert_to_csv(data_frame: pd.DataFrame, path: Path) -> None:
    csv_text = data_frame.to_csv(index=False) ##Convert to csv without indexed rows
    with open(path, mode="w", encoding="utf-8") as file:
        file.write(csv_text)

def init_winnings_check(path: Path, area: str | None, purchase_date: str | None, bond_value: str | None) -> list[str]:
    with open(path, mode="r", encoding="utf-8") as file:

        csv_dict_reader = csv.DictReader(file) ##Convert the csv file into a python dictionary/map
        raw_area_codes: list[str] = [row["area"] for row in csv_dict_reader]

        unique_area_codes: set[str] = set(raw_area_codes)

        logger.info(f"Finding the closest matching area codes as per PB_AREA environment variable: {area}...")

        area = str(area).lower().replace("  ", " ").replace(" ", "_").strip() ##Normalize pb_area due to string alphabetic nature

        area_matches: list[str] = difflib.get_close_matches(area, unique_area_codes, n=3, cutoff=0.6) #Returns 3 since London has 3 sections for example so will check date, amount for all of them
        logger.info(f"The closest matching area codes as per your PB_AREA environment variable are: {area_matches}")
        
        if not area_matches:
            msg = f"There were no matches for the provided area code: {area}...\nChange your area code to a style that matches the below and try again...\n{random.sample(list(unique_area_codes), 7)}"
            logger.critical(msg)
            raise KeyError(msg)
        
        return area_matches

###

def check_if_winner(area_matches: list[str], path: Path, area: str | None, purchase_date: str | None, bond_value: str | None) -> Path | None:

    with open(path, mode="r", encoding="utf-8") as file:
        csv_dict_reader = csv.DictReader(file)
        winning_matches_results: list[dict[str, str]] = [holding for holding in csv_dict_reader if holding["val_of_bond"] == bond_value and holding["area"] in area_matches and holding["dt_of_pur"] == purchase_date]

        file.seek(0)

        assert len(winning_matches_results) < len([holding for holding in csv_dict_reader]), f"Winning Matches results is greater than, or equal to, the total winning entries in the {path.name} csv file"
        
        if winning_matches_results:
            message = f"Congratulations, you have {len(winning_matches_results)} potentially matching wins!"
            logger.info(message)
            pretty_printed_result = json.dumps(winning_matches_results, indent=2)

            if os.getenv("GITHUB_OUTPUT") is not None: ##GitHub stores the environment variable for us on GitHub runners
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", delete=False) as temp_file:
                    temp_file.write(pretty_printed_result)
                    results_path = Path(temp_file.name)
                zip_file_name: str = "results.zip" ##Used in GitHub actions workflow
                with zipfile.ZipFile(zip_file_name, mode="w" ) as zip_file:
                    zip_file.write(results_path)
                with open(os.environ["GITHUB_OUTPUT"], "a") as file:
                    file.write(f"RESULTS_PATH={zip_file_name}\n")
                    file.write(f"MESSAGE={message}\n")
                    file.write(f"CREATE_ARTIFACT=True\n")
                    return results_path

        else:
            message = f"Unfortunately, there are no matches for you this month!"
            logger.info(message)
            if os.getenv("GITHUB_OUTPUT") != None:
                with open(os.environ["GITHUB_OUTPUT"], "a") as file:
                    file.write(f"MESSAGE={message}\n")

def cleanup(path: Path, results_path: Path | None):
    ##Cleanup
    for temp_file in [path, results_path]:
        if temp_file is not None:
            if temp_file.exists():
                logger.info(f"{temp_file} exists hence deleting...") ##Should be in logs instead
                temp_file.unlink()
                logger.info(f"Cleanup finished!") ##Should be in logs instead
                assert not temp_file.exists(), f"File {temp_file.name} still exists"

if __name__ == "__main__":
    main()

