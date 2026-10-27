#!/usr/bin/env python
import asyncio
import os
from typing import Coroutine
import httpx
import certifi

from pymongo import ASCENDING

from cbio_auth import async_get_cbio_session_id
from benchmark_tools import BenchmarkTimes
import cbio_logger
import cbio_tools_arg_parser
import output_manager
from genomic_types import CnvEventTypeEnum
import cbio_api_helper

logger = cbio_logger.initialize_logging(__name__)

# CNA lookup dictionary
cna_lookup_dic = {
    "-2": "Homozygous deletion",
    "-1": "Heterozygous deletion",
    "0": "Neutral",
    "1": "Gain",
    "2": "High level amplification"
}

# Sample attribute dictionary
sample_attr_dict = {
    'MSI_STABILITY': ' '
}

def generate_oncoKB_dict() -> dict:
    """
    Generate a dictionary from the OncoKB annotated variants file.
    
    Returns:
        dict: A dictionary with keys as gene:protein_change and values as oncogenicity and mutation effect.
    """
    oncoKB_dict = {}
    # this can be run standalone or outside of the module, make the path relative to the current module
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, '..', 'data', 'allAnnotatedVariants.txt')
    with open(file_path) as f:
        for line in f.readlines()[1:]:
            parts2 = line.strip().split("\t")
            key = "%s:p.%s" % (parts2[3], parts2[4])
            oncoKB_dict[key] = {"ONCOGENICITY": parts2[6], "MUTATION_EFFECT": parts2[7]}
    return oncoKB_dict


def fetch_sample_data(cbio_session_id: str, study_id: str) -> list[dict]:
    """
    Fetch sample data for a given study ID.
    
    Args:
        study_id (str): The study ID.
        cbio_session_id (str): The cBioPortal session ID.
    
    Returns:
        list[dict]: A list of sample data dictionaries.
    """

    logger.info("Fetching sample data...")
    sample_url = f'https://cbioportal.ca/cbioportal/api/studies/{ study_id }/samples'
    headers_cookie = 'JSESSIONID=' + cbio_session_id
    # Define the headers
    headers = {
        'User-Agent': 'PMatch-Assembler',
        'Cookie': headers_cookie,
        'Content-Type': 'application/json'
    }

    try:
        sample_response = httpx.get(sample_url, headers=headers)
        if sample_response.is_error:
            logger.error(f"Failed to retrieve sample data with status {sample_response.status_code}")
            raise httpx.HTTPStatusError(f"Failed to retrieve sample data with status {sample_response.status_code}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise e
    
    logger.info("Finished fetching sample data.")
    return sample_response.json()

async def fetch_mutation_data(study_id: str, cbio_session_id: str, sample_list: dict) -> list[dict]:
    """
    Fetch mutation data for a given study ID and sample list.
    
    Args:
        study_id (str): The study ID.
        cbio_session_id (str): The cBioPortal session ID.
        sample_list (list[str]): The list of sample IDs.
    
    Returns:
        list[dict]: A list of mutation data dictionaries.
    """
    logger.info("Fetching mutation data...")
    # Docs: https://cbioportal.ca/cbioportal/api/swagger-ui/index.html?urls.primaryName=default#/Mutations/fetchMutationsInMolecularProfileUsingPOST
    mutation_url = f'https://cbioportal.ca/cbioportal/api/molecular-profiles/{ study_id }_mutations/mutations/fetch' 
    
    headers_cookie = 'JSESSIONID=' + cbio_session_id

    # Define the headers
    headers = {
        'User-Agent': 'PMatch-Assembler',
        'Cookie': headers_cookie,
        'Content-Type': 'application/json'
    }

    result: list[dict] = await cbio_api_helper.fetch_paginated_data(
        log_title="fetch_mutation_data",
        logger=logger,
        method="POST",
        url=mutation_url,
        headers=headers,
        params={ "projection": "DETAILED" },
        body=sample_list,
        page_size=5000,
        max_concurrent_requests=5,
    )
    
    logger.info("Finished fetching mutation data.")
    return result

async def fetch_cnv_data(
        study_id: str, 
        cbio_session_id: str, 
        sample_list: list[str]
    ):
    """
    Fetch CNV data for a given study ID and sample list.
    
    Args:
        study_id (str): The study ID.
        cbio_session_id (str): The cBioPortal session ID.
        sample_list (list[str]): The list of sample IDs.

    Returns:
        A list of CNV data dictionaries.
    """

    cnv_url = f'https://cbioportal.ca/cbioportal/api/molecular-profiles/{ study_id }_gistic/discrete-copy-number/fetch' 
    
    headers_cookie = 'JSESSIONID=' + cbio_session_id

    # Define the headers
    headers = {
        'User-Agent': 'PMatch-Assembler',
        'Cookie': headers_cookie,
        'Content-Type': 'application/json'
    }

    result: list[dict] = []

    async with httpx.AsyncClient(verify=certifi.where()) as client:
        logger.info("Fetching CNV data...")
    
        concurrent_requests: Coroutine = []
        timeout = httpx.Timeout(60.0)  # Set a 10-second timeout for each request

        concurrent_requests.append(
            client.post(cnv_url, headers=headers, params={ 'projection': 'DETAILED' }, json=sample_list, timeout=timeout)
        )
        concurrent_requests.append(
            client.post(
                cnv_url, 
                headers=headers, 
                params={ 'projection': 'DETAILED', 'discreteCopyNumberEventType': CnvEventTypeEnum.GAIN }, 
                json=sample_list,
                timeout=timeout
            )
        )
        concurrent_requests.append(
            client.post(
                cnv_url, 
                headers=headers, 
                params={ 'projection': 'DETAILED', 'discreteCopyNumberEventType': CnvEventTypeEnum.HETLOSS }, 
                json=sample_list,
                timeout=timeout
            )
        )

        # wait for all requests to complete
        batched_responses: list[httpx.Response] = await asyncio.gather(*concurrent_requests)
        # Add responses to the result list
        for response in batched_responses:
            currEventType = response.request.url.params.get("discreteCopyNumberEventType")
            if response.is_error:
                logger.error(f"Failed to retrieve CNV data for [{ currEventType }] : {response.status_code} - {response.content}")
                raise Exception(f"Failed to retrieve CNV data: {response.status_code} - {response.content}")
            data = response.json()
            logger.info(f"Event Type [{currEventType}] of CNV data fetched. Contains {len(data)} records.")
            result.extend(data)
    
    logger.info("Finished fetching CNV data.")
    return result

async def fetch_sv_data(cbio_session_id: str, sv_sample_list: dict) -> list[dict]:
    """
    Fetch structural variant data for a given study ID and sample list.
    
    Args:
        study_id (str): The study ID.
        cbio_session_id (str): The cBioPortal session ID.
        sv_sample_list (dict): The dict containing the list of sample molecular identifiers.
    
    Returns:
        A list of structural variant data dictionaries.
    """

    logger.info("Fetching SV data...")
    
    headers_cookie = 'JSESSIONID=' + cbio_session_id

    # Define the headers
    headers = {
        'User-Agent': 'PMatch-Assembler',
        'Cookie': headers_cookie,
        'Content-Type': 'application/json'
    }

    sv_url = 'https://cbioportal.ca/cbioportal/api/structural-variant/fetch'
    async with httpx.AsyncClient(verify=certifi.where()) as client:
        timeout = httpx.Timeout(60.0)
        response = await client.post(sv_url, headers=headers, json=sv_sample_list, timeout=timeout)
        if response.is_error:
            logger.error(f"Failed to retrieve SV data: {response.status_code}")
            raise Exception(f"Failed to retrieve SV data: {response.status_code}")
        
        logger.info("Finished fetching structural variant data.")
        return response.json()

async def fetch_clinical_data(cbio_session_id: str, study_id: str) -> list[dict]:
    """
    Fetch clinical data for a given study ID.
    
    Args:
        cbio_session_id (str): The cBioPortal session ID.
        study_id (str): The study ID.
    
    Returns:
        list[dict]: A list of clinical data dictionaries.
    """

    logger.info("Fetching clinical data...")
    headers_cookie = 'JSESSIONID=' + cbio_session_id
    # Define the headers
    headers = {
        'User-Agent': 'PMatch-Assembler',
        'Cookie': headers_cookie,
        'Content-Type': 'application/json'
    }

    clinical_url = 'https://cbioportal.ca/cbioportal/api/clinical-data-table/fetch'
    async with httpx.AsyncClient(verify=certifi.where()) as client:
        response = await client.post(clinical_url, headers=headers, json={ "studyIds": [ study_id ] })
        if response.is_error:
            logger.error(f"Failed to retrieve clinical data: {response.status_code}")
            raise Exception(f"Failed to retrieve clinical data: {response.status_code}")
        logger.info("Finished fetching clinical data.")
        return response.json()

def generate_data_sample_lists(study_id: str, sample_data: list[dict]) -> tuple[dict, dict]:
    """
    Generate sample data lists for mutation and CNV data.
    
    Args:
        sample_data (list[dict]): The sample data.
    
    Returns:
        tuple[dict, dict]: A tuple containing request_data_sample_list, request_data_sv_sample_list sample lists.
    """
    request_data_sample_list = {}
    sample_id_list = []
    request_data_sv_sample_list = {}
    sv_sample_id_list = []
    
    for item in sample_data:
        sample_id_list.append(item['sampleId'])
        sv_map = {}
        sv_map['molecularProfileId'] = f'{ study_id }_structural_variants'
        sv_map['sampleId'] = item['sampleId']
        sv_sample_id_list.append(sv_map)
    request_data_sample_list['sampleIds'] = sample_id_list
    request_data_sv_sample_list['sampleMolecularIdentifiers'] = sv_sample_id_list

    return request_data_sample_list, request_data_sv_sample_list

async def fetch_cbio_data(study_id: str, cbio_session_id: str, request_data_sample_list: dict, request_data_sv_sample_list: dict) -> list[dict]:
    """
    Fetch all the required data from cBioPortal.
    
    Args:
        study_id (str): The study ID.
        cbio_session_id (str): The cBioPortal session ID.
        request_data_sample_list (dict): The sample data list.
        request_data_sv_sample_list (dict): The structural variant sample data list.

    Returns:
        list[dict]: A list of fetched data in the order [mutation_data, cnv_data, sv_data, clinical_data].
    """
    results = await asyncio.gather(
            fetch_mutation_data(study_id, cbio_session_id, request_data_sample_list),
            fetch_cnv_data(study_id, cbio_session_id, request_data_sample_list),
            fetch_sv_data(cbio_session_id, request_data_sv_sample_list),
            fetch_clinical_data(cbio_session_id, study_id),
        )
    mutation_data = results[0]
    cnv_data = results[1]
    sv_data = results[2]
    clinical_data = results[3]
    return mutation_data, cnv_data, sv_data, clinical_data

async def post_process(study_id: str, oncoKB_dict: dict, clinical_data: list[dict], mutation_data: list[dict], cnv_data: list[dict], sv_data: list[dict]) -> list[dict]:
    """
    Post-process the fetched data to create a list of sample dictionaries.
    
    Args:
        study_id (str): The study ID.
        oncoKB_dict (dict): The OncoKB dictionary.
        clinical_data (list[dict]): The clinical data.
        mutation_data (list[dict]): The mutation data.
        cnv_data (list[dict]): The CNV data.
        sv_data (list[dict]): The structural variant data.
    
    Returns:
        list[dict]: A list of processed sample dictionaries.
    """

    sample_list = []

    # Process mutation data
    for item in mutation_data:
        sample_dict = {}
        sample_dict['SAMPLE_ID'] = item['sampleId']
        sample_dict['TRUE_HUGO_SYMBOL'] = item['gene']['hugoGeneSymbol']
        sample_dict['TRUE_PROTEIN_CHANGE'] = 'p.' + item['proteinChange']
        sample_dict['TRUE_VARIANT_CLASSIFICATION'] = item['mutationType']
        sample_dict['VARIANT_CATEGORY'] = 'MUTATION'
        sample_dict['CNV_CALL'] = ''
        sample_dict['WILD_TYPE'] = 'false'
        sample_dict['CHROMOSOME'] = 'chr' + item['chr']
        sample_dict['POSITION'] = item['startPosition']
        sample_dict['TRUE_CDNA_CHANGE'] = ''
        sample_dict['REFERENCE_ALLELE'] = item['referenceAllele']
        # Left blank because Exon data is not available in CBioPortal - See CTM-686
        sample_dict['TRUE_TRANSCRIPT_EXON'] = ''
        sample_dict['CANONICAL_STRAND'] = '+'

        sample_dict['ALLELE_FRACTION'] = 0.0
        if 'tumorRefCount' in item and item['tumorRefCount'] != 0:
            sample_dict['ALLELE_FRACTION'] = round(item["tumorAltCount"] / (item["tumorAltCount"] + item["tumorRefCount"]), 10)

        key = ":".join([item['gene']['hugoGeneSymbol'], 'p.'+item['proteinChange']])

        # Add OncoKB data if available
        try:
            sample_dict['ONCOGENICITY'] = oncoKB_dict[key]["ONCOGENICITY"]
        except BaseException:
            sample_dict['ONCOGENICITY'] = 'unknown'
        
        try:
            sample_dict['MUTATION_EFFECT'] = oncoKB_dict[key]["MUTATION_EFFECT"]
        except BaseException:
            sample_dict['MUTATION_EFFECT'] = 'unknown'
        
        sample_dict['LEFT_PARTNER_GENE'] = ''
        sample_dict['RIGHT_PARTNER_GENE'] = ''
        sample_dict['MS_STATUS'] = ''
        sample_list.append(sample_dict)

    # Process CNV data
    for item in cnv_data:
        sample_dict = {}
        sample_dict['SAMPLE_ID'] = item['sampleId']
        sample_dict['TRUE_HUGO_SYMBOL'] = item['gene']['hugoGeneSymbol']
        sample_dict['TRUE_PROTEIN_CHANGE'] = ''
        sample_dict['TRUE_VARIANT_CLASSIFICATION'] = ''
        sample_dict['VARIANT_CATEGORY'] = 'CNV'
        try:
            cnv_value = cna_lookup_dic[str(item['alteration'])]
        except BaseException:
            cnv_value = ''
        sample_dict['CNV_CALL'] = cnv_value
        sample_dict['WILD_TYPE'] = ''
        sample_dict['CHROMOSOME'] = ''
        sample_dict['POSITION'] = ''
        sample_dict['TRUE_CDNA_CHANGE'] = ''
        sample_dict['REFERENCE_ALLELE'] = ''
        sample_dict['TRUE_TRANSCRIPT_EXON'] = ''
        sample_dict['CANONICAL_STRAND'] = ''
        sample_dict['ALLELE_FRACTION'] = ''
        sample_dict['ONCOGENICITY'] = ''
        sample_dict['MUTATION_EFFECT'] = ''
        sample_dict['LEFT_PARTNER_GENE'] = ''
        sample_dict['RIGHT_PARTNER_GENE'] = ''
        sample_dict['MS_STATUS'] = ''
        sample_list.append(sample_dict)

    # Process structural variant data
    for item in sv_data:
        sample_dict = {}
        sample_dict['SAMPLE_ID'] = item['sampleId']
        sample_dict['TRUE_HUGO_SYMBOL'] = ''
        sample_dict['TRUE_PROTEIN_CHANGE'] = ''
        sample_dict['TRUE_VARIANT_CLASSIFICATION'] = ''
        sample_dict['VARIANT_CATEGORY'] = 'SV'
        sample_dict['CNV_CALL'] = ''
        sample_dict['WILD_TYPE'] = ''
        sample_dict['CHROMOSOME'] = ''
        sample_dict['POSITION'] = ''
        sample_dict['TRUE_CDNA_CHANGE'] = ''
        sample_dict['REFERENCE_ALLELE'] = ''
        sample_dict['TRUE_TRANSCRIPT_EXON'] = ''
        sample_dict['CANONICAL_STRAND'] = ''
        sample_dict['ALLELE_FRACTION'] = ''
        sample_dict['ONCOGENICITY'] = ''
        sample_dict['MUTATION_EFFECT'] = ''
        if 'site1HugoSymbol' in item:
            sample_dict['LEFT_PARTNER_GENE'] = item['site1HugoSymbol']
        else:
            sample_dict['LEFT_PARTNER_GENE'] = ''
        if 'site2HugoSymbol' in item:
            sample_dict['RIGHT_PARTNER_GENE'] = item['site2HugoSymbol']
        else:
            sample_dict['RIGHT_PARTNER_GENE'] = ''
        sample_dict['MS_STATUS'] = ''
        sample_list.append(sample_dict)

    # Process clinical data
    sample_dict = {}
    for item in clinical_data['sampleClinicalData']:
        clinical_attr = item['clinicalAttributeId']
        clinical_value = item['value']
        sample_key = item['uniqueSampleKey']
        sample_id = item['sampleId']
        patient_id = item['patientId']
        study_id = item['studyId']

        if item['uniqueSampleKey'] in sample_dict:
            pass
        else:
            sample_dict[sample_key] = {}
            sample_dict[sample_key]['sampleId'] = sample_id
            sample_dict[sample_key]['patientId'] = patient_id
            sample_dict[sample_key]['studyId'] = study_id

        if clinical_attr in sample_attr_dict:
            sample_dict[sample_key][clinical_attr] = clinical_value

    # Add clinical data to sample list
    for x in sample_dict:
        if 'MSI_STABILITY' in sample_dict[x]:
            sample_row_dict = {}
            sample_row_dict['SAMPLE_ID'] = sample_dict[x]['sampleId']
            sample_row_dict['TRUE_HUGO_SYMBOL'] = ''
            sample_row_dict['TRUE_PROTEIN_CHANGE'] = ''
            sample_row_dict['TRUE_VARIANT_CLASSIFICATION'] = ''
            # !!! If the study is OCTANE, set VARIANT_CATEGORY to 'SIGNATURE'
            sample_row_dict['VARIANT_CATEGORY'] = 'SIGNATURE' if study_id == 'OCTANE' else ''
            sample_row_dict['CNV_CALL'] = ''
            sample_row_dict['WILD_TYPE'] = ''
            sample_row_dict['CHROMOSOME'] = ''
            sample_row_dict['POSITION'] = ''
            sample_row_dict['TRUE_CDNA_CHANGE'] = ''
            sample_row_dict['REFERENCE_ALLELE'] = ''
            sample_row_dict['TRUE_TRANSCRIPT_EXON'] = ''
            sample_row_dict['CANONICAL_STRAND'] = ''
            sample_row_dict['ALLELE_FRACTION'] = ''
            sample_row_dict['ONCOGENICITY'] = ''
            sample_row_dict['MUTATION_EFFECT'] = ''
            sample_row_dict['LEFT_PARTNER_GENE'] = ''
            sample_row_dict['RIGHT_PARTNER_GENE'] = ''
            sample_row_dict['MS_STATUS'] = sample_dict[x]['MSI_STABILITY']
            sample_list.append(sample_row_dict)
    return sample_list

async def pull_genomic_data(study_id: str, output_dir: str, output_ip: str):
    """
    Main function to pull genomic data for a given study ID.
    
    Args:
        study_id (str): The study ID.
    """
    logger.info("Starting genomic data pull script...")
    benchmark = BenchmarkTimes()
    benchmark.set_start_time()

    # Get the session ID
    logger.info("Logging into CBio Portal...")
    benchmark.set_login_start_time()
    cbio_session_id = await async_get_cbio_session_id()
    benchmark.set_login_end_time()
    logger.info("Successfully logged in.")

    # Fetch the data
    logger.info("Begin fetch requests...")
    benchmark.set_req_start_time()

    sample_data = fetch_sample_data(cbio_session_id, study_id)
    # clinical_data = fetch_clinical_data(cbio_session_id, study_id)
    request_data_sample_list, request_data_sv_sample_list = generate_data_sample_lists(study_id, sample_data)
    mutation_data, cnv_data, sv_data, clinical_data = await fetch_cbio_data(study_id, cbio_session_id, request_data_sample_list, request_data_sv_sample_list)
    
    benchmark.set_req_end_time()
    oncoKB_dict = generate_oncoKB_dict()

    # Post-process the data
    logger.info("Post-processing data...")
    benchmark.set_post_processing_start_time()
    
    
    sample_list = await post_process(study_id, oncoKB_dict, clinical_data, mutation_data, cnv_data, sv_data)
    benchmark.set_post_processing_end_time()
    logger.info("Finished all post-processing.")

    # Export the data to a file
    if output_dir:
        output_manager.export_to_file(f"genomic_data_{ study_id }.csv", sample_list)

    # Export the data to MongoDB
    if output_ip:
        indexes = [
            ('VARIANT_CATEGORY', ASCENDING),
            ('TRUE_HUGO_SYMBOL', ASCENDING),
            ('UVA_STATUS', ASCENDING),
            ('RIGHT_PARTNER_GENE', ASCENDING),
            ('CNV_CALL', ASCENDING),
            ('APOBEC_STATUS', ASCENDING),
            ('TRUE_PROTEIN_CHANGE', ASCENDING),
            ('TEMOZOLOMIDE_STATUS', ASCENDING),
            ('SAMPLE_ID', ASCENDING),
            ('CLINICAL_ID', ASCENDING),
            ('POLE_STATUS', ASCENDING),
            ('MMR_STATUS', ASCENDING),
            ('MOLECULAR_FUNCTION', ASCENDING),
            ('TRUE_VARIANT_CLASSIFICATION', ASCENDING),
            ('TABACCO_STATUS', ASCENDING),
            ('LEFT_PARTNER_GENE', ASCENDING)
        ]
        output_manager.export_to_mongodb(output_ip, f"genomic", sample_list, indexes)

    benchmark.set_end_time()
    logger.info(str(benchmark))

if __name__ == "__main__":
    parser = cbio_tools_arg_parser.generate_default_arg_parser()
    # parser.add_argument("-avf", "--all_annotated_variants_file", type=str, required=True, help="The file containing all annotated variants.")
    args: cbio_tools_arg_parser.CBioToolsArgParser = parser.parse_args()
    asyncio.run(pull_genomic_data(args.study_id, args.output_dir, args.output_ip))