#!/usr/bin/env python
import urllib3

import requests
from pymongo import ASCENDING

from cbio_auth import get_cbio_session_id
from benchmark_tools import BenchmarkTimes
import cbio_logger
import cbio_tools_arg_parser
import output_manager

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = cbio_logger.initialize_logging(__name__)

URL = 'https://cbioportal.ca/cbioportal/api/clinical-data-table/fetch'

def fetch_data(study_id: str, cbio_session_id: str) -> requests.Response:
    """
    Fetch clinical data from the cBioPortal API for a given study ID.

    Args:
        study_id (str): The ID of the study to fetch data for.
        cbio_session_id (str): The session ID for authentication.

    Returns:
        requests.Response: The response object containing the clinical data.
    """
    logger.info("Fetching clinical data...")
    headers_cookie = 'JSESSIONID=' + cbio_session_id
    # Define the headers
    headers = {
        'User-Agent': 'PMatch-Assembler',
        'Cookie': headers_cookie,
        'Content-Type': 'application/json'
    }
    # Make a POST request with headers
    try:
        response = requests.post(URL, headers=headers, json={"studyIds": [study_id]})
        response.raise_for_status()  # Raise an HTTPError if the response code is not 200
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while making the HTTP request: {e}")
        raise
    logger.info("Finished fetching clinical data.")
    return response

def post_process(data: dict) -> list[dict]:
    """
    Post-process the clinical data to extract relevant patient and sample information.

    Args:
        data (dict): The raw clinical data from the API response.

    Returns:
        list[dict]: A list of dictionaries containing processed sample data.
    """
    logger.info("Post-processing clinical data...")
    pat_attr_dict = {
        'AGE': '1',
        'GENDER': 'male',
        'OS_STATUS': 'deceased',
        'CENTRE': ' ',
        'PR_STATUS': ' ',
        'ER_STATUS': ' ',
        'HER2_STATUS': ' ',
    }

    pat_attr_dict_new = {
        'AGE': '1',
        'GENDER': 'male',
        'ETHNICITY': 'male',
        'VITAL_STATUS': 'deceased',
        'CENTRE': ' ',
        'PR_STATUS': ' ',
        'ER_STATUS': ' ',
        'HER2_STATUS': ' ',
    }

    sample_attr_dict = {
        'CANCER_TYPE_DETAILED': ' ',
        'ONCOTREE_CODE': ' ',
        'MSI_STABILITY': ' '
    }

    patient_dict = {}
    sample_dict = {}
    
    # Process patient clinical data
    for item in data['patientClinicalData']:
        clinical_attr = item['clinicalAttributeId']
        clinical_value = item['value']
        patient_key = item['uniquePatientKey']
        patient_id = item['patientId']
        study_id = item['studyId']

        if item['uniquePatientKey'] in patient_dict:
            pass
        else:
            patient_dict[patient_key] = {}
            patient_dict[patient_key]['PATIENT_ID'] = patient_id
            patient_dict[patient_key]['STUDY_ID'] = study_id

        if clinical_attr in pat_attr_dict:
            if clinical_attr == 'GENDER':
                patient_dict[patient_key]['GENDER'] = clinical_value
                patient_dict[patient_key]['ETHNICITY'] = clinical_value
            elif clinical_attr == 'OS_STATUS':
                if clinical_value == '0:LIVING':
                    patient_dict[patient_key]['VITAL_STATUS'] = 'LIVING'
                elif clinical_value == '1:DECEASED':
                    patient_dict[patient_key]['VITAL_STATUS'] = 'DECEASED'
                else:
                    patient_dict[patient_key]['VITAL_STATUS'] = 'NA'
            else:
                patient_dict[patient_key][clinical_attr] = clinical_value

    # Process sample clinical data
    for item in data['sampleClinicalData']:
        clinical_attr = item['clinicalAttributeId']
        clinical_value = item['value']
        sample_key = item['uniqueSampleKey']
        patient_key = item['uniquePatientKey']
        sample_id = item['sampleId']
        patient_id = item['patientId']
        study_id = item['studyId']

        if item['uniqueSampleKey'] in sample_dict:
            pass
        else:
            sample_dict[sample_key] = {}
            sample_dict[sample_key]['SAMPLE_ID'] = sample_id
            sample_dict[sample_key]['ONCOTREE_PRIMARY_DIAGNOSIS_NAME'] = 'NA'
            sample_dict[sample_key]['CANCER_TYPE'] = 'NA'
            sample_dict[sample_key]['AGE'] = 'NA'
            sample_dict[sample_key]['GENDER'] = 'NA'
            sample_dict[sample_key]['ETHNICITY'] = 'NA'
            sample_dict[sample_key]['VITAL_STATUS'] = 'NA'
            sample_dict[sample_key]['ER_STATUS'] = 'NA'
            sample_dict[sample_key]['PR_STATUS'] = 'NA'
            sample_dict[sample_key]['HER2_STATUS'] = 'NA'
            sample_dict[sample_key]['CENTRE'] = 'NA'
            sample_dict[sample_key]['PATIENT_ID'] = patient_id
            sample_dict[sample_key]['STUDY_ID'] = study_id
            sample_dict[sample_key]['MS_STATUS'] = 'NA'

            for key in pat_attr_dict_new:
                if key in patient_dict[patient_key]:
                    sample_dict[sample_key][key] = patient_dict[patient_key][key]

        if clinical_attr in sample_attr_dict:
            if clinical_attr == 'CANCER_TYPE_DETAILED':
                sample_dict[sample_key]['ONCOTREE_PRIMARY_DIAGNOSIS_NAME'] = clinical_value
            if clinical_attr == 'ONCOTREE_CODE':
                sample_dict[sample_key]['CANCER_TYPE'] = clinical_value
            if clinical_attr == 'MSI_STABILITY':
                sample_dict[sample_key]['MS_STATUS'] = clinical_value

    sample_list: list[dict] = []
    for x in sample_dict:
        sample_list.append(sample_dict[x])
    
    logger.info("Finished post-processing clinical data.")
    return sample_list

def pull_clinical_data(study_id: str, output_dir: str, output_ip: str):
    """
    Main function to pull clinical data for a given study ID, process it, and export it to a file.

    Args:
        study_id (str): The ID of the study to pull data for.
    """
    logger.info("Starting clinical data pull script...")
    benchmark = BenchmarkTimes()
    benchmark.set_start_time()

    # Get the session ID
    logger.info("Logging into CBio Portal...")
    benchmark.set_login_start_time()
    cbio_session_id = get_cbio_session_id()
    benchmark.set_login_end_time()
    logger.info("Successfully logged in.")

    # Fetch the data
    benchmark.set_req_start_time()
    response = fetch_data(study_id, cbio_session_id)
    benchmark.set_req_end_time()

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        data = response.json()

        # Post-process the data
        benchmark.set_post_processing_start_time()
        sample_list = post_process(data)
        benchmark.set_post_processing_end_time()

        # Export the data to a file
        if output_dir:
            output_manager.export_to_file(f"clinical_data_{ study_id }.csv", sample_list)
        
        # Export the data to MongoDB
        if output_ip:
        # create clinical indexes
            indexes = [
                ('FIRST_LAST', ASCENDING),
                ('ER_STATUS', ASCENDING),
                ('TUMOR_MUTATIONAL_BURDEN_PER_MEGABASE', ASCENDING),
                ('PR_STATUS', ASCENDING),
                ('SAMPLE_ID', ASCENDING),
                ('VITAL_STATUS', ASCENDING),
                ('ONCOTREE_PRIMARY_DIAGNOSIS_NAME', ASCENDING),
                ('MRN', ASCENDING),
                ('GENDER', ASCENDING),
                ('HER2_STATUS', ASCENDING),
                ('BIRTH_DATE_INT', ASCENDING)
            ]
            output_manager.export_to_mongodb(output_ip,f"clinical", sample_list, indexes)

        benchmark.set_end_time()
    else:
        logger.error(f"Failed to retrieve data: {response.status_code}")
    logger.info(str(benchmark))


if __name__ == "__main__":
    parser = cbio_tools_arg_parser.generate_default_arg_parser()
    args: cbio_tools_arg_parser.CBioToolsArgParser = parser.parse_args()

    pull_clinical_data(args.study_id, args.output_dir, args.output_ip)
