import argparse
import json

import pandas

from src.tools.assembler_utils.datatypes.config import Config, Filter, MAF
from src.tools.assembler_utils.script_logging import init_logger
import logging
import pandas as pd


# Define argument types
ArgsType = argparse.Namespace
CNADictType = dict[str, dict[str, str]]
OncoKBDictType = dict[str, dict[str, str]]
FusionArrayType = list[dict[str, str]]


def get_options() -> ArgsType:
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--maf-file", type=str, required=False,
                        help="VEP annotated MAF file e.g data_mutations_extended.txt")
    parser.add_argument("-c", "--cna-file", type=str, required=False,
                        help="discrate copy number data from GISTIC2 e.g data_CNA.txt")
    parser.add_argument("-v", "--variants", type=str, required=False,
                        help="oncoKB all annotated variants e.g allAnnotatedVariants.txt")
    #add an argument as a flag to indicate if the MAF file is annotated with oncoKB annotations
    parser.add_argument("-am", "--annotatedmaf", dest="annotatedmaf", required=False, action="store_true",
                        help="oncoKB annotations can be included in the MAF file e.g data_mutations_extended.txt")
    parser.add_argument("-o", "--output-file", type=str, required=True,
                        help="output genomic data file for trial match e.g genomic.csv")
    parser.add_argument("-f", "--fusion-file", type=str, required=False,
                        help="fusion structural variant e.g data_fusions.txt")
    parser.add_argument("-sv", "--data_sv", type=str, required=False,
                        help="e.g data_sv.txt")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="debug mode print to stdout")
    parser.add_argument("-cf", "--config-file", type=str, required=True,
                        help="config file that holds settings for filters")
    parser.add_argument("-dcs", "--data-clinical-samples", type=str, required=True,
                        help="file that holds MSI_STATUS data")

    return parser.parse_args()


def open_config(config_fp: str) -> Config:
    """
    Opens the config file, loads into dictionary
    :param config_fp: File path to config file. Should come from args.
    :return: Loaded config json as a dictionary.
    """
    try:
        with open(config_fp) as f:
            json_data = json.load(f)
        # Deserialize the JSON data into a Config object
            maf = MAF(Variant_Classification=json_data['filters']['maf']['Variant_Classification'])
            filters = Filter(maf=maf)
            config_data = Config(filters=filters)
            return config_data
    except FileNotFoundError as e:
        logging.error(f"Config file could not be found at {config_fp}")


def get_oncoKB_table(variant_file, debug) -> OncoKBDictType:
    oncoKB_dict = {}
    with open(variant_file) as f:
        header = f.readline()
        header_parts = header.strip().split("\t")
        logging.debug([(idx, val) for idx, val in enumerate(header_parts)])
        for line in f.readlines()[1:]:
            logging.debug(line)
            parts2 = line.strip().split("\t")
            key = "%s:p.%s" % (parts2[3], parts2[4])
            oncoKB_dict[key] = {"ONCOGENICITY": parts2[6], "MUTATION_EFFECT": parts2[7]}
    logging.debug(oncoKB_dict.keys())
    logging.debug(oncoKB_dict.values())
    return oncoKB_dict


def get_fusion_array(fusion_file: str) -> FusionArrayType:
    """
    Process a fusion file and return a list of dictionaries containing fusion data objects.

    This function reads the fusion file using pandas, processes the data, and organizes it into
    a dictionary based on the sample ID. It then creates fusion data objects and stores them
    in a list to be returned.

    Args:
        fusion_file (str): Path to the fusion file to be processed.

    Returns:
        list: A list of dictionaries containing fusion data objects.
    """

    # Read the fusion file using pandas and assign column names
    df = pd.read_csv(fusion_file, sep='\t')

    # Get the fusions grouped and keep original order by Tumor_Sample_Barcode
    # Get the unique values of the 'Tumor_Sample_Barcode' column in the original order
    unique_sample_ids = df['Tumor_Sample_Barcode'].unique()

    # Convert the 'Tumor_Sample_Barcode' column to a categorical data type with the original order of categories
    df['Tumor_Sample_Barcode'] = pd.Categorical(df['Tumor_Sample_Barcode'], categories=unique_sample_ids, ordered=True)

    # Group the dataframe by 'SAMPLE_ID' and aggregate the 'Col1' values into lists
    fusion_groups = df.groupby('Tumor_Sample_Barcode', sort=False)['Hugo_Symbol'].apply(list)


    # Initialize an empty list to store the final fusion data objects
    fusion_data = []

    # Process the fusion groups and create fusion data objects
    # Loop through the groups. genes is a list of Hugo_Symbol strings containing either 1, 2 or 4 values
    for sample_barcode, genes in fusion_groups.items():
        num_genes = len(genes)
        # If there are a valid number of genes
        if num_genes in (1, 2, 4):
            # The list should have either a single gene, a single pair of genes or two pairs of genes.
            # Loop by two, for each pair
            for i in range(0, num_genes, 2):
                # Left gene is always i
                left_partner_gene = genes[i]
                # The right gene should be the next item in the array.
                # If the next item in the array does not exist, then use this same gene as the right gene
                right_partner_gene = genes[i+1] if (i+1) < num_genes else genes[i]
                fusion_data.append({
                    "SAMPLE_ID": sample_barcode,
                    "VARIANT_CATEGORY": "SV",
                    "LEFT_PARTNER_GENE": left_partner_gene,
                    "RIGHT_PARTNER_GENE": right_partner_gene
                })
        else:
            logging.error(f"Error: fusion file has more than 2 partners: {sample_barcode}")

    return fusion_data


def process_sample_id(value: str) -> str:
    """
    Modifies the inputted sample ID
    :param value: Value from file
    :return: Modified value
    """

    modified = value.replace("-TD", "-Exome")
    if modified.startswith("OCT-01"):
        modified = modified.replace("_Tumour", "-555Panel")
    return modified

def calculate_allele_fraction(val_1: int, val_2: int):
    try:
        result = val_1 / val_2
        # Round to 10 decimal places
        return round(result, 10)
    except ZeroDivisionError:
        return 0.0

def generate_oncogenicity(val_1, val_2, oncoKB_dict):

    # Retrieve oncogenicity and mutation effect from the OncoKB dictionary, if available
    try:
        # Create a key for OncoKB lookup using HUGO symbol and protein change
        key2 = ":".join([val_1, val_2])
        return oncoKB_dict[key2]["ONCOGENICITY"]
    except:
        return "Unknown"

def generate_mutation_effect(val_1, val_2, oncoKB_dict):

    try:
        # Create a key for OncoKB lookup using HUGO symbol and protein change
        key2 = ":".join([val_1, val_2])
        return oncoKB_dict[key2]["MUTATION_EFFECT"]
    except:
        return "Unknown"


def add_oncogenicity(df, args):
    oncoKB_dict = get_oncoKB_table(args.variants, args.debug)

    df['ONCOGENICITY'] = df.apply(lambda row: (
        generate_oncogenicity(row['TRUE_HUGO_SYMBOL'], row['TRUE_PROTEIN_CHANGE'], oncoKB_dict)
    ), axis=1)
    # MUTATION_EFFECT
    df['MUTATION_EFFECT'] = df.apply(lambda row: (
        generate_mutation_effect(row['TRUE_HUGO_SYMBOL'], row['TRUE_PROTEIN_CHANGE'], oncoKB_dict)
    ), axis=1)
    return df


def add_fusion_array(df, args):
    fusion_array = get_fusion_array(args.fusion_file)
    output_df_cols = df.columns
    for fusion_dict in fusion_array:
        new_row_dict: dict = { col: fusion_dict.get(col, '') for col in output_df_cols }
        new_row_df = pd.DataFrame(new_row_dict, index=[0])
        df = pd.concat([df, new_row_df], ignore_index=True)
    return df


def add_cna(args, output_df):
    cna_lookup_dic = {
        "-2": "Homozygous Deletion",
        "-1": "Heterozygous Deletion",
        "0": "Neutral",
        "1": "Gain",
        "2": "High Amplification"
    }
    cna_df = pd.read_csv(args.cna_file, delimiter="\t")
    # Loop through column names. The column names are the sample IDs.
    # Skip the first column, as it is 'Hugo_Symbol'.
    # For each column, loop through the rows and add them to the output if their value is valid
    for column in cna_df.columns[1:]:
        for index, row in cna_df.iterrows():
            value = row[column]
            if value != 0:
                cnv_call_lookup = cna_lookup_dic[str(value)]
                row_dict = {
                    'SAMPLE_ID': column,
                    'VARIANT_CATEGORY': 'CNV',
                    'CNV_CALL': cnv_call_lookup,
                    'TRUE_HUGO_SYMBOL': row['Hugo_Symbol']
                }
                new_row_dict: dict = {col: row_dict.get(col, '') for col in output_df.columns}
                new_row_df = pd.DataFrame(new_row_dict, index=[0])
                output_df = pd.concat([output_df, new_row_df], ignore_index=True)
    return output_df


def add_maf(df, args, filters: Filter, annotatedmaf: bool):
    # Original script skips the first line after the header, so reading the file begins on like 3 instead of line 2
    maf_df: pd.DataFrame = pd.read_csv(args.maf_file, delimiter="\t", skiprows=[1])
    # SAMPLE_ID
    maf_df['SAMPLE_ID'] = maf_df['Tumor_Sample_Barcode'].apply(process_sample_id)
    # TRUE_TRANSCRIPT_EXON
    maf_df['TRUE_TRANSCRIPT_EXON'] = maf_df['Exon_Number'].fillna('').apply(lambda value: value.split('/')[0])
    # ALLELE_FRACTION
    maf_df['ALLELE_FRACTION'] = maf_df.apply(lambda row: (
        calculate_allele_fraction(int(row['t_alt_count']), int(row['t_depth']))
    ), axis=1)
    # ONCOGENICITY
    maf_df['Tumor_Sample_UUID'] = maf_df['Tumor_Sample_UUID'].fillna('')
    # Create output DataFrame with required columns
    # if annotatedmaf == False then we read the oncoKB annotations from the oncoKB file
    # if annotatedmaf == True then we read the oncoKB annotations from the MAF file 
    # from the columns with the header "ONCOGENIC" and "MUTATION_EFFECT"
    if annotatedmaf == False:
        output_df: pd.DataFrame = pd.DataFrame({
            'SAMPLE_ID': maf_df['SAMPLE_ID'],
            'TRUE_HUGO_SYMBOL': maf_df['Hugo_Symbol'],
            'TRUE_PROTEIN_CHANGE': maf_df['HGVSp_Short'],
            'TRUE_VARIANT_CLASSIFICATION': maf_df['Variant_Classification'],
            'VARIANT_CATEGORY': 'MUTATION',
            'CNV_CALL': '',
            'WILDTYPE': 'false',
            'CHROMOSOME': maf_df['Chromosome'],
            'POSITION': maf_df['Start_Position'],
            'TRUE_CDNA_CHANGE': '',
            'REFERENCE_ALLELE': maf_df['Reference_Allele'],
            'TRUE_TRANSCRIPT_EXON': maf_df['TRUE_TRANSCRIPT_EXON'],
            'CANONICAL_STRAND': maf_df['Strand'],
            'ALLELE_FRACTION': maf_df['ALLELE_FRACTION'],
            'ONCOGENICITY': '',
            'MUTATION_EFFECT': '',
            'LEFT_PARTNER_GENE': '',
            'RIGHT_PARTNER_GENE': ''
        })
    else:
        output_df: pd.DataFrame = pd.DataFrame({
            'SAMPLE_ID': maf_df['SAMPLE_ID'],
            'TRUE_HUGO_SYMBOL': maf_df['Hugo_Symbol'],
            'TRUE_PROTEIN_CHANGE': maf_df['HGVSp_Short'],
            'TRUE_VARIANT_CLASSIFICATION': maf_df['Variant_Classification'],
            'VARIANT_CATEGORY': 'MUTATION',
            'CNV_CALL': '',
            'WILDTYPE': 'false',
            'CHROMOSOME': maf_df['Chromosome'],
            'POSITION': maf_df['Start_Position'],
            'TRUE_CDNA_CHANGE': '',
            'REFERENCE_ALLELE': maf_df['Reference_Allele'],
            'TRUE_TRANSCRIPT_EXON': maf_df['TRUE_TRANSCRIPT_EXON'],
            'CANONICAL_STRAND': maf_df['Strand'],
            'ALLELE_FRACTION': maf_df['ALLELE_FRACTION'],
            'ONCOGENICITY':  maf_df['ONCOGENIC'].fillna("Unknown"),
            'MUTATION_EFFECT': maf_df['MUTATION_EFFECT'].fillna("Unknown"),
            'LEFT_PARTNER_GENE': '',
            'RIGHT_PARTNER_GENE': ''
        })

    # Filter out all rows in this output df where the variant classification is in this list of blacklisted values
    output_df = output_df[~output_df['TRUE_VARIANT_CLASSIFICATION'].isin(filters.maf.Variant_Classification)]
    return output_df


def add_data_sv(df: pandas.DataFrame, args: ArgsType):
    """
    Adds SV data to the output dataframe
    :param df: Dataframe to add rows to
    :param args: Args object from script input
    :return: Dataframe with SV data added
    """
    sv_df: pandas.DataFrame = pandas.read_csv(args.data_sv, delimiter="\t")
    # Loop through sv_df and add the left and right partner genes to the output df as new rows
    for index, row in sv_df.iterrows():
        row_dict = {
            'SAMPLE_ID': row['Sample_Id'],
            'LEFT_PARTNER_GENE': row['Site1_Hugo_Symbol'],
            'RIGHT_PARTNER_GENE': row['Site2_Hugo_Symbol'],
            'VARIANT_CATEGORY': 'SV'
        }
        # Sometimes the Site2_Hugo_Symbol will be empty. At that time, the same gene is fused with itself.
        # The field Event_Info will show the same gene twice. This is for verification purposes.
        # check if row_dict['RIGHT_PARTNER_GENE'] is nan
        if row_dict['RIGHT_PARTNER_GENE'] != row_dict['RIGHT_PARTNER_GENE']:
            # Event info follows the pattern "LEFT_PARTNER_GENE-LEFT_PARTNER_GENE fusion",
            # so check that it starts with the same gene
            expected_event_info = f"{row_dict['LEFT_PARTNER_GENE']}-{row_dict['LEFT_PARTNER_GENE']}"
            if row['Event_Info'].startswith(expected_event_info):
                row_dict['RIGHT_PARTNER_GENE'] = row_dict['LEFT_PARTNER_GENE']
        new_row_dict: dict = {col: row_dict.get(col, '') for col in df.columns}
        new_row_df = pandas.DataFrame(new_row_dict, index=[0])
        df = pandas.concat([df, new_row_df], ignore_index=True)
    return df

def add_ms_status(df: pandas.DataFrame, args: ArgsType):
    """
    Adds MSI status data to the output dataframe
    :param df: Dataframe to add rows to
    :param args: Args object from script input
    :return: Dataframe with MSI status data added
    """
    # Read the data_clinical_samples file using pandas, extract the sample ID and MS status columns, then add them as new rows in df. Ignore any row with NA in  MS_STATUS column
    msi_df: pandas.DataFrame = pandas.read_csv(args.data_clinical_samples, delimiter="\t", skiprows=4)
    filtered_msi_df = msi_df.dropna(subset=['MSI_STABILITY'])
    new_rows = filtered_msi_df[['SAMPLE_ID', 'MSI_STABILITY']].rename(columns={'MSI_STABILITY': 'MS_STATUS'})
    df_updated = pd.concat([df, new_rows], ignore_index=True)

    return df_updated

def prepare_genomic_data(args: ArgsType, config: Config) -> None:
    output_df = pd.DataFrame(columns=[
        'SAMPLE_ID',
        'TRUE_HUGO_SYMBOL',
        'TRUE_PROTEIN_CHANGE',
        'TRUE_VARIANT_CLASSIFICATION',
        'VARIANT_CATEGORY',
        'CNV_CALL',
        'WILDTYPE',
        'CHROMOSOME',
        'POSITION',
        'TRUE_CDNA_CHANGE',
        'REFERENCE_ALLELE',
        'TRUE_TRANSCRIPT_EXON',
        'CANONICAL_STRAND',
        'ALLELE_FRACTION',
        'ONCOGENICITY',
        'MUTATION_EFFECT',
        'LEFT_PARTNER_GENE',
        'RIGHT_PARTNER_GENE'
    ])
    annotatedmaf : bool = False

    if hasattr(args, 'annotatedmaf') and args.annotatedmaf:
        annotatedmaf = True
        print("annotatedmaf is true")
    
    if hasattr(args, 'maf_file') and args.maf_file and len(args.maf_file) > 0:
        output_df = add_maf(output_df, args, config.filters, annotatedmaf)

    #if annotatedmaf == False, then only use the oncoKB annotations from the oncoKB file
    if annotatedmaf == False:
        if hasattr(args, 'variants') and args.variants and len(args.variants) > 0:
            output_df = add_oncogenicity(output_df, args)

    if hasattr(args, 'fusion_file') and args.fusion_file and len(args.fusion_file) > 0:
        output_df = add_fusion_array(output_df, args)

    if hasattr(args, 'cna_file') and args.cna_file and len(args.cna_file) > 0:
        output_df = add_cna(args, output_df)

    if hasattr(args, 'data_sv') and args.data_sv and len(args.data_sv) > 0:
        output_df = add_data_sv(output_df, args)

    output_df = add_ms_status(output_df, args)

    output_df.to_csv(args.output_file, index=False, lineterminator='\n')
    logging.info(f'Genomic file generated to {args.output_file}')
    print(f'Genomic file generated to {args.output_file}')


def add_columns_to_maf(maf_df):
    # SAMPLE_ID
    maf_df['SAMPLE_ID'] = maf_df['Tumor_Sample_Barcode'].apply(process_sample_id)
    # TRUE_TRANSCRIPT_EXON
    maf_df['TRUE_TRANSCRIPT_EXON'] = maf_df['Exon_Number'].fillna('').apply(lambda value: value.split('/')[0])
    # ALLELE_FRACTION
    maf_df['ALLELE_FRACTION'] = maf_df.apply(lambda row: (
        calculate_allele_fraction(int(row['t_alt_count']), int(row['t_depth']))
    ), axis=1)
    # ONCOGENICITY
    maf_df['Tumor_Sample_UUID'] = maf_df['Tumor_Sample_UUID'].fillna('')

def main():
    args = get_options()
    init_logger(args.debug)
    if args.debug:
        logging.debug(f"Args: {args}")
    config = open_config(args.config_file)
    prepare_genomic_data(args, config)


if __name__ == "__main__":
    main()
