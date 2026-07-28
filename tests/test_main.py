import io
import logging
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.main import (create_data_frame, create_temp_file, env_vars_init,
                      init_winnings_check, process_data_frame)

valid_mock_env_vars = {
    "area": "london",
    "purchase_date": "2024-02-26",
    "bond_value": "25000"
}

mock_data_csv_file_name = "mock_data_frame.csv"

@pytest.fixture(autouse=True)
def disable_logging():
    # Disables all logging calls of severity CRITICAL and below
    logging.disable(logging.CRITICAL)
    yield
    # Restores logging after the tests finish
    logging.disable(logging.NOTSET)

def test_missing_env_vars_as_none():
    with pytest.raises(ValueError):
        env_vars_init(None, None, None)

def test_temp_file_exists():
    path = create_temp_file()
    assert path.exists() is True

def get_empty_excel_bytes() -> bytes:
    buffer = io.BytesIO()
    data = [["Skipped row 1"], ["Skipped row 2"], ["column_header"]] ##Simulates two skipped rows and then header name, as first 2 rows skipped in main
    df = pd.DataFrame(data) 
    with pd.ExcelWriter(buffer) as writer:
        df.to_excel(writer, index=False, header=False)
    return buffer.getvalue()

def test_create_data_frame_raises_on_empty():
    # 1. ARRANGE: Create a MagicMock for the response
    mock_response = MagicMock()
    mock_response.content = get_empty_excel_bytes()

    # 2. ACT & ASSERT
    with pytest.raises(RuntimeError):
        create_data_frame(mock_response)

def get_incorrect_headers() -> pd.DataFrame:
    buffer = io.BytesIO()
    data = [
        ["Skipped row 1", "-", "-", "-", "-", "-"], 
        ["Skipped row 2", "-", "-", "-", "-", "-"], 
        ["incorrect_header_1", "incorrect_header_2", "incorrect_header_3", "incorrect_header_4", "incorrect_header_5", "incorrect_header_6"],
        ["dummy_value", "dummy_value", "dummy_value", "dummy_value", "dummy_value", "dummy_value"],
            ]
    df = pd.DataFrame(data)
    with pd.ExcelWriter(buffer) as writer:
        df.to_excel(writer, index=False, header=False)
    df = pd.read_excel(buffer, skiprows=2)
    return df

def test_process_data_frame_has_expected_headers():
    # 1. ARRANGE: Create a MagicMock for the response
    mock_response = MagicMock()
    mock_response.data_frame = get_incorrect_headers()

    # 2. ACT & ASSERT
    with pytest.raises(KeyError):
        process_data_frame(mock_response.data_frame)

def test_init_winnings_check_raises_with_missing_area():
    absolute_path = (Path(__file__).parent / mock_data_csv_file_name).resolve()
    print(f"path is {absolute_path.name}")
    with pytest.raises(KeyError):
        init_winnings_check(absolute_path, "non-existent-area", valid_mock_env_vars["purchase_date"], valid_mock_env_vars["bond_value"])

def test_init_winnings_check_raises_with_correct_area():
    absolute_path = (Path(__file__).parent / mock_data_csv_file_name).resolve()
    result = init_winnings_check(absolute_path, valid_mock_env_vars["area"], valid_mock_env_vars["purchase_date"], valid_mock_env_vars["bond_value"])
    assert result
    
