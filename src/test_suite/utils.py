import datetime
import os

import pandas as pd
from pandas import DataFrame


def compare_birth_dates(expected: str, test: str) -> bool:
    """
    Compare two birth dates and return True if they are the same year and month or within one day of each other.
    :param expected: The expected birth date in the format 'YYYY-MM-DD'.
    :param test: The test birth date in the format 'YYYY-MM-DD'.
    :return: True if the birth dates are the same year and month or within one day of each other, False otherwise.
    """

    # Convert the dates to datetime.date objects
    expected_date = datetime.datetime.strptime(expected, '%Y-%m-%d').date()
    testing_date = datetime.datetime.strptime(test, '%Y-%m-%d').date()

    # Calculate the difference between the two dates
    delta = abs(expected_date - testing_date)

    # Check if the year and month are the same or if the difference is less than or equal to one day
    day_month_same = expected_date.year == testing_date.year and expected_date.month == testing_date.month
    within_one_day = delta <= datetime.timedelta(days=1)

    # Compare the year and month of the two dates and return the result
    if day_month_same or within_one_day:
        return True
    return False


def assert_df_equals(expected_df: DataFrame, testing_df: DataFrame):
    """
    Asserts that two pandas dataframes are equal.

    Args:
        expected_df: A pandas dataframe representing the expected data.
        testing_df: A pandas dataframe representing the actual data.

    Raises:
        AssertionError: If the two dataframes are not equal.

    Returns:
        None
    """

    for expected_chunk, testing_chunk in zip(expected_df, testing_df):
        expected_cols = expected_chunk.columns.tolist()
        # Loop through each row synchronously
        for index, expected_row in expected_chunk.iterrows():
            testing_row = testing_chunk.loc[index]
            for col in expected_cols:
                expected_val = expected_row[col]
                testing_val = testing_row[col]

                # First check if both values are nan, as nan values cannot be used in equality check
                if pd.isnull(expected_val) and pd.isnull(testing_val):
                    continue

                try:
                    assert expected_val == testing_val, f"Col: {col}, Row: {index}, Expected: {expected_val}, Value: {testing_val}"
                except AssertionError as e:
                    raise AssertionError(e)


def fp_does_not_exist(fp):
    return not os.path.isfile(fp)


def create_empty_file(file_key: str):
    """
    Creates an empty file based on the key inputted.
    The key is from the script input section of the test_config.json file
    :param file_key: String
    :return: File path of the newly created file
    """

    file_name, line = '', ''

    # Each if simply sets the output file path and the header line to write to the file
    if file_key == "maf_fp":
        file_name = "../../input/data_mutations_extended.txt"
        line = "Hugo_Symbol	Entrez_Gene_Id	Center	NCBI_Build	Chromosome	Start_Position	End_Position	Strand	Variant_Classification	Variant_Type	Reference_Allele	Tumor_Seq_Allele1	Tumor_Seq_Allele2	dbSNP_RS	dbSNP_Val_Status	Tumor_Sample_Barcode	Matched_Norm_Sample_Barcode	Match_Norm_Seq_Allele1	Match_Norm_Seq_Allele2	Tumor_Validation_Allele1	Tumor_Validation_Allele2	Match_Norm_Validation_Allele1	Match_Norm_Validation_Allele2	Verification_Status	Validation_Status	Mutation_Status	Sequencing_Phase	Sequence_Source	Validation_Method	Score	BAM_File	Sequencer	Tumor_Sample_UUID	Matched_Norm_Sample_UUID	HGVSp_Short	Transcript_ID	Exon_Number	t_depth	t_ref_count	t_alt_count	tumor_vaf	n_depth	n_ref_count	n_alt_count	normal_vaf	Allele	cDNA_position	CDS_position	Protein_position	Amino_acids	Codons	HGNC_ID	BIOTYPE	CCDS	ENSP	SWISSPROT	SIFT	PolyPhen	EXON	AF	AFR_AF	AMR_AF	ASN_AF	EAS_AF	EUR_AF	SAS_AF	AA_AF	EA_AF	CLIN_SIG	IMPACT	ExAC_AF	ExAC_AF_AFR	ExAC_AF_AMR	ExAC_AF_EAS	ExAC_AF_FIN	ExAC_AF_NFE	ExAC_AF_OTH	ExAC_AF_SAS	FILTER	flanking_bps	variant_id	ExAC_AF_Adj	ExAC_AC_AN_Adj	ExAC_AC_AN	ExAC_AC_AN_AFR	ExAC_AC_AN_AMR	ExAC_AC_AN_EAS	ExAC_AC_AN_FIN	ExAC_AC_AN_NFE	ExAC_AC_AN_OTH	ExAC_AC_AN_SAS	ExAC_FILTER	gnomAD_AF	gnomAD_AFR_AF	gnomAD_AMR_AF	gnomAD_ASJ_AF	gnomAD_EAS_AF	gnomAD_FIN_AF	gnomAD_NFE_AF	gnomAD_OTH_AF	gnomAD_SAS_AF	OCT_Freq	LEVEL_1	LEVEL_3A	LEVEL_3B	LEVEL_4	LEVEL_R1"
    elif file_key == "cna_fp":
        file_name = "../../input/data_CNA.txt"
        line = "Hugo_Symbol	OCT-06-0002-OncoMine	OCT-06-0014-OncoMine	OCT-06-0018-OncoMine	OCT-06-0039-OncoMine	OCT-06-0041-OncoMine	OCT-06-0044-OncoMine	OCT-06-0049-OncoMine	OCT-06-0052-OncoMine	OCT-06-0054-OncoMine	OCT-06-0061-OncoMine	OCT-06-0057-OncoMine	OCT-06-0070-OncoMine	OCT-06-0076-OncoMine	OCT-06-0077-OncoMine	OCT-06-0082-OncoMine	OCT-06-0083-OncoMine	OCT-06-0086-OncoMine	OCT-06-0090-OncoMine	OCT-06-0091-OncoMine	OCT-06-0095-OncoMine	OCT-06-0096-OncoMine	OCT-06-0097-OncoMine	OCT-06-0100-OncoMine	OCT-06-0104-OncoMine	OCT-06-0105-OncoMine	OCT-06-0107-OncoMine	OCT-06-0109-OncoMine	OCT-06-0112-OncoMine	OCT-06-0123-OncoMine	OCT-06-0125-OncoMine	OCT-06-0126-OncoMine	OCT-06-0128-OncoMine	OCT-06-0132-OncoMine	OCT-06-0136-OncoMine	OCT-06-0137-OncoMine	OCT-06-0143-OncoMine	OCT-06-0144-OncoMine	OCT-06-0150-OncoMine	OCT-05-0445_Tumour	OCT-05-0448_Tumour	OCT-05-0449_Tumour	OCT-05-0452_Tumour	OCT-05-0456_Tumour	OCT-05-0459_Tumour	OCT-05-0460_Tumour	OCT-05-0462_Tumour	OCT-05-0465_Tumour	OCT-05-0466_Tumour	OCT-05-0467_Tumour	OCT-05-0468_Tumour	OCT-05-0469_Tumour	OCT-05-0471_Tumour	OCT-05-0472_Tumour	OCT-05-0457_Tumour	OCT-05-0478_Tumour	OCT-05-0481_Tumour	OCT-05-0483_Tumour	OCT-05-0485_Tumour	OCT-05-0504_Tumour"
    elif file_key == "fusion_fp":
        file_name = "../../input/data_fusions.txt"
        line = "Hugo_Symbol	Entrez_Gene_Id	Center	Tumor_Sample_Barcode	Fusion	DNA_support	RNA_support	Method	Frame	Annotation"
    elif file_key == "variants_fp":
        file_name = "../../input/allAnnotatedVariants.txt"
        line = '"Isoform	RefSeq	Entrez Gene ID	Hugo Symbol	Alteration	Protein Change	Oncogenicity	Mutation Effect	PMIDs for Mutation Effect	Abstracts for Mutation Effect"'

    with open(file_name, 'w') as f:
        f.write(line)
    return file_name

