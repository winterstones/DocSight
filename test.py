import requests, re
s = requests.Session()
s.post('http://localhost:8000/api/auth/login/', json={'username':'operator_b', 'password':'operator123'})
r2 = s.get('http://localhost:8000/api/search/?q=test')
match = re.search(r'exception_value.>(.*?)</', r2.text)
if match: print(match.group(1))
else: print('Not found')
