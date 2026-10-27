import json

from pandas import DataFrame
from src.test_suite import utils as test_utils


def test_filtered_refactored_genomic_code(generated_refactored_genomic_df: DataFrame, genomic_config):
    config_fp = genomic_config["script_input"]["config_file"]
    with open(config_fp) as f:
        config = json.load(f)
    filters = config["filters"]["maf"]["Variant_Classification"]
    for chunk in generated_refactored_genomic_df:
        has_filtered_val = chunk['TRUE_VARIANT_CLASSIFICATION'].isin(filters)
        assert(has_filtered_val, False)
