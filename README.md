# Installation

Python 3.8+ is recommended for running this script. The required Python packages can be installed with:

```bash
pip install -r requirements.txt
```

# Clinical Data Script

This script is designed to merge and reformat clinical sample and patient data from files for further use in trial matching. It handles tasks such as reading data from files, processing data, and outputting results in a new CSV file.

## Usage
The script is used from the command-line and requires three arguments: the paths to the clinical sample file, the clinical patient file, and the output file. An optional argument can be used to enable debug mode.

Here's a basic usage example:

```sh
python prepare_clinical_data.py --sample-file path/to/sample_file --patient-file path/to/patient_file --output path/to/output_file
```

### Command-Line Arguments

The following command-line arguments are available:

* `-s`, `--sample-file`: The path to the clinical sample file (e.g., `data_clinical_samples.txt`).
* `-p`, `--patient-file`: The path to the clinical patient file (e.g., `data_clinical_patients.txt`).
* `-o`, `--output`: The path to the output clinical file for trial matching (e.g., `clinical.csv`).
* `-d`, `--debug`: (Optional) Enable debug mode; the program will print to stdout.
* `-st`, `--study-file`: Contains a cancer_study_identifier line. Example: cancer_study_identifier: BRCA_pps.
* `-lt`, `--logto`: (Optional) The file path to log to. The file will be created if it does not exist.

## Output
The script generates an output CSV file containing merged and reformatted data. The output file includes the following columns:

- 'SAMPLE_ID'
- 'ORD_PHYSICIAN_NAME'
- 'ORD_PHYSICIAN_EMAIL'
- 'ONCOTREE_PRIMARY_DIAGNOSIS_NAME'
- 'CANCER_TYPE'
- 'REPORT_DATE'
- 'BIRTH_DATE'
- 'AGE'
- 'GENDER'
- 'ETHNICITY'
- 'VITAL_STATUS'
- 'ER_STATUS'
- 'PR_STATUS'
- 'HER2_STATUS'
- 'CENTRE'
- 'PATIENT_ID'
- 'STUDY_ID'

If the debug mode is enabled (`-d` or `--debug` flag), the script will also print debug messages to the standard output.

# Genomic Data Preparation Script

This script is designed to prepare genomic data for further analysis. The script takes in four types of files: VEP annotated Mutation Annotation Format (MAF) file, Discrete Copy Number data from GISTIC2, OncoKB all annotated variants, and Fusion structural variant file. It processes these files, filters data according to provided configuration, adds calculated information and generates a consolidated csv file.

## Running the Script

You can run the script from the command line with the following format:

```bash
python prepare_genomic_data.py -m <maf_file> -c <cna_file> -v <variants_file> -o <output_file> -f <fusion_file> -cf <config_file> -sv <data_sv_file> -dcs <data_clinical_samples_file> [-d]
```

The arguments represent:

* `-m, --maf-file`: A VEP annotated MAF file, e.g. `data_mutations_extended.txt`
* `-c, --cna-file`: A discrete copy number data from GISTIC2, e.g. `data_CNA.txt`
* `-v, --variants`: An OncoKB all annotated variants file, e.g. `allAnnotatedVariants.txt`
* `-o, --output-file`: The output genomic data file for trial match, e.g. `genomic.csv`
* `-f, --fusion-file`: A fusion structural variant file, e.g. `data_fusions.txt`
* `-d, --debug`: (Optional) Run in debug mode to print to stdout
* `-cf, --config-file`: Config file that holds settings for filters
* `-sv, --data_sv`: e.g data_sv.txt.
* `-dcs, --data-clinical-samples`: e.g data_clinical_samples.txt.


## Configuration

The configuration file (`config.json`) is used to set filters for data processing. The example structure of the configuration file is as follows:

```json
{
  "filters": {
    "maf": {
      "Variant_Classification": ["Frame_Shift_Del", "Frame_Shift_Ins", "Splice_Site", "Translation_Start_Site"]
    }
  }
}
```

## Log

The script logs its process into a `log.txt` file. If debug mode is activated, logs will also be printed to stdout.
