import unittest
import pandas as pd
import os
import sys
from pathlib import Path

# Ensure the project root is on sys.path so tests can import project modules (e.g. utils)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from utils import atc_processing


class TestExcelIntegration(unittest.TestCase):
    def setUp(self):
        # Paths to example input files and expected output
        self.file1 = "tests/data/input1.xlsm"
        self.file2 = "tests/data/input2.xlsm"
        self.files = [self.file1, self.file2]
        self.expected_file = "tests/data/expected_output.xlsm"
        self.output_file = "tests/data/output.xlsm"

        # Ensure output file does not exist before test
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def test_merge_excel_files(self):
        # Run the actual merge function
        atc_processing(self.files, self.output_file)

        # Load the output and expected DataFrames
        actual_df = pd.read_excel(self.output_file)
        expected_df = pd.read_excel(self.expected_file)

        # Compare DataFrames (ignore index)
        breakpoint()
        pd.testing.assert_frame_equal(
            actual_df.reset_index(drop=True), expected_df.reset_index(drop=True)
        )

    def tearDown(self):
        # Clean up output file after test
        if os.path.exists(self.output_file):
            os.remove(self.output_file)


if __name__ == "__main__":
    unittest.main()
