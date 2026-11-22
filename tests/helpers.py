

def submit(client, problem, code='print(3)', language='python3', **extra):
    """POST /api/submissions/ for a problem."""
    payload = {'problem_id': problem.id, 'language': language, 'code': code}
    payload.update(extra)
    return client.post('/api/submissions/', payload, format='json')


def results_of(response):
    """List endpoints may return a plain list or a paginated {'results': [...]}."""
    data = response.json()
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    return data
