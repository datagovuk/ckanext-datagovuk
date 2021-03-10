import json
import pytest

from ckan.tests import factories


@pytest.fixture
def sample_org():
    user = factories.User()
    organization = factories.Organization(
        users=[{'name': user['id'], 'capacity': 'admin'}]
    )
    return organization


@pytest.fixture
def sample_dataset(sample_org):
    dataset = factories.Dataset(
      name='some-dataset', title='A test dataset', owner_org=sample_org['id']
    )
    return dataset



@pytest.mark.usefixtures("clean_db", "with_plugins", "with_request_context")
class TestViews:

    def test_search_dataset_has_results_element_at_root(self, app, sample_dataset):
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=f'/api/search/dataset?q=name:{sample_dataset["name"]}&fl=*',
            extra_environ=env,
        )
        json_resp = json.loads(response.get_data())
        assert 'results' in json_resp.keys()

    def test_search_dataset_v3_has_result_element_at_root(self, app, sample_dataset):
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=f'/api/3/search/dataset?q=name:{sample_dataset["name"]}&fl=*',
            extra_environ=env,
        )
        json_resp = json.loads(response.get_data())
        assert 'result' in json_resp.keys()
