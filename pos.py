import requests

# Make sure your file exists
response = requests.post('http://localhost:8000/analyze',
                        files={'file': open('data/blood_test_report.pdf', 'rb')},
                        data={'query': 'Analyze my report', 'async_processing': True})

print(response.json())
task_id = response.json()['task_id']

# Check status
status_response = requests.get(f'http://localhost:8000/task/{task_id}')
print(status_response.json())