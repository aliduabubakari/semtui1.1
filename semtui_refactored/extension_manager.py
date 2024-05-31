import requests
import json
import pandas as pd
from reconciliation_manager import ReconciliationManager  # Assuming this class is defined in reconciliation_manager.py

class ExtensionManager:
    def __init__(self, api_url, token):
        self.api_url = api_url
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.reconciliation_manager = ReconciliationManager(api_url, token)  # Dependency Injection

    def get_extender(self, id_extender, response):
        """
        Given the extender's ID, returns the main information in JSON format

        :id_extender: the ID of the extender in question
        :response: JSON containing information about the extenders
        :return: JSON containing the main information of the extender
        """
        for extender in response:
            if extender['id'] == id_extender:
                return {
                    'name': extender['name'],
                    'relativeUrl': extender['relativeUrl']
                }
        return None
    
    def get_extender_data(self):
        """
        Retrieves extender data from the backend

        :return: data of extension services in JSON format
        """
        try:
            response = requests.get(f"{self.api_url}extenders/list", headers=self.headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()
        except requests.RequestException as e:
            print(f"Error occurred while retrieving extender data: {e}")
            return None
    
    def get_extenders_list(self):
        """
        Provides a list of available extenders with their main information.

        :return: DataFrame containing extenders and their information.
        """
        response = self.get_extender_data()
        if response:
            return self.clean_service_list(response)
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

    def create_extension_payload(self, data, reconciliated_column_name, properties, id_extender, dates, weather_params, decimal_format=None):
        """
        Creates the payload for the extension request

        :param data: table in raw format
        :param reconciliated_column_name: the name of the column containing reconciled id
        :param properties: the properties to use in a list format
        :param id_extender: the ID of the extender service
        :param dates: a dictionary containing the date information for each row
        :param weather_params: a list of weather parameters to include in the request
        :param decimal_format: the decimal format to use for the values (default: None)
        :return: the request payload
        """
        items = {}
        if 'rows' not in data:
            raise KeyError("The 'data' dictionary does not contain the 'rows'")
        rows = data['rows'].keys()
        for row in rows:
            if 'cells' not in data['rows'][row]:
                raise KeyError(f"The 'data['rows'][{row}]' dictionary does not contain the 'cells' key.")
            
            cell = data['rows'][row]['cells'].get(reconciliated_column_name)
            if cell and cell.get('annotationMeta', {}).get('match', {}).get('value') == True:
                for metadata in cell.get('metadata', []):
                    if metadata.get('match') == True:
                        items[row] = metadata.get('id')
                        break    
        payload = {
            "serviceId": id_extender,
            "items": {
                str(reconciliated_column_name): items
            },
            "property": properties,
            "dates": dates,
            "weatherParams": weather_params,
            "decimalFormat": decimal_format or []
        }
        
        return payload
    
    def get_reconciliator_from_prefix(self, prefix_reconciliator, response):
        """
        Function that, given the reconciliator's prefix, returns a dictionary 
        with all the service information

        :prefix_reconciliator: the prefix of the reconciliator in question
        :return: a dictionary with the reconciliator's information
        """
        for reconciliator in response:
            if reconciliator['prefix'] == prefix_reconciliator:
                return {
                    'uri': reconciliator['uri'],
                    'id': reconciliator['id'],
                    'name': reconciliator['name'],
                    'relativeUrl': reconciliator['relativeUrl']
                }
        return None

    def get_column_id_reconciliator(self, table, column_name, reconciliator_response):
        """
        Specifying the column of interest returns the reconciliator's ID,
        if the column is reconciled

        :table: table in raw format
        :column_name: name of the column in question
        :return: the ID of the reconciliator used
        """
        prefix = list(table['columns'][column_name]['context'].keys())
        return self.get_reconciliator_from_prefix(prefix[0], reconciliator_response)['id']

    def check_entity(self, new_column_data):
        entity = False
        # Assuming newColumnData refers to a row payload, which contains a 'cells' list
        for cell in new_column_data['cells']:
            # Check if there is metadata and it's not empty
            if 'metadata' in cell and cell['metadata']:
                entity = True
                break
        return entity

    def parse_name_entities(self, entities, uri_reconciliator):
        """
        Function iterated in parseNameMetadata, works at the entity level

        :param entities: List of entities present in the cell/column
        :param uri_reconciliator: the URI of the affiliated knowledge graph
        :return: List of entities with updated names
        """
        for entity in entities:
            if 'id' in entity and ':' in entity['id']:
                entity_type = entity['id'].split(':')[1]  # Safely extract after colon
                entity['name'] = self.reconciliation_manager.parse_name_field(
                    entity.get('name', ''),  # Safely access 'name'
                    uri_reconciliator,
                    entity_type
                )
        return entities

    def add_extended_cell(self, table, new_column_data, new_column_name, id_reconciliator, reconciliator_response):
        if 'cells' not in new_column_data:
            raise ValueError("newColumnData must contain 'cells'")
        
        row_keys = new_column_data['cells']
        entity = self.check_entity(new_column_data)
        column_type = new_column_data.get('kind', 'entity' if entity else 'literal')

        for row_key in row_keys:
            cell_data = new_column_data['cells'][row_key]
            new_cell = table['rows'][row_key]['cells'].setdefault(new_column_name, {})
            new_cell['id'] = f"{row_key}${new_column_name}"
            new_cell['label'] = cell_data.get('label', '')

            uri_reconciliator = self.reconciliation_manager.get_reconciliator(id_reconciliator, reconciliator_response)['uri']
            new_cell['metadata'] = self.parse_name_entities(cell_data.get('metadata', []), uri_reconciliator)

            if column_type == 'entity':
                new_cell['annotationMeta'] = self.reconciliation_manager.create_annotation_meta_cell(new_cell['metadata'])
            else:
                new_cell['annotationMeta'] = {}

        return table

    def add_extended_columns(self, table, extension_data, new_columns_name, reconciliator_response):
        """
        Allows iterating the operations to insert a single column for
        all the properties to be inserted.

        :param table: table in raw format
        :param extension_data: data obtained from the extender
        :param new_columns_name: names of the new columns to insert into the table
        :param reconciliator_response: response containing reconciliator information
        :return: the table with the new fields inserted
        """
        if 'columns' not in extension_data or 'meta' not in extension_data:
            raise ValueError("extensionData must contain 'columns' and 'meta'")

        # Iterating through new columns to be added
        for i, column_key in enumerate(extension_data['columns'].keys()):
            if i >= len(new_columns_name):
                raise IndexError("There are more columns to add than names provided.")
            
            # Fetching reconciliator ID for the current column
            id_reconciliator = self.get_column_id_reconciliator(
                table, extension_data['meta'][column_key], reconciliator_response)
            
            # Adding the extended cell/column to the table
            table = self.add_extended_cell(
                table, extension_data['columns'][column_key], new_columns_name[i], id_reconciliator, reconciliator_response)
            
        return table

    def extend_column(self, table, reconciliated_column_name, id_extender, properties, new_columns_name, date_column_name, weather_params, decimal_format=None):
        """
        Extends the specified properties present in the Knowledge Graph as new columns.

        :param table: the table containing the data
        :param reconciliated_column_name: the column containing the ID in the KG
        :param id_extender: the extender to use for extension
        :param properties: the properties to extend in the table
        :param new_columns_name: the names of the new columns to add
        :param date_column_name: the name of the date column to extract date information for each row
        :param weather_params: a list of weather parameters to include in the request
        :param decimal_format: the decimal format to use for the values (default: None)
        :return: the extended table
        """
        reconciliator_response = self.reconciliation_manager.get_reconciliator_data()
        extender_data = self.get_extender(id_extender, self.get_extender_data())
        
        if extender_data is None:
            raise ValueError(f"Extender with ID '{id_extender}' not found.")
        
        url = self.api_url + "extenders/" + extender_data['relativeUrl']
        
        # Prepare the dates information dynamically
        dates = {}
        for row_key, row_data in table['rows'].items():
            date_value = row_data['cells'].get(date_column_name, {}).get('label')
            if date_value:
                dates[row_key] = [date_value]
            else:
                print(f"Missing or invalid date for row {row_key}, skipping this row.")
                continue  # Optionally skip this row or handle accordingly
        decimal_format = ["comma"]  # Use comma as the decimal separator
        payload = self.create_extension_payload(table, reconciliated_column_name, properties, id_extender, dates, weather_params, decimal_format)
        headers = {"Accept": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            table = self.add_extended_columns(table, data, new_columns_name, reconciliator_response)
            return table
        except requests.RequestException as e:
            print(f"An error occurred while making the request: {e}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    
    def get_extender_parameters(self, id_extender, print_params=False):
        """
        Retrieves the parameters needed for a specific extender service.

        :param id_extender: The ID of the extender service.
        :param print_params: (optional) Whether to print the retrieved parameters or not.
        :return: A dictionary containing the parameter details, or None if the extender is not found.
        """
        extender_data = self.get_extender_data()
        if not extender_data:
            return None
        
        for extender in extender_data:
            if extender['id'] == id_extender:
                parameters = extender.get('formParams', [])
                mandatory_params = [
                    {
                        'name': param['id'],
                        'type': param['inputType'],
                        'mandatory': 'required' in param.get('rules', []),
                        'description': param.get('description', ''),
                        'label': param.get('label', ''),
                        'infoText': param.get('infoText', ''),
                        'options': param.get('options', [])
                    } for param in parameters if 'required' in param.get('rules', [])
                ]
                optional_params = [
                    {
                        'name': param['id'],
                        'type': param['inputType'],
                        'mandatory': 'required' in param.get('rules', []),
                        'description': param.get('description', ''),
                        'label': param.get('label', ''),
                        'infoText': param.get('infoText', ''),
                        'options': param.get('options', [])
                    } for param in parameters if 'required' not in param.get('rules', [])
                ]

                param_dict = {
                    'mandatory': mandatory_params,
                    'optional': optional_params
                }

                if print_params:
                    print(f"Parameters for extender '{id_extender}':")
                    print("Mandatory parameters:")
                    for param in param_dict['mandatory']:
                        print(f"- {param['name']} ({param['type']}): Mandatory")
                        print(f"  Description: {param['description']}")
                        print(f"  Label: {param['label']}")
                        print(f"  Info Text: {param['infoText']}")
                        print(f"  Options: {param['options']}")
                        print("")

                    print("Optional parameters:")
                    for param in param_dict['optional']:
                        print(f"- {param['name']} ({param['type']}): Optional")
                        print(f"  Description: {param['description']}")
                        print(f"  Label: {param['label']}")
                        print(f"  Info Text: {param['infoText']}")
                        print(f"  Options: {param['options']}")
                        print("")

                return param_dict

        print(f"Extender with ID '{id_extender}' not found.")
        return None
