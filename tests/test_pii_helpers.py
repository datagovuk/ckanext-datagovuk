import json
import unittest

from ckanext.datagovuk.pii_helpers import (
    remove_pii_from_api_search_dataset, remove_pii,
    PII_LIST
)


sample_package_search_result = {
    "count": 1,
    "sort": "score desc, metadata_modified desc",
    "facets": {},
    "results": [
        {
            "license_title": "Creative Commons Attribution",
            "maintainer": None,
            "contact-phone": "",
            "relationships_as_object": [],
            "private": False,
            "maintainer_email": None,
            "num_tags": 0,
            "organization": {
                "description": "",
                "created": "2019-08-28T12:00:00",
                "title": "test",
                "name": "test",
                "is_organization": True,
                "state": "active",
                "image_url": "",
                "revision_id": "revision_id",
                "type": "organization",
                "id": "org_id",
                "approval_status": "approved"
            },
            "foi-email": "test-foi@example.com",
            "id": "data_id",
            "metadata_created": "2019-08-28T11:00:00",
            "licence-custom": "",
            "metadata_modified": "2019-08-28T11:00:00",
            "author": None,
            "author_email": None,
            "state": "active",
            "version": None,
            "license_id": "cc-by",
            "foi-web": "",
            "resources": [
                {
                    "mimetype": None,
                    "cache_url": None,
                    "hash": "",
                    "description": "",
                    "name": "Example dataset",
                    "format": "",
                    "url": "https://example.com/datasets/dataset_id",
                    "datafile-date": "",
                    "cache_last_updated": None,
                    "resource-type": "data-link",
                    "package_id": "dataset_id",
                    "created": "2019-08-28T12:00:00",
                    "state": "active",
                    "mimetype_inner": None,
                    "last_modified": None,
                    "position": 0,
                    "revision_id": "revision_id",
                    "url_type": None,
                    "id": "resource_id",
                    "resource_type": None,
                    "size": None
                }
            ],
            "num_resources": 1,
            "contact-email": "test@example.com",
            "tags": [],
            "foi-name": "",
            "groups": [],
            "creator_user_id": "user_id",
            "relationships_as_subject": [],
            "codelist": "",
            "contact-name": "Test User",
            "name": "test",
            "isopen": True,
            "schema-vocabulary": "",
            "url": None,
            "type": "dataset",
            "notes": "",
            "owner_org": "org_id",
            "license_url": "http://www.opendefinition.org/licenses/cc-by",
            "title": "test",
            "revision_id": "revision_id",
            "foi-phone": "",
            "theme-primary": ""
        }
    ],
    "search_facets": {}
}

sample_api_search_dataset = {
    "count": 1,
    "facets": {},
    "results": [
    {
        "id": "a18d2811-13b0-4838-8bfb-5793433317b9",
        "name": "example-dataset-number-one",
        "title": "Example Dataset #1",
        "url": "http://static-mock-harvest-source:11088/mock-third-party/example-dataset-1/about",
        "notes": "This is an example CKAN dataset consisting of a number of active resources.",
        "license_id": "uk-ogl",
        "metadata_created": "2021-03-05T12:03:39.772Z",
        "metadata_modified": "2021-03-05T12:03:39.772Z",
        "state": "active",
        "organization": "example-publisher-1",
        "harvest": ["{\"key\": \"harvest_object_id\", \"value\": \"88400dc8-e493-4b0b-a37c-4803572a7dca\"}", "{\"key\": \"harvest_source_id\", \"value\": \"c52db9bf-9acb-4a47-b11c-009ccf4bb381\"}", "{\"key\": \"harvest_source_title\", \"value\": \"Example Harvest #1\"}"], 
        "validated_data_dict": "{\"author\": null, \"author_email\": null, \"codelist\": \"\", \"contact-email\": \"\", \"contact-name\": \"Example User\", \"contact-phone\": \"\", \"creator_user_id\": \"597dc643-c335-402b-90f1-e72b7ed27169\", \"foi-email\": \"\", \"foi-name\": \"\", \"foi-phone\": \"\", \"foi-web\": \"\", \"id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"isopen\": true, \"licence-custom\": \"\", \"license_id\": \"uk-ogl\", \"license_title\": \"UK Open Government Licence (OGL)\", \"license_url\": \"http://reference.data.gov.uk/id/open-government-licence\", \"maintainer\": null, \"maintainer_email\": null, \"metadata_created\": \"2021-03-05T12:03:39.772848\", \"metadata_modified\": \"2021-03-05T12:03:39.772867\", \"name\": \"example-dataset-number-one\", \"notes\": \"This is an example CKAN dataset consisting of a number of active resources.\", \"num_resources\": 4, \"num_tags\": 1, \"organization\": {\"id\": \"66f1850e-2138-4fda-b15d-dda31e995c7e\", \"name\": \"example-publisher-1\", \"title\": \"Example Publisher #1\", \"type\": \"organization\", \"description\": \"\", \"image_url\": \"\", \"created\": \"2021-03-05T12:03:35.727220\", \"is_organization\": true, \"approval_status\": \"approved\", \"state\": \"active\"}, \"owner_org\": \"66f1850e-2138-4fda-b15d-dda31e995c7e\", \"private\": false, \"schema-vocabulary\": \"\", \"state\": \"active\", \"theme-primary\": \"\", \"title\": \"Example Dataset #1\", \"type\": \"dataset\", \"url\": \"http://static-mock-harvest-source:11088/mock-third-party/example-dataset-1/about\", \"version\": null, \"extras\": [{\"key\": \"harvest_object_id\", \"value\": \"88400dc8-e493-4b0b-a37c-4803572a7dca\"}, {\"key\": \"harvest_source_id\", \"value\": \"c52db9bf-9acb-4a47-b11c-009ccf4bb381\"}, {\"key\": \"harvest_source_title\", \"value\": \"Example Harvest #1\"}], \"resources\": [{\"cache_last_updated\": null, \"cache_url\": null, \"created\": \"2021-03-05T12:03:39.778124\", \"description\": \"Example Dataset #1 - summary of findings\", \"format\": \"PDF\", \"hash\": \"\", \"id\": \"1c217a07-21f1-4e98-b4fa-f9d6009f4151\", \"last_modified\": null, \"metadata_modified\": \"2021-03-05T12:03:39.758062\", \"mimetype\": null, \"mimetype_inner\": null, \"name\": null, \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"position\": 0, \"resource_type\": null, \"size\": null, \"state\": \"active\", \"url\": \"http://static-mock-harvest-source:11088/mock-third-party/example-dataset-1/findings.pdf\", \"url_type\": null}, {\"cache_last_updated\": null, \"cache_url\": null, \"created\": \"2021-03-05T12:03:39.778139\", \"description\": \"Example Dataset #1 - benchmark\", \"format\": \"PDF\", \"hash\": \"\", \"id\": \"9c32745b-d611-4d8c-bec0-4615fb9464d7\", \"last_modified\": null, \"metadata_modified\": \"2021-03-05T12:03:39.759916\", \"mimetype\": null, \"mimetype_inner\": null, \"name\": null, \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"position\": 1, \"resource_type\": null, \"size\": null, \"state\": \"active\", \"url\": \"http://static-mock-harvest-source:11088/mock-third-party/example-dataset-1/benchmark.pdf\", \"url_type\": null}, {\"cache_last_updated\": null, \"cache_url\": null, \"created\": \"2021-03-05T12:03:39.778152\", \"description\": \"Example Dataset #1 - summary of category scores (XLS)\", \"format\": \"XLS\", \"hash\": \"\", \"id\": \"67eefa14-86de-4a3f-8fe3-3804ff08f8ce\", \"last_modified\": null, \"metadata_modified\": \"2021-03-05T12:03:39.761777\", \"mimetype\": null, \"mimetype_inner\": null, \"name\": null, \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"position\": 2, \"resource_type\": null, \"size\": null, \"state\": \"active\", \"url\": \"http://static-mock-harvest-source:11088/mock-third-party/example-dataset-1/all-categories-summary.xls\", \"url_type\": null}, {\"cache_last_updated\": null, \"cache_url\": null, \"created\": \"2021-03-05T12:03:39.778164\", \"description\": \"Example Dataset #1 - summary of category scores (CSV)\", \"format\": \"CSV\", \"hash\": \"\", \"id\": \"27ec6d83-7f13-4daf-ba90-227f4271d7f6\", \"last_modified\": null, \"metadata_modified\": \"2021-03-05T12:03:39.763987\", \"mimetype\": null, \"mimetype_inner\": null, \"name\": null, \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"position\": 3, \"resource_type\": null, \"size\": null, \"state\": \"active\", \"url\": \"http://static-mock-harvest-source:11088/mock-third-party/example-dataset-1/all-categories-summary.csv\", \"url_type\": null}], \"tags\": [{\"display_name\": \"example-data\", \"id\": \"56d6b78f-9494-41fb-955b-08b3659bfe80\", \"name\": \"example-data\", \"state\": \"active\", \"vocabulary_id\": null}], \"groups\": [], \"relationships_as_subject\": [], \"relationships_as_object\": []}",
        "tags": [
            "example-data"
        ],
        "capacity": "public",
        "res_description": [
            "Example Dataset #1 - summary of findings",
            "Example Dataset #1 - benchmark",
            "Example Dataset #1 - summary of category scores (XLS)",
            "Example Dataset #1 - summary of category scores (CSV)"
        ],
        "res_format": [
            "PDF",
            "PDF",
            "XLS",
            "CSV"
        ],
        "res_url": [
            "http://static-mock-harvest-source:11088/mock-third-party/example-dataset-1/findings.pdf",
            "http://static-mock-harvest-source:11088/mock-third-party/example-dataset-1/benchmark.pdf",
            "http://static-mock-harvest-source:11088/mock-third-party/example-dataset-1/all-categories-summary.xls",
            "http://static-mock-harvest-source:11088/mock-third-party/example-dataset-1/all-categories-summary.csv"
        ],
        "entity_type": "package",
        "dataset_type": "dataset",
        "site_id": "default",
        "index_id": "78a56565b87a9c722e4893ef9bfe4a06",
        "_version_": "1693393432794365952",
        "indexed_ts": "2021-03-05T12:03:44.426Z",
        "data_dict": "{\"id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"name\": \"example-dataset-number-one\", \"title\": \"Example Dataset #1\", \"version\": null, \"url\": \"http://static-mock-harvest-source:11088/mock-third-party/example-dataset-1/about\", \"notes\": \"This is an example CKAN dataset consisting of a number of active resources.\", \"license_id\": \"uk-ogl\", \"type\": \"dataset\", \"owner_org\": \"66f1850e-2138-4fda-b15d-dda31e995c7e\", \"creator_user_id\": \"597dc643-c335-402b-90f1-e72b7ed27169\", \"metadata_created\": \"2021-03-05T12:03:39.772848\", \"metadata_modified\": \"2021-03-05T12:03:39.772867\", \"private\": false, \"state\": \"active\", \"resources\": [{\"id\": \"1c217a07-21f1-4e98-b4fa-f9d6009f4151\", \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"url\": \"http://static-mock-harvest-source:11088/mock-third-party/example-dataset-1/findings.pdf\", \"format\": \"PDF\", \"description\": \"Example Dataset #1 - summary of findings\", \"hash\": \"\", \"position\": 0, \"name\": null, \"resource_type\": null, \"mimetype\": null, \"mimetype_inner\": null, \"size\": null, \"created\": \"2021-03-05T12:03:39.778124\", \"last_modified\": null, \"metadata_modified\": \"2021-03-05T12:03:39.758062\", \"cache_url\": null, \"cache_last_updated\": null, \"url_type\": null, \"state\": \"active\"}, {\"id\": \"9c32745b-d611-4d8c-bec0-4615fb9464d7\", \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"url\": \"http://static-mock-harvest-source:11088/mock-third-party/example-dataset-1/benchmark.pdf\", \"format\": \"PDF\", \"description\": \"Example Dataset #1 - benchmark\", \"hash\": \"\", \"position\": 1, \"name\": null, \"resource_type\": null, \"mimetype\": null, \"mimetype_inner\": null, \"size\": null, \"created\": \"2021-03-05T12:03:39.778139\", \"last_modified\": null, \"metadata_modified\": \"2021-03-05T12:03:39.759916\", \"cache_url\": null, \"cache_last_updated\": null, \"url_type\": null, \"state\": \"active\"}, {\"id\": \"67eefa14-86de-4a3f-8fe3-3804ff08f8ce\", \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"url\": \"http://static-mock-harvest-source:11088/mock-third-party/example-dataset-1/all-categories-summary.xls\", \"format\": \"XLS\", \"description\": \"Example Dataset #1 - summary of category scores (XLS)\", \"hash\": \"\", \"position\": 2, \"name\": null, \"resource_type\": null, \"mimetype\": null, \"mimetype_inner\": null, \"size\": null, \"created\": \"2021-03-05T12:03:39.778152\", \"last_modified\": null, \"metadata_modified\": \"2021-03-05T12:03:39.761777\", \"cache_url\": null, \"cache_last_updated\": null, \"url_type\": null, \"state\": \"active\"}, {\"id\": \"27ec6d83-7f13-4daf-ba90-227f4271d7f6\", \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"url\": \"http://static-mock-harvest-source:11088/mock-third-party/example-dataset-1/all-categories-summary.csv\", \"format\": \"CSV\", \"description\": \"Example Dataset #1 - summary of category scores (CSV)\", \"hash\": \"\", \"position\": 3, \"name\": null, \"resource_type\": null, \"mimetype\": null, \"mimetype_inner\": null, \"size\": null, \"created\": \"2021-03-05T12:03:39.778164\", \"last_modified\": null, \"metadata_modified\": \"2021-03-05T12:03:39.763987\", \"cache_url\": null, \"cache_last_updated\": null, \"url_type\": null, \"state\": \"active\"}], \"num_resources\": 4, \"tags\": [{\"id\": \"56d6b78f-9494-41fb-955b-08b3659bfe80\", \"name\": \"example-data\", \"vocabulary_id\": null, \"state\": \"active\", \"display_name\": \"example-data\"}], \"num_tags\": 1, \"extras\": [{\"id\": \"99fe3b0a-a3e6-4929-b718-5b8cbf6d0a56\", \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"key\": \"codelist\", \"value\": \"\", \"state\": \"active\"}, {\"id\": \"4b75b5be-7c3a-49c9-b360-3b239fb36df0\", \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"key\": \"contact-email\", \"value\": \"\", \"state\": \"active\"}, {\"id\": \"c0d678dd-6788-4d60-9d13-303c70ce18ca\", \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"key\": \"contact-name\", \"value\": \"Example User\", \"state\": \"active\"}, {\"id\": \"5c913308-5631-460c-91f1-6195c188d7ea\", \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"key\": \"contact-phone\", \"value\": \"\", \"state\": \"active\"}, {\"id\": \"10329d5d-f1d8-462b-b5a1-0a826b3a7934\", \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"key\": \"foi-email\", \"value\": \"\", \"state\": \"active\"}, {\"id\": \"1c281258-619f-4506-b2dc-60b6ac87219e\", \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"key\": \"foi-name\", \"value\": \"\", \"state\": \"active\"}, {\"id\": \"aa20ff78-9604-48f3-bffe-bd839b6eaa69\", \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"key\": \"foi-phone\", \"value\": \"\", \"state\": \"active\"}, {\"id\": \"44f31508-0d3e-483e-89a6-91131cd58c77\", \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"key\": \"foi-web\", \"value\": \"\", \"state\": \"active\"}, {\"id\": \"d271775a-4363-4f8b-8abb-7eaf5fa886f2\", \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"key\": \"licence-custom\", \"value\": \"\", \"state\": \"active\"}, {\"id\": \"c903aed7-1211-4f55-8c18-ab3b5c8de79a\", \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"key\": \"schema-vocabulary\", \"value\": \"\", \"state\": \"active\"}, {\"id\": \"9c365f3a-cc75-4a13-bd3c-dd0ea266a419\", \"package_id\": \"a18d2811-13b0-4838-8bfb-5793433317b9\", \"key\": \"theme-primary\", \"value\": \"\", \"state\": \"active\"}, {\"key\": \"harvest_object_id\", \"value\": \"88400dc8-e493-4b0b-a37c-4803572a7dca\", \"state\": \"active\"}, {\"key\": \"harvest_source_id\", \"value\": \"c52db9bf-9acb-4a47-b11c-009ccf4bb381\", \"state\": \"active\"}, {\"key\": \"harvest_source_title\", \"value\": \"Example Harvest #1\", \"state\": \"active\"}], \"groups\": [], \"organization\": {\"id\": \"66f1850e-2138-4fda-b15d-dda31e995c7e\", \"name\": \"example-publisher-1\", \"title\": \"Example Publisher #1\", \"type\": \"organization\", \"description\": \"\", \"image_url\": \"\", \"created\": \"2021-03-05T12:03:35.727220\", \"is_organization\": true, \"approval_status\": \"approved\", \"state\": \"active\"}, \"relationships_as_subject\": [], \"relationships_as_object\": [], \"isopen\": true, \"license_url\": \"http://reference.data.gov.uk/id/open-government-licence\", \"license_title\": \"UK Open Government Licence (OGL)\", \"harvest\": [{\"key\": \"harvest_object_id\", \"value\": \"88400dc8-e493-4b0b-a37c-4803572a7dca\"}, {\"key\": \"harvest_source_id\", \"value\": \"c52db9bf-9acb-4a47-b11c-009ccf4bb381\"}, {\"key\": \"harvest_source_title\", \"value\": \"Example Harvest #1\"}]}",
        "contact-name": "Example User",
        "harvest_object_id": "88400dc8-e493-4b0b-a37c-4803572a7dca",
        "harvest_source_id": "c52db9bf-9acb-4a47-b11c-009ccf4bb381",
        "harvest_source_title": "Example Harvest #1"
        }
    ],
    "sort": "score desc, metadata_modified desc",
    "search_facets": {}
}

sample_package_show_result = {
    "license_title": "Creative Commons Attribution",
    "maintainer": None,
    "contact-phone": "",
    "relationships_as_object": [],
    "private": False,
    "maintainer_email": None,
    "num_tags": 0,
    "organization": {
        "description": "",
        "created": "2019-08-28T12:00:00",
        "title": "test",
        "name": "test",
        "is_organization": True,
        "state": "active",
        "image_url": "",
        "revision_id": "revision_id",
        "type": "organization",
        "id": "org_id",
        "approval_status": "approved"
    },
    "foi-email": "test-foi@example.com",
    "id": "id",
    "metadata_created": "2019-08-28T11:00:00",
    "licence-custom": "",
    "metadata_modified": "2019-08-28T11:00:00",
    "author": None,
    "author_email": None,
    "state": "active",
    "version": None,
    "license_id": "cc-by",
    "foi-web": "",
    "resources": [
        {
            "mimetype": None,
            "cache_url": None,
            "hash": "",
            "description": "",
            "name": "Example",
            "format": "",
            "url": "https://example.com/datasets/dataset_id",
            "datafile-date": "",
            "cache_last_updated": None,
            "resource-type": "data-link",
            "package_id": "dataset_id",
            "created": "2019-08-28T11:00:00",
            "state": "active",
            "mimetype_inner": None,
            "last_modified": None,
            "position": 0,
            "revision_id": "revision_id",
            "url_type": None,
            "id": "resource_id",
            "resource_type": None,
            "size": None
        }
    ],
    "num_resources": 1,
    "contact-email": "test@example.com",
    "tags": [],
    "foi-name": "",
    "groups": [],
    "creator_user_id": "user_id",
    "relationships_as_subject": [],
    "codelist": "",
    "contact-name": "Test User",
    "name": "test",
    "isopen": True,
    "schema-vocabulary": "",
    "url": None,
    "type": "dataset",
    "notes": "",
    "owner_org": "owner_id",
    "license_url": "http://www.opendefinition.org/licenses/cc-by",
    "title": "test",
    "revision_id": "revision_id",
    "foi-phone": "",
    "theme-primary": ""
}


sample_api_search_dataset_without_fields = '''
{
    "count": 1,
    "results": [
        {
            "site_id": "dgu",
            "res_name": [
                "Example dataset"
            ],
            "id": "dataset_id",
            "metadata_created": "2019-08-28T11:00:00Z",
            "capacity": "public",
            "metadata_modified": "2019-08-28T11:00:00Z",
            "entity_type": "package",
            "state": "active",
            "license_id": "cc-by",
            "indexed_ts": "2019-08-28T11:00:00Z",
            "dataset_type": "dataset",
            "res_url": [
                "https://example.com/datasets/dataset_id"
            ],
            "name": "test",
            "title": "test",
            "organization": "test",
            "revision_id": "revision_id",
            "index_id": "index_id"
        }
    ]
}'''

sample_api_search_dataset_strings = '''
{
    "count": 2,
    "results": [
        "test-1",
        "test-2"
    ]
}'''


class TestRemovePII:
    def test_removes_pii_from_package_show(self):
        res = remove_pii(sample_package_show_result.copy())
        assert not any(elem in PII_LIST for elem in res)

    def test_removes_pii_from_api_search_dataset(self):
        res = remove_pii_from_api_search_dataset(sample_api_search_dataset)
        json_res = json.loads(res)['results'][0]

        assert not any(elem in PII_LIST for elem in json_res)

        json_data_dict = json.loads(json_res['data_dict'])
        assert not any(elem in PII_LIST for elem in json_data_dict)

        json_validated_data_dict = json.loads(json_res['validated_data_dict'])
        assert not any(elem in PII_LIST for elem in json_validated_data_dict)

    def test_does_not_error_with_strings_in_response(self):
        remove_pii_from_api_search_dataset(sample_api_search_dataset_strings)

    def test_removes_pii_from_api_search_dataset_without_fields_and_does_not_add_fields(self):
        res = remove_pii_from_api_search_dataset(sample_api_search_dataset_without_fields)
        json_res = json.loads(res)['results'][0]
        assert not any(elem in PII_LIST for elem in json_res)
        assert not any(elem in ['data_dict', 'validated_data_dict', 'extras'] for elem in json_res.keys())

    def test_removes_pii_works_even_if_pii_element_doesnt_exist(self):
        modified_sample_package_show_result = sample_package_show_result.copy()
        del modified_sample_package_show_result['author']

        res = remove_pii(modified_sample_package_show_result)
        assert not any(elem in PII_LIST for elem in res)
