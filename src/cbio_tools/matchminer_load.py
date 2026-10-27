import cbio_logger

logger = cbio_logger.initialize_logging(__name__)


def pre_process_clinical_data(data: list[dict]) -> list[dict]:
    """
    Pre-process the clinical data to extract relevant patient and sample information.

    Args:
        data (dict): The raw clinical data from the API response.

    Returns:
        dict: A dictionary containing processed clinical data.
    """
    logger.info("Pre-processing clinical data...")
    ok_clinical_data = []
    for c in data:
        if isinstance(c.get('AGE'), str):
            if c['AGE'] != 'NA':
                c['AGE'] = int(c['AGE'])
            else:
                c['AGE'] = None

        # remove the row if there's no sample_id
        if 'SAMPLE_ID' in c:
            ok_clinical_data.append(c)

    return ok_clinical_data


def pre_process_other_data(db_rw, data: list[dict]) -> list[dict]:
    """
    Pre-process the other data(genomic/prior treatment) to extract relevant patient and sample information.

    Args:
        data (dict): The raw data from the API response.

    Returns:
        dict: A dictionary containing processed data.
    """
    logger.info("Pre-processing data...")
    ok_data = []
    clinical_dict = {item['SAMPLE_ID']: item['_id'] for item in db_rw['clinical'].find({}, {'_id': 1, 'SAMPLE_ID': 1})}
    for g in data:
        if g.get('CLINICAL_ID'):
            ok_data.append(g)
        elif g.get('SAMPLE_ID') in clinical_dict:
            g['CLINICAL_ID'] = clinical_dict[g['SAMPLE_ID']]
            ok_data.append(g)

    return ok_data

