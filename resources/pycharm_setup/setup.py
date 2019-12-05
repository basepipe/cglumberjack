import requests

authorization = "Bearer 0/60638fd908735ac8ed156242a9d39887"


class SetupGUI:

    def __init__(self):
        print "hello"

    def get_projects(self):
        result = []
        response = requests.get("https://app.asana.com/api/1.0/projects", headers={'Authorization': authorization})
        for r in response.json()['data']:
            print r['name']
            result.append(r['name'])
        return result

if __name__ == "__main__":
    g = SetupGUI()
    g.get_projects()
