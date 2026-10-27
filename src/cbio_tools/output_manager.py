import csv
import json

from pymongo import MongoClient

import cbio_logger
import matchminer_load

logger = cbio_logger.initialize_logging(__name__)


def export_to_file(file_name: str, output_data: list[dict]):
    """
    Export the processed sample data to a CSV file.

    Args:
        file_name (str): The name of the file to output.
        output_data (list[dict]): The list of processed data.
    """
    
    logger.info(f"Exporting { len(output_data) } rows of data to { file_name }...")
    with open(file_name, "w") as file:
        csv_file = csv.writer(file)
        csv_file.writerow(output_data[0].keys()) 
        for row in output_data:
            csv_file.writerow(row.values())


def export_to_mongodb(db_ip: str, collection_name: str, output_data: list[dict], indexes: list[tuple]):
    """
    Export the processed sample data to a MongoDB database.

    Args:
        db_ip (str): The IP address of the MongoDB database.
        collection_name (str): The name of the collection to output to.
        output_data (list[dict]): The list of processed data.
    """

    logger.info(f"Exporting { len(output_data) } rows of data to MongoDB database at { db_ip }...")
    client = MongoClient(db_ip)
    db = client.matchminer
    collection = db[collection_name]


    if collection_name == "clinical":
        normalized_data = matchminer_load.pre_process_clinical_data(output_data)
    else:
        normalized_data = matchminer_load.pre_process_other_data(db, output_data)
    
    # If there is no data to export, skip the insert_many
    if (len(normalized_data) == 0):
        logger.warning("There is no normalized_data to export. Skipping insert_many.")
    else:
        batch_insert(collection, normalized_data)

    for field, direction in indexes:
        # for some reason first_last index is custom name and doesn't use sort order in the name
        if field == 'FIRST_LAST':
            collection.create_index([(field, direction)], name=f"{field}")
        else:
            collection.create_index([(field, direction)], name=f"{field}_1")

    client.close()
    logger.info("Export complete.")


def batch_insert(collection, data, batch_size=1000):
    """
    Insert data into MongoDB in batches to avoid timing out

    Args:
        collection (pymongo.collection.Collection): The MongoDB collection to insert data into.
        data (list[dict]): The list of data to insert.
        batch_size (int): The number of documents to insert in each batch.
    """
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        collection.insert_many(batch)
