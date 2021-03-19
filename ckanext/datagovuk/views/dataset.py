from ckan.views.api import action
from ckanext.datagovuk.pii_helpers import remove_pii_from_api_search_dataset


def dataset_search(ver=1):
    data = action('package_search', ver=ver)
    return remove_pii_from_api_search_dataset(
        data.json.get('result') if ver == 1 else data.json
    )


def dataset_search_v3():
    return dataset_search(3)
