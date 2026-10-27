import argparse
import pandas as pd
import logging

from src.tools.assembler_utils.script_logging import init_logger


# from src.tools.script_logging import init_logger


def get_options():
    """
    Parse command-line arguments for the main script using argparse.

    Returns:
        An argparse Namespace object containing the parsed command-line arguments.
    """

    # Create an instance of the ArgumentParser class.
    parser = argparse.ArgumentParser()

    # Add four command-line arguments to the parser object.
    # The "--sample-file", "--patient-file", and "--output" arguments are required.
    # The "--debug" argument is optional.
    parser.add_argument("-s", "--sample-file", type=str, required=True,
                        help="cbioportal clinical sample file e.g data_clinical_samples.txt")
    parser.add_argument("-p", "--patient-file", type=str, required=True,
                        help="cbioportal clinical patient file e.g data_clinical_patients.txt")
    parser.add_argument("-st", "--study-file", type=str, required=True,
                        help="Contains a cancer_study_identifier line. Example: cancer_study_identifier: BRCA_pps")
    parser.add_argument("-o", "--output", type=str, required=True,
                        help="output clinical file for trial match e.g clinical.csv")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="debug mode print to stdout")
    parser.add_argument("-l", "--logto", type=str, required=False,
                        help="the file path to log to. The file will be created if it does not exist.")


    # Parse the command-line arguments and return the result.
    return parser.parse_args()


def get_study_id(args: argparse.Namespace) -> str:
    """
    Read the study ID from a file.

    Args:
        args: An argparse Namespace object containing command-line arguments.

    Returns:
        A string representing the study ID.
    """

    with open(args.study_file) as f:
        for line in f.readlines():
            if line.startswith("cancer_study_identifier"):
                return line.strip().split(": ", 1)[1]

#function map_MS_STATUS takes a string as an argument and returns a string
def map_ms_status(msi_stability: str) -> str:
    """
    Map the MSI_STABILITY column to the MS_STATUS column.

    Args:
        msi_stability: A string representing the MSI_STABILITY column.

    Returns:
        A string representing the MS_STATUS column.
    """
    
    # If msi_stability is "Stable", "High", or "Indeterminate", return msi_stability
    if msi_stability == "Stable" or msi_stability == "High" or msi_stability == "Indeterminate":
        return msi_stability
     # Otherwise, return "NA"
    else:
        return "NA"


def prepare_sample_data(args: argparse.Namespace) -> None:
    """
    Read patient and sample data from files, combine them into a new file, and return the output filename.

    Args:
        args: An argparse Namespace object containing command-line arguments.
        p_dic: A dictionary containing patient data, with patient IDs as keys.

    Returns:
        A string representing the output filename.
    """

    logging.debug(f"Merging files - patient_file: {args.patient_file} - sample_file: {args.sample_file}")

    patient_df: pd.DataFrame = pd.read_csv(args.patient_file, delimiter="\t", skiprows=4)
    sample_df: pd.DataFrame = pd.read_csv(args.sample_file, delimiter="\t", skiprows=4)

    logging.debug(f"Sample file before merge: {sample_df.to_string()}")
    logging.debug(f"Patient file before merge: {sample_df.to_string()}")

    # Perform join on sample and patient dataframes, join on the PATIENT_ID column.
    # merged_df = sample_df.merge(patient_df, on='PATIENT_ID', suffixes=('_sample', '_patient'), how='left', validate="many_to_one")
    merged_df = pd.merge(sample_df, patient_df, on='PATIENT_ID', how='left', suffixes=('_left', '_right'))

    # Create the ONCOTREE_PRIMARY_DIAGNOSIS_NAME column, it is a copy of the sample's CANCER_TYPE_DETAILED column
    merged_df['ONCOTREE_PRIMARY_DIAGNOSIS_NAME'] = sample_df['CANCER_TYPE_DETAILED'].str.strip()

    # Create the GENDER and ETHNICITY columns, they are copies of the patient file's SEX column
    merged_df['GENDER'] = merged_df['SEX']
    merged_df['ETHNICITY'] = merged_df['SEX']

    # Create the VITAL_STATUS column, it is a copy of the patient's OS_STATUS column
    merged_df['VITAL_STATUS'] = merged_df['OS_STATUS']

    # Remove the original CANCER_TYPE column and replace it with the ONCOTREE_CODE column
    del merged_df['CANCER_TYPE']
    merged_df.rename(columns={"ONCOTREE_CODE": "CANCER_TYPE"}, inplace=True)

    # Create a new column MS_STATUS, set the value to MSI_STABILITY column after applying the map_MS_STATUS function
    merged_df['MS_STATUS'] = merged_df['MSI_STABILITY'].apply(map_ms_status)    

    output_columns = [
        'SAMPLE_ID',
        'ONCOTREE_PRIMARY_DIAGNOSIS_NAME',
        'CANCER_TYPE',
        'AGE',
        'GENDER',
        'ETHNICITY',
        'VITAL_STATUS',
        'ER_STATUS',
        'PR_STATUS',
        'HER2_STATUS',
        'CENTRE',
        'PATIENT_ID',
        'MS_STATUS'
    ]

    output_df: pd.DataFrame = merged_df[output_columns]

    logging.debug(f"Merged file: {output_df.to_string()}")
    output_df = output_df.fillna('NA')
    output_df['ONCOTREE_PRIMARY_DIAGNOSIS_NAME'] = output_df['ONCOTREE_PRIMARY_DIAGNOSIS_NAME'].str.strip()
    study_id = get_study_id(args)
    # add a column named "STUDY_ID" to the output_df and set the value for each row to study_id
    output_df['STUDY_ID'] = study_id
    output_df.to_csv(args.output, index=False, lineterminator='\n')


def main():
    args = get_options()
    init_logger(args.debug)
    logging.debug("Args: ", str(args))
    prepare_sample_data(args)


if __name__ == "__main__":
    main()
