import json
import os
import requests
import sys
import urlparse
from xml.dom import minidom

# Set this to the LAN address of your StashApp server.
# Image URLs comeback as localhost, and if you are running
# Plex on a different server in your network, images won't
# work. Can set to localhost if everything runs on same server.
LAN_ADDRESS = "192.168.50.202"

FRAGMENT = json.loads(sys.stdin.read())
FRAGMENT_SERVER = FRAGMENT["server_connection"]
FRAGMENT_SCENE_ID = FRAGMENT["args"]["hookContext"]["id"]

def printConsole(message):
    print(json.dumps({"output": message}))

# GraphQL functions taken from: https://github.com/stashapp/CommunityScripts/blob/52cc6cbfc212e6747cafee71eae2db55c669ddce/plugins/renamerOnUpdate/renamerOnUpdate.py#L65
def callGraphQL(query, variables=None):
    # Session cookie for authentication
    graphql_port = FRAGMENT_SERVER['Port']
    graphql_scheme = FRAGMENT_SERVER['Scheme']
    graphql_cookies = {
        'session': FRAGMENT_SERVER.get('SessionCookie').get('Value')
    }
    graphql_headers = {
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Connection": "keep-alive",
        "DNT": "1"
    }
    if FRAGMENT_SERVER.get('Domain'):
        graphql_domain = FRAGMENT_SERVER['Domain']
    else:
        graphql_domain = 'localhost'
    # Stash GraphQL endpoint
    graphql_url = graphql_scheme + "://" + \
        graphql_domain + ":" + str(graphql_port) + "/graphql"

    json = {'query': query}
    if variables is not None:
        json['variables'] = variables
    response = requests.post(graphql_url, json=json,
                             headers=graphql_headers, cookies=graphql_cookies)
    if response.status_code == 200:
        result = response.json()
        if result.get("error"):
            for error in result["error"]["errors"]:
                raise Exception("GraphQL error: {}".format(error))
        if result.get("data"):
            return result.get("data")
    elif response.status_code == 401:
        sys.exit("HTTP Error 401, Unauthorised.")
    else:
        raise ConnectionError("GraphQL query failed:{} - {}. Query: {}. Variables: {}".format(
            response.status_code, response.content, query, variables))

def findScene(scene_id):
    query = """
    query FindScene($id: ID!, $checksum: String) {
        findScene(id: $id, checksum: $checksum) {
            ...SceneData
        }
    }
    fragment SceneData on Scene {
        id
        title
        url
        date
        details
        path
        studio {
            name
        }
        tags {
            name
        }
        performers {
            name
            url
            gender
            image_path
            tags {
                name
            }
        }
    }
    """
    variables = {
        "id": scene_id        
    }
    result = callGraphQL(query, variables)
    return result.get('findScene')

def writeFile(full_path, data):
    file_handle = open(full_path, "wb")
    file_handle.write(data)
    file_handle.close()



### Start Script ###

scene = findScene(FRAGMENT_SCENE_ID)

# get scene's directory path & filename as we will
# be saving XML alongside video with same name.
scene_path, ext = os.path.splitext(scene["path"])
filename = os.path.split(scene_path)[1]

root = minidom.Document()
xml = root.createElement('movie')
root.appendChild(xml);

title = root.createElement('title')
title.appendChild(root.createTextNode(scene['title']))
xml.appendChild(title)

sorttitle = root.createElement('sorttitle')
sorttitle.appendChild(root.createTextNode(scene['title']))
xml.appendChild(sorttitle)

if scene['date']:
    date = root.createElement('releasedate')
    date.appendChild(root.createTextNode(scene['date']))
    xml.appendChild(date)

if scene['studio']['name']:
    studio = root.createElement('studio')
    studio.appendChild(root.createTextNode(scene['studio']['name']))
    xml.appendChild(studio)

if scene['tags']:
    for tag in scene['tags']:
        genre = root.createElement('genre')
        genre.appendChild(root.createTextNode(tag['name']))
        xml.appendChild(genre)

if scene['performers']:
    for perf in scene['performers']:
        if perf['gender'] == 'FEMALE':
            collection = root.createElement('set')
            collection.appendChild(root.createTextNode(perf['name']))
            xml.appendChild(collection)


            # <actor>
            #   <name/>
            #   <thumb/>
            # </actor>
            actor = root.createElement('actor')
            name = root.createElement('name')
            thumb = root.createElement('thumb')

            name.appendChild(root.createTextNode(perf['name']))
            
            # StashApp will return image path of localhost. rebuild
            # the path using the LAN addy instead so we can access from
            # other local servers.
            port = str(FRAGMENT_SERVER['Port'])
            url_path = str(urlparse.urlparse(perf['image_path']).path)
            query = str(urlparse.urlparse(perf['image_path']).query)
            image_url = LAN_ADDRESS + ":" + port + url_path + "?" + query

            thumb.appendChild(root.createTextNode(image_url))

            actor.appendChild(name)
            actor.appendChild(thumb)

            xml.appendChild(actor)

            # all tags go on movie in plex, so attach any from performer as well
            if perf['tags']:
                for tag in perf['tags']:
                    genre = root.createElement('genre')
                    genre.appendChild(root.createTextNode(tag['name']))
                    xml.appendChild(genre)

# write XML file and exit
xml_str = root.toprettyxml(indent = "\t")

with open(scene_path + ".xml", "w") as f:
    f.write(xml_str)

printConsole(scene)
sys.exit()
