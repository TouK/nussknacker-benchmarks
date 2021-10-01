import zipfile
import requests
from io import BytesIO,TextIOWrapper
import csv
import os

token = os.environ.get('TOKEN')

def invokeGithub(url): 
    headers = {'Authorization': "Bearer {}".format(token)}
    return requests.get(url, headers=headers)

def getJson(url):
    return invokeGithub(url).json()

def zipContent(url):
    content = invokeGithub(url).content
    zip_file_object = zipfile.ZipFile(BytesIO(content))
    first_file = zip_file_object.namelist()[0]
    file = zip_file_object.open(first_file)
    return TextIOWrapper(file)

def urlWithDate(artifactList):
    if not artifactList['artifacts']:
        return None
    artifact = artifactList['artifacts'][0]
    return {'url': artifact['archive_download_url'], 'date': artifact['created_at']}

def allArtifactsWithDates(project, name):
    workflowRuns = getJson(f"https://api.github.com/repos/touk/{project}/actions/workflows/{name}/runs")
    artifactsUrls = list(map(lambda workflow: workflow['artifacts_url'], workflowRuns['workflow_runs']))
    artifactsObjects = list(map(lambda url: getJson(url), artifactsUrls))
    return list(filter(None, map(urlWithDate, artifactsObjects)))

def appendFileJson(content, date, csvWriter, skipFirst):
    reader = csv.reader(content)
    if skipFirst:
        next(reader)
    for idx, row in enumerate(reader):
        csvWriter.writerow([date if (skipFirst or idx > 0) else 'Date'] + row)

def appendFileLines(content, date, csvWriter, skipFirst):
    lines = content.read(-1).splitlines()
    if not skipFirst:
        csvWriter.writerow(["Date", "Step", "Value"])
    for i in range(0, len(lines), 2):
        csvWriter.writerow([date] + lines[i:i + 2])


def rewriteToCsv(urlWithDates, appendFile, name):
    with open(f"data/{name}.csv", 'w', newline='') as csvfile:
        aggregated = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for idx, urlWithDate in enumerate(urlWithDates):
            content = zipContent(urlWithDate['url'])
            appendFile(content, urlWithDate['date'], aggregated, idx > 0)    

rewriteToCsv(allArtifactsWithDates("nussknacker", "benchmark.yml"), appendFileJson, 'microbenchmarks')
rewriteToCsv(allArtifactsWithDates("nussknacker-quickstart", "benchmark-workflow.yml"), appendFileLines, 'e2e')


