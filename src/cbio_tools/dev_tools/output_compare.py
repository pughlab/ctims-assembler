#!/usr/bin/env python3

"""
Module Docstring:
Compare two CSV files for equality regardless of row order.

Purpose: As changes are made to the cbio tools, it is important to ensure that the output of the tools remains consistent.
This script can be used to compare the output of a tool before and after a change to ensure that the changes did not affect the output.

Usage: python output_compare.py old_output.csv new_output.csv
"""

import pandas as pd
import argparse
import sys

def read_csv_file(file_path: str) -> pd.DataFrame:
    """
    Reads a CSV file and returns a DataFrame with all columns as strings.
    """
    try:
        # Read everything as string, no type conversion
        return pd.read_csv(file_path, dtype=str)
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        sys.exit(1)

def compare_files(df1: pd.DataFrame, df2: pd.DataFrame) -> bool:
    """
    Compares two dataframes treating all values as strings.
    Returns True if they contain the same data regardless of row order.
    """
    if set(df1.columns) != set(df2.columns):
        print("\nColumn mismatch:")
        print(f"File 1 contains {len(df1.columns)} columns")
        print(f"File 2 contains {len(df2.columns)} columns")
        print(f"Columns in file 1 but not in file 2: {set(df1.columns) - set(df2.columns)}")
        print(f"Columns in file 2 but not in file 1: {set(df2.columns) - set(df1.columns)}")
        print(f"File 1 columns ({ list(df1.columns) }): {list(df1.columns)}")
        print(f"File 2 columns ({ list(df1.columns) }): {list(df2.columns)}")
        return False

    if len(df1) != len(df2):
        print(f"\nRow count mismatch:")
        print(f"File 1: {len(df1)} rows")
        print(f"File 2: {len(df2)} rows")
        return False

    # Convert each DataFrame to a set of tuples for comparison
    rows1 = {tuple(row) for _, row in df1.iterrows()}
    rows2 = {tuple(row) for _, row in df2.iterrows()}

    if rows1 == rows2:
        return True

    # Find and display differences
    print("\nContent differences found:")
    only_in_first = rows1 - rows2
    only_in_second = rows2 - rows1
    
    if only_in_first:
        print("\nRows only in first file (up to 5):")
        for row in list(only_in_first)[:5]:
            print(f"  {row}")
            
    if only_in_second:
        print("\nRows only in second file (up to 5):")
        for row in list(only_in_second)[:5]:
            print(f"  {row}")
            
    return False

def main():
    parser = argparse.ArgumentParser(description='Compare two CSV files for equality regardless of row order')
    parser.add_argument('file1', help='First CSV file')
    parser.add_argument('file2', help='Second CSV file')
    args = parser.parse_args()

    print(f"Reading files...")
    df1 = read_csv_file(args.file1)
    df2 = read_csv_file(args.file2)

    print("Comparing files...")
    if compare_files(df1, df2):
        print("\nFiles contain the same data (ignoring row order)")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()