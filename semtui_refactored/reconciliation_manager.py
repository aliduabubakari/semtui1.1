import requests
import json
import pandas as pd
from .token_manager import TokenManager
from urllib.parse import urljoin
import logging

# Configure logging
#ogging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__)

class ReconciliationManager:
    def __init__(self, base_url, token):
        self.base_url = base_url.rstrip('/') + '/'
        self.api_url = urljoin(self.base_url, 'api/')
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def get_reconciliator_data(self):
        """
        Retrieves reconciliator data from the backend.
        :return: data of reconciliator services in JSON format
        """
        try:
            response = requests.get(f"{self.api_url}reconciliators/list", headers=self.headers)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while retrieving reconciliator data: {e}")
            return None

    def clean_service_list(self, service_list):
        """
        Cleans and formats the service list.
        :param service_list: data regarding available services
        :return: DataFrame containing reconciliators information
        """
        reconciliators = pd.DataFrame(columns=["id", "relativeUrl", "name"])
        for reconciliator in service_list:
            reconciliators.loc[len(reconciliators)] = [
            reconciliator["id"], reconciliator["relativeUrl"], reconciliator["name"]]
        return reconciliators

    def get_reconciliators_list(self):
        """
        Provides a list of available reconciliators with their main information.
        :return: DataFrame containing reconciliators and their information
        """
        response = self.get_reconciliator_data()
        if response:
            return self.clean_service_list(response)
        return None

    def get_extender_data(self):
        """
        Retrieves extender data from the backend

        :return: data of extension services in JSON format
        """
        try:
            response = requests.get(f"{self.api_url}extenders/list", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while retrieving extender data: {e}")
            return None

    def get_extenders_list(self):
        """
        Provides a list of available extenders with their main information

        :return: a dataframe containing extenders and their information
        """
        response = self.get_extender_data()
        if response:
            return self.clean_service_list(response)
        return None

    def get_reconciliator(self, id_reconciliator, response):
        """
        Function that, given the reconciliator's ID, returns a dictionary 
        with all the service information

        :id_reconciliator: the ID of the reconciliator in question
        :return: a dictionary with the reconciliator's information
        """
        for reconciliator in response:
            if reconciliator['id'] == id_reconciliator:
                return {
                    'uri': reconciliator['uri'],
                    'prefix': reconciliator['prefix'],
                    'name': reconciliator['name'],
                    'relativeUrl': reconciliator['relativeUrl']
                }
        return None

    def create_reconciliation_payload(self, table, column_name, id_reconciliator):
        """
        Creates the payload for the reconciliation request

        :table: table in raw format
        :columnName: the name of the column to reconcile
        :idReconciliator: the id of the reconciliation service to use
        :return: the request payload
        """
        rows = []
        rows.append({"id": 'column$index', "label": column_name})
        for row in table['rows'].keys():
            rows.append({"id": row+"$"+column_name,
                        "label": table['rows'][row]['cells'][column_name]['label']})
        return {"serviceId": id_reconciliator, "items": rows}

    def parse_name_field(self, name, uri_reconciliator, id_entity):
        """
        The actual function that changes the name format to the one required for visualization

        :name: entity name
        :uri_reconciliator: the URI of the affiliated knowledge graph
        :id_entity: entity ID
        :return: the name in the correct format
        """
        return {
            'value': name,
            'uri': f"{uri_reconciliator}{id_entity}"
        }

    def create_cell_metadata_name_field(self, metadata, id_reconciliator, reconciliator_response):
        """
        Refactor of the name field within cell-level metadata
        necessary for visualization within SEMTUI

        :metadata: column-level metadata
        :id_reconciliator: ID of the reconciliator performed in the operation
        :reconciliator_response: response containing reconciliator information
        :return: metadata containing the name field in the new format
        """
        for row in range(len(metadata)):
            try:
                for item in range(len(metadata[row]["metadata"])):
                    value = metadata[row]["metadata"][item]['name']
                    uri = metadata[row]["metadata"][item]['id']
                    metadata[row]["metadata"][item]['name'] = self.parse_name_field(
                        value, self.get_reconciliator(id_reconciliator, reconciliator_response)['uri'], uri.split(':')[1])
            except:
                return []
        return metadata

    def calculate_score_bound_cell(self, metadata):
        """
        Calculates the min and max value of the score of the results obtained for
        a single cell

        :metadata: metadata of a single cell
        :return: a dictionary containing the two values
        """
        try:
            score_list = [item['score'] for item in metadata]
            return {'lowestScore': min(score_list), 'highestScore': max(score_list)}
        except:
            return {'lowestScore': 0, 'highestScore': 0}
    
    def value_match_cell(self, metadata):
        """
        Returns whether a cell has obtained a match or not

        :metadata: cell-level metadata
        :return: True or False based on the match occurrence
        """
        for item in metadata:
            if item['match'] == True:
                return True
        return False

    def create_annotation_meta_cell(self, metadata):
        """
        Creates the annotationMeta field at the cell level, 
        which will then be inserted into the table

        :metadata: cell-level metadata
        :return: the dictionary with data regarding annotationMeta
        """
        score_bound = self.calculate_score_bound_cell(metadata)
        return {'annotated': True,
                'match': {'value': self.value_match_cell(metadata)},
                'lowestScore': score_bound['lowestScore'],
                'highestScore': score_bound['highestScore']}

    def update_metadata_cells(self, table, metadata):
        """
        Allows inserting new cell-level metadata

        :table: table in raw format
        :metadata: cell-level metadata
        :return: the table in raw format with metadata
        """
        for item in metadata:
            item["id"] = item["id"].split("$")
            try:
                table["rows"][item["id"][0]]["cells"][item["id"]
                                                    [1]]["metadata"] = item["metadata"]
                table["rows"][item["id"][0]]["cells"][item["id"][1]
                                                    ]["annotationMeta"] = self.create_annotation_meta_cell(item["metadata"])
            except:
                print("")
        return table

    def calculate_n_cells_reconciliated_column(self, table, column_name):
        """
        Calculates the number of reconciled cells within 
        a column

        :table: table in raw format
        :column_name: name of the column in question
        :return: the number of reconciled cells
        """
        cells_reconciliated = 0
        rows_index = table["rows"].keys()
        for row in rows_index:
            try:
                if table['rows'][row]['cells'][column_name]['annotationMeta']["annotated"] == True:
                    cells_reconciliated += 1
            except:
                cells_reconciliated = cells_reconciliated
        return cells_reconciliated

    def create_context_column(self, table, column_name, id_reconciliator, reconciliator_response):
        """
        Creates the context field at the column level by retrieving the necessary data

        :table: table in raw format
        :column_name: the name of the column for which the context is being created
        :id_reconciliator: the ID of the reconciliator used for the column
        :reconciliator_response: response containing reconciliator information
        :return: the context field of the column
        """
        n_cells = len(table["rows"].keys())
        reconciliator = self.get_reconciliator(id_reconciliator, reconciliator_response)
        return {reconciliator['prefix']: {
                'uri': reconciliator['uri'],
                'total': n_cells,
                'reconciliated': self.calculate_n_cells_reconciliated_column(table, column_name)
                }}

    def get_column_metadata(self, metadata):
        """
        Allows retrieving column-level data, particularly
        the entity corresponding to the column, the column types,
        and the match value of the entities in the column

        :metadata: column metadata obtained from the reconciliator
        :return: dictionary containing the different data
        """
        entity = []
        types = []
        for i in range(len(metadata)):
            try:
                if metadata[i]['id'] == ['column', 'index']:
                    entity = metadata[i]['metadata']
            except:
                print("No column entity is provided")
            try:
                if metadata[i]['id'] != ['column', 'index']:
                    for j in range(len(metadata[i]['metadata'])):
                        if metadata[i]['metadata'][j]['match'] == True:
                            types.append(metadata[i]['metadata'][j]['type'][0])
            except:
                print("No column type is provided")
        match_metadata_value = True
        for item in entity:
            if item['match'] == False:
                match_metadata_value = False
        return {'entity': entity, 'type': types, 'matchMetadataValue': match_metadata_value}

    def create_metadata_field_column(self, metadata):
        """
        Allows creating the metadata field for a column, which will
        then be inserted into the general column-level metadata

        :metadata: column-level metadata
        :return: the metadata field at the column level
        """
        return [
            {'id': '',
            'match': self.get_column_metadata(metadata)['matchMetadataValue'],
            'score': 0,
            'name':{'value': '', 'uri': ''},
            'entity': self.get_column_metadata(metadata)['entity'],
            'property':[],
            'type': self.get_column_metadata(metadata)['type']}
        ]

    def calculate_score_bound_column(self, table, column_name, reconciliator_response):
        all_scores = []
        match_value = True
        rows = table["rows"].keys()
        for row in rows:
            try:
                annotation_meta = table["rows"][row]['cells'][column_name]['annotationMeta']
                if annotation_meta['annotated'] == True:
                    all_scores.append(annotation_meta['lowestScore'])
                    all_scores.append(annotation_meta['highestScore'])
                if annotation_meta['match']['value'] == False:
                    match_value = False
            except KeyError:
                print(f"Missing key in cell annotation metadata: 'annotationMeta'")
                print(f"Row: {row}, Column: {column_name}")
                print(f"Cell data: {table['rows'][row]['cells'][column_name]}")
        
        if all_scores:
            return {'lowestScore': min(all_scores), 'highestScore': max(all_scores), 'matchValue': match_value}
        else:
            print("No valid annotation metadata found for the column.")
            return {'lowestScore': None, 'highestScore': None, 'matchValue': None}

    def create_annotation_meta_column(self, annotated, table, column_name, reconciliator_response):
        score_bound = self.calculate_score_bound_column(
            table, column_name, reconciliator_response)
        return {'annotated': annotated,
                'match': {'value': score_bound['matchValue']},
                'lowestScore': score_bound['lowestScore'],
                'highestScore': score_bound['highestScore']
                }

    def update_metadata_column(self, table, column_name, id_reconciliator, metadata, reconciliator_response):
        """
        Allows inserting column-level metadata

        :table: table in raw format
        :column_name: name of the column to operate on
        :id_reconciliator: ID of the reconciliator used
        :metadata: column-level metadata
        :reconciliator_response: response containing reconciliator information
        :return: the table with the new metadata inserted
        """
        # inquire about the different states
        table['columns'][column_name]['status'] = 'pending'
        table['columns'][column_name]['kind'] = "entity"
        table['columns'][column_name]['context'] = self.create_context_column(
            table, column_name, id_reconciliator, reconciliator_response)
        table['columns'][column_name]['metadata'] = self.create_metadata_field_column(
            metadata)
        table['columns'][column_name]['annotationMeta'] = self.create_annotation_meta_column(
            True, table, column_name, reconciliator_response)
        return table

    def update_metadata_table(self, table):
        """
        Updates the table-level metadata.

        :param table: table in raw format
        :return: updated table
        """
        # Placeholder implementation
        return table

    def reconcile(self, table, column_name, id_reconciliator, optional_columns=None):
        """
        Reconciles a column with the chosen reconciliator and creates a payload for backend update
        :param table: the table with the column to reconcile
        :param column_name: the name of the column to reconcile
        :param id_reconciliator: ID of the reconciliator to use
        :param optional_columns: optional list of additional column names
        :return: tuple (reconciled table, payload for backend update)
        """
        # Reconciliation process
        reconciliator_response = self.get_reconciliator_data()
        if reconciliator_response is None:
            print("Failed to retrieve reconciliator data.")
            return None, None
        reconciliator = self.get_reconciliator(id_reconciliator, reconciliator_response)
        if reconciliator is None:
            print(f"Reconciliator with ID {id_reconciliator} not found.")
            return None, None

        url = f"{self.api_url}reconciliators{reconciliator['relativeUrl']}"
        payload = self.create_reconciliation_payload(table, column_name, id_reconciliator)
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error occurred while sending reconciliation request: {e}")
            return None, None

        # Updating the table with reconciliation data
        metadata = self.create_cell_metadata_name_field(response_data, id_reconciliator, reconciliator_response)
        table = self.update_metadata_cells(table, metadata)
        table = self.update_metadata_column(table, column_name, id_reconciliator, metadata, reconciliator_response)
        table = self.update_metadata_table(table)

        # Creating payload for backend update
        table_data = table.get("table", {})

        nCellsReconciliated = 0
        if column_name in table.get("columns", {}):
            column = table["columns"][column_name]
            if "context" in column and "georss" in column["context"]:
                nCellsReconciliated = column["context"]["georss"].get("reconciliated", 0)

        backend_payload = {
            "tableInstance": {
                "id": table_data.get("id"),
                "idDataset": table_data.get("idDataset"),
                "name": table_data.get("name"),
                "nCols": table_data.get("nCols", 0),
                "nRows": table_data.get("nRows", 0),
                "nCells": table_data.get("nCells", 0),
                "nCellsReconciliated": nCellsReconciliated,
                "lastModifiedDate": table_data.get("lastModifiedDate", ""),
                "minMetaScore": table_data.get("minMetaScore", 0),
                "maxMetaScore": table_data.get("maxMetaScore", 1)
            },
            "columns": {
                "byId": table.get("columns", {}),
                "allIds": list(table.get("columns", {}).keys())
            },
            "rows": {
                "byId": table.get("rows", {}),
                "allIds": list(table.get("rows", {}).keys())
            }
        }

        return table, backend_payload

    def create_reconciliation_payload_for_backend(self, table_json, reconciliated_column_name, table_id, dataset_id, table_name):
        """
        Creates the payload required to perform the table update operation.

        :param table_json: JSON representation of the table
        :param reconciliated_column_name: The name of the column that contains the reconciliated information
        :param table_id: ID of the table
        :param dataset_id: ID of the dataset
        :param table_name: Name of the table
        :return: request payload
        """
        # Default values for missing fields
        default_table_fields = {
            "minMetaScore": 0,
            "maxMetaScore": 1,
            "nCols": 0,
            "nRows": 0,
            "nCells": 0,
            "lastModifiedDate": ""
        }

        # Ensure all required fields are present in the table section
        table_data = {**default_table_fields, **table_json.get("table", {})}

        # Recalculate nCellsReconciliated
        nCellsReconciliated = 0

        # Check the specified reconciliated column for reconciliated count
        if reconciliated_column_name in table_json.get("columns", {}):
            column = table_json["columns"][reconciliated_column_name]
            if "context" in column and "georss" in column["context"]:
                nCellsReconciliated = column["context"]["georss"].get("reconciliated", 0)

        # Override id and idDataset with provided values
        table_data["id"] = table_id
        table_data["idDataset"] = dataset_id
        table_data["name"] = table_name

        # Construct the payload
        payload = {
            "tableInstance": {
                "id": table_data["id"],
                "idDataset": table_data["idDataset"],
                "name": table_data["name"],
                "nCols": table_data["nCols"],
                "nRows": table_data["nRows"],
                "nCells": table_data["nCells"],
                "nCellsReconciliated": nCellsReconciliated,
                "lastModifiedDate": table_data["lastModifiedDate"],
                "minMetaScore": table_data["minMetaScore"],
                "maxMetaScore": table_data["maxMetaScore"]
            },
            "columns": {
                "byId": table_json.get("columns", {}),
                "allIds": list(table_json.get("columns", {}).keys())
            },
            "rows": {
                "byId": table_json.get("rows", {}),
                "allIds": list(table_json.get("rows", {}).keys())
            }
        }
        return payload
    
    def get_reconciliator_parameters(self, id_reconciliator, print_params=False):
        """
        Retrieves the parameters needed for a specific reconciliator service.

        :param id_reconciliator: the ID of the reconciliator service
        :param print_params: (optional) whether to print the retrieved parameters or not
        :return: a dictionary containing the parameter details
        """
        mandatory_params = [
            {'name': 'table', 'type': 'json', 'mandatory': True, 'description': 'The table data in JSON format'},
            {'name': 'columnName', 'type': 'string', 'mandatory': True, 'description': 'The name of the column to reconcile'},
            {'name': 'idReconciliator', 'type': 'string', 'mandatory': True, 'description': 'The ID of the reconciliator to use'}
        ]
        
        reconciliator_data = self.get_reconciliator_data()
        if not reconciliator_data:
            return None

        for reconciliator in reconciliator_data:
            if reconciliator['id'] == id_reconciliator:
                parameters = reconciliator.get('formParams', [])
                optional_params = [
                    {
                        'name': param['id'],
                        'type': param['inputType'],
                        'mandatory': 'required' in param.get('rules', []),
                        'description': param.get('description', ''),
                        'label': param.get('label', ''),
                        'infoText': param.get('infoText', '')
                    } for param in parameters
                ]

                param_dict = {
                    'mandatory': mandatory_params,
                    'optional': optional_params
                }

                if print_params:
                    print(f"Parameters for reconciliator '{id_reconciliator}':")
                    print("Mandatory parameters:")
                    for param in param_dict['mandatory']:
                        print(f"- {param['name']} ({param['type']}): Mandatory")
                        print(f"  Description: {param['description']}")
                    
                    print("\nOptional parameters:")
                    for param in param_dict['optional']:
                        mandatory = "Mandatory" if param['mandatory'] else "Optional"
                        print(f"- {param['name']} ({param['type']}): {mandatory}")
                        print(f"  Description: {param['description']}")
                        print(f"  Label: {param['label']}")
                        print(f"  Info Text: {param['infoText']}")

                return param_dict

        return None
    