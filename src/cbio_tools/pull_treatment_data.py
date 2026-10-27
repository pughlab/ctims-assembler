#!/usr/bin/env python
import asyncio

import certifi
import urllib3

import httpx
from pymongo import ASCENDING

from cbio_auth import async_get_cbio_session_id
from benchmark_tools import BenchmarkTimes
import cbio_logger
import cbio_tools_arg_parser
import output_manager
import cbio_api_helper


# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = cbio_logger.initialize_logging(__name__)

async def retrieve_clinical_events(study_id: str, cbio_session_id: str) -> list[dict]:
    """
    Fetch clinical event data from the cBioPortal API.

    Args:
        study_id (str): The ID of the study to fetch data for.
        cbio_session_id (str): The session ID for authentication.

    Returns:
        list[dict]: A list of dictionaries containing clinical event data.
    """

    logger.info("Fetching data...")

    headers_cookie = 'JSESSIONID=' + cbio_session_id

    # Define the headers
    headers = {
        'User-Agent': 'PMatch-Assembler',
        'Cookie': headers_cookie,
        'Content-Type': 'application/json'
    }

    # Define the URL of the REST API endpoint
    url = f'https://cbioportal.ca/cbioportal/api/studies/{ study_id }/clinical-events'

    page_size = 5000

    result: list[dict] = []

    # The maximum number of concurrent requests to make
    max_concurrent_requests = 5
    result = await cbio_api_helper.fetch_paginated_data(
        log_title="retrieve_clinical_events",
        logger=logger,
        method="GET",
        url=url,
        headers=headers,
        params={ "projection": "DETAILED" },
        page_size=page_size,
        max_concurrent_requests=max_concurrent_requests
    )

    logger.info(f"Finished fetching clinical event data. Total records: {len(result)}")
    return result

async def retrieve_clinical_data(study_id: str, cbio_session_id: str) -> list[dict]:
    """
    Fetch clinical data from the cBioPortal API for a given study ID.

    Args:
        study_id (str): The ID of the study to fetch data for.
        cbio_session_id (str): The session ID for authentication.
    
    Returns:
        list[dict]: A list of dictionaries containing clinical data.
    """

    logger.info("Fetching data...")

    url = 'https://cbioportal.ca/cbioportal/api/clinical-data-table/fetch'
    
    headers_cookie = 'JSESSIONID=' + cbio_session_id

    # Define the headers
    headers = {
        'User-Agent': 'PMatch-Assembler',
        'Cookie': headers_cookie,
        'Content-Type': 'application/json'
    }
    result: list[dict] = []
    async with httpx.AsyncClient(verify=certifi.where()) as client:
        try:
            response = await client.post(url, headers=headers, json={ "studyIds": [ study_id ] })
            if response.is_error:
                logger.error(f"Failed to retrieve data: {response.status_code}")
                raise httpx.HTTPStatusError(f"Failed to retrieve data: {response.status_code}")
            result = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Request responded with bad status: {e}")
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise e
    
    logger.info(f"Finished fetching clinical data. Total records: { len(result) }")

    return result

def post_process_event_data(clinical_event_data: list[dict]) -> list[dict]:
    patient_treatment_list = []

    for item in clinical_event_data:
        patient_id = item['patientId']
        study_id = item['studyId']
        event_type = item['eventType']


        # create new patient treatment dict for each new patient
        treatment_dict = {}
        treatment_dict['PATIENT_ID'] = patient_id
        treatment_dict['STUDY_ID'] = study_id
        treatment_dict['START_DAYS'] = 'NA'
        treatment_dict['STOP_DAYS'] = 'NA'
        treatment_dict['EVENT_TYPE'] = event_type
        treatment_dict['TREATMENT_CATEGORY'] = 'NA'
        treatment_dict['SUBTYPE'] = 'NA'
        treatment_dict['AGENT'] = 'NA'
        treatment_dict['RADIATION_SITE'] = 'NA'
        treatment_dict['RADIATION_DOSE'] = 'NA'
        treatment_dict['INSTANCE'] = 'NA'
        treatment_dict['SURGERY_TYPE'] = 'NA'
        treatment_dict['PERFORMANCE_STATUS'] = 'NA'
        treatment_dict['SPECIMEN_TYPE'] = 'NA'
        treatment_dict['SAMPLE_CLASS'] = 'NA'
        treatment_dict['FIRST_RELAPSE'] = 'NA'
        treatment_dict['IMAGE_DESCRIPTION'] = 'NA'
        treatment_dict['IMAGE_MODALITY'] = 'NA'
        treatment_dict['NUMBER_OF_LESIONS'] = 'NA'
        treatment_dict['TOTAL_TUMOUR_VOL_STR'] = 'NA'

        if item['eventType'] == 'Treatment':
            treatment_dict['EVENT_TYPE'] = 'Treatment'
            treatment_attributes = item['attributes']
            for attr in treatment_attributes:
                attr_key = attr['key']
                attr_value = attr['value']
                if attr_key == 'TREATMENT_TYPE':
                    treatment_dict['TREATMENT_CATEGORY'] = attr_value
                if attr_key == 'SUBTYPE':
                    treatment_dict['SUBTYPE'] = attr_value
                if attr_key == 'AGENT':
                    treatment_dict['AGENT'] = attr_value
                if attr_key == 'RADIATION_SITE':
                    treatment_dict['RADIATION_SITE'] = attr_value
                if attr_key == 'RADIATION_DOSE':
                    treatment_dict['RADIATION_DOSE'] = attr_value
                if attr_key == 'INSTANCE':
                    treatment_dict['INSTANCE'] = attr_value


        elif item['eventType'] == 'Surgery':
            treatment_dict['EVENT_TYPE'] = 'Surgery'
            surgery_attributes = item['attributes']
            for attr in surgery_attributes:
                attr_key = attr['key']
                attr_value = attr['value']
                if attr_key == 'SURGERY_TYPE':
                    treatment_dict['SURGERY_TYPE'] = attr_value
                if attr_key == 'INSTANCE':
                    treatment_dict['INSTANCE'] = attr_value

        elif item['eventType'] == 'Imaging':
            treatment_dict['EVENT_TYPE'] = 'Imaging'
        elif item['eventType'] == 'Relapse':
            treatment_dict['EVENT_TYPE'] = 'Relapse'
        elif item['eventType'] == 'Specimen':
            treatment_dict['EVENT_TYPE'] = 'Specimen'
        elif item['eventType'] == 'ECOG': 
            treatment_dict['EVENT_TYPE'] = 'ECOG'
        
        if 'startNumberOfDaysSinceDiagnosis' in item:
            treatment_dict['START_DAYS'] = item['startNumberOfDaysSinceDiagnosis']
        if 'endNumberOfDaysSinceDiagnosis' in item:
            treatment_dict['STOP_DAYS'] = item['endNumberOfDaysSinceDiagnosis']

        #if item['eventType'] == 'Surgery':
        patient_treatment_list.append(treatment_dict)

    
    return patient_treatment_list

def post_process_clinical_data(clinical_data: list[dict], patient_treatment_list: list[dict]) -> list[dict]:

    # Create a dictionary of patient treatment data where the ID is the key and the value is all rows for that patient
    patient_treatment_dict = {}
    for item in patient_treatment_list:
        patient_id = item['PATIENT_ID']
        if patient_id not in patient_treatment_dict:
            patient_treatment_dict[patient_id] = []
        patient_treatment_dict[patient_id].append(item)

    pat_attr_dict = {
        'AGE': '1',
        'SEX': 'male',
        'OS_STATUS': 'deceased',
        'CENTRE': ' ',
        'PR_STATUS': ' ',
        'ER_STATUS': ' ',
        'HER2_STATUS': ' ',
    }

    pat_attr_dict_treatment = {
        'EVENT_TYPE': '',
        'TREATMENT_CATEGORY': '',
        'SUBTYPE':'',
        'AGENT': '',
        'RADIATION_SITE': '',
        'RADIATION_DOSE': '',
        'SURGERY_TYPE': '',
    }

    patient_dict = {}
    sample_dict = {}
    sample_list = []

    # Take all the rows in the clinical data and add them to the patient dictionary, using the unique patient key as the key
    # The dictionary value is a dictionary of all the clinical data for that patient, where this inner dictionary uses the clinical attribute ID as the key
    for item in clinical_data['patientClinicalData']:
        clinical_attr = item['clinicalAttributeId']
        clinical_value = item['value']
        patient_key = item['uniquePatientKey']
        patient_id = item['patientId']
        study_id = item['studyId']

        # If the patient is not in the dictionary, add them with the patient ID and study ID
        if item['uniquePatientKey'] not in patient_dict:
            patient_dict[patient_key] = {
                'PATIENT_ID': patient_id,
                'STUDY_ID': study_id
            }

        # If the clinical attribute is in the dictionary, add the value to the patient dictionary
        if clinical_attr in pat_attr_dict:
            # Handle special cases where the value in the incoming data must be converted for the output
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
                # Otherwise just add the value directly to the dict
                patient_dict[patient_key][clinical_attr] = clinical_value
    

    # Take all the rows in the clinical data and add them to the sample dictionary, using the unique sample key as the key
    for item in clinical_data['sampleClinicalData']:
        clinical_attr = item['clinicalAttributeId']
        clinical_value = item['value']
        sample_key = item['uniqueSampleKey']
        patient_key = item['uniquePatientKey']
        sample_id = item['sampleId']
        patient_id = item['patientId']
        study_id = item['studyId']

        if item['uniqueSampleKey'] not in sample_dict:
            sample_dict[sample_key] = {}
            sample_dict[sample_key]['SAMPLE_ID'] = sample_id
            sample_dict[sample_key]['PATIENT_ID'] = patient_id
            sample_dict[sample_key]['STUDY_ID'] = study_id

    # For each sample in the sample dictionary, add the treatment data to the outputted sample list
    for sample_key in sample_dict:
        patient_id = sample_dict[sample_key]['PATIENT_ID']
        sample_id = sample_dict[sample_key]['SAMPLE_ID']
        study_id = sample_dict[sample_key]['STUDY_ID']
    
        # If the patient ID from the sample dict is in the patient treatment dictionary, add the treatment data to the outputted sample list
        if patient_id in patient_treatment_dict:
            # For each item in the patient treatment dictionary, add the treatment data to the sample list
            curr_patient_treatment = patient_treatment_dict[patient_id]
            for item in curr_patient_treatment:
                # Find all patient event data for the current patient
                if patient_id == item['PATIENT_ID']: 
                    sample_treatment = {}
                    sample_treatment['SAMPLE_ID'] = sample_id
                    sample_treatment['PATIENT_ID'] = patient_id
                    sample_treatment['STUDY_ID'] = study_id

                    for key in pat_attr_dict_treatment:
                        if key in item:
                            sample_treatment[key] = item[key]
                    sample_list.append(sample_treatment)
    
    return sample_list

def post_process(clinical_event_data: list[dict], clinical_data: list[dict]) -> list[dict]:
    """
    Post-process the fetched clinical event data.

    Args:
        data (dict): The raw clinical event data.

    Returns:
        list[dict]: A list of dictionaries containing processed treatment data.
    """
    logger.info("Post-processing clinical event data...")
    patient_treatment_list = post_process_event_data(clinical_event_data)
    logger.info("Finished processing clinical event data.")
    logger.info("Post-processing clinical data...")
    sample_list = post_process_clinical_data(clinical_data, patient_treatment_list)
    logger.info("Finished processing clinical data.")
    return sample_list

async def pull_treatment_data(study_id: str, output_dir: str, output_ip: str):
    """
    Main function to pull treatment data for a given study ID.

    Args:
        study_id (str): The ID of the study.
    """
    logger.info("Starting treatment data pull script...")
    benchmark = BenchmarkTimes()
    benchmark.set_start_time()

    # Get the session ID
    logger.info("Logging into CBio Portal...")
    benchmark.set_login_start_time()
    cbio_session_id = await async_get_cbio_session_id()
    benchmark.set_login_end_time()
    logger.info("Successfully logged in.")

    # Fetch the data
    logger.info("Starting async API requests...")
    benchmark.set_req_start_time()
    clinical_event_coroutine = retrieve_clinical_events(study_id, cbio_session_id)
    clinical_data_coroutine = retrieve_clinical_data(study_id, cbio_session_id)
    clinical_event_data, clinical_data = await asyncio.gather(
        clinical_event_coroutine, clinical_data_coroutine
    )
    benchmark.set_req_end_time()
    logger.info("Finished async API requests.")

    # Post-process the data
    logger.info("Post-processing data...")
    benchmark.set_post_processing_start_time()
    sample_list = post_process(clinical_event_data, clinical_data)
    benchmark.set_post_processing_end_time()
    logger.info("Finished all post-processing.")
    
    benchmark.set_output_write_start_time()
    # Export the data to a file
    if output_dir:
        output_manager.export_to_file(f"treatment_data_{ study_id }.csv", sample_list)
    
    # Export the data to MongoDB
    if output_ip:
        indexes = [
            ('AGENT', ASCENDING),
            ('SAMPLE_ID', ASCENDING),
            ('CLINICAL_ID', ASCENDING)
        ]
        output_manager.export_to_mongodb(output_ip, f"prior_treatment", sample_list, indexes)
    
    benchmark.set_output_write_end_time()

    benchmark.set_end_time()
    logger.info(str(benchmark))


if __name__ == "__main__":
    parser = cbio_tools_arg_parser.generate_default_arg_parser()
    args: cbio_tools_arg_parser.CBioToolsArgParser = parser.parse_args()

    asyncio.run(pull_treatment_data(args.study_id, args.output_dir, args.output_ip))