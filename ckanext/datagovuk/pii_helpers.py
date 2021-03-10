import copy
import json

PII_LIST = [
    'author',
    'author_email',
    'maintainer',
    'maintainer_email'
]


def remove_pii_from_api_search_dataset(json_data, json_dumps=True):
    if isinstance(json_data, str):
        try:
            json_data = json.loads(json_data)
        except:
            return
    new_json_data = copy.deepcopy(json_data)
    if 'results' in json_data.keys():
        for i in range(len(json_data['results'])):
            new_json_data['results'][i] = remove_pii_from_api_search_dataset(
                json_data['results'][i], json_dumps=False)
    else:
        for k, v in json_data.items():
            if k in ['data_dict', 'validated_data_dict']:
                if isinstance(json_data[k], str):
                    new_json_data[k] = json.loads(json_data[k])

                new_json_data[k] = remove_pii_block(new_json_data[k])
            elif k =='extras':
                new_json_data[k] = remove_pii(json_data[k])
            elif hasattr(json_data[k], 'keys'):
                new_json_data[k] = remove_pii(json_data[k])
        
        new_json_data = remove_pii(new_json_data)

    return json.dumps(new_json_data) if json_dumps else new_json_data


def remove_pii(element):
    valid_element = {}
    if not isinstance(element, dict):
        return element
    for key in element.keys():
        if key not in PII_LIST:
            valid_element[key] = element[key]
    return valid_element


def remove_pii_block(json_data):
    new_json_data = {}
    for key in json_data.keys():
        if key == 'extras':
            extras = [e for e in json_data['extras'] if e['key'] not in PII_LIST]
            new_json_data['extras'] = extras
        elif key not in PII_LIST:
            new_json_data[key] = json_data[key]

    return json.dumps(new_json_data)
