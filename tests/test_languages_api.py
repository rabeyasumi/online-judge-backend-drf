from submissions.languages import LANGUAGES

URL = '/api/submissions/languages/'


def test_is_public(anon_client):
    assert anon_client.get(URL).status_code == 200


def test_returns_every_configured_language(anon_client):
    data = anon_client.get(URL).json()
    assert data == LANGUAGES
    assert len(data) == 19


def test_each_item_has_the_fields_the_frontend_needs(anon_client):
    for item in anon_client.get(URL).json():
        assert set(item) >= {'label', 'language', 'version_index'}


def test_language_codes_are_unique(anon_client):
    codes = [item['language'] for item in anon_client.get(URL).json()]
    assert len(codes) == len(set(codes))


def test_common_languages_are_available(anon_client):
    codes = {item['language'] for item in anon_client.get(URL).json()}
    assert {'c', 'cpp17', 'java', 'python3', 'nodejs'} <= codes
