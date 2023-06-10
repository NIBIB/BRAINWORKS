import json

"""
Transform the original Les Mis data into an example for mapping node/edge color and size
"""

with open("../../external_test/static/original_data.json") as file:
    data = json.load(file)

map = {
    "Myriel": "major",
    "Napoleon": "minor",
    "MlleBaptistine": "minor",
    "MmeMagloire": "minor",
    "CountessDeLo": "minor",
    "Geborand": "minor",
    "Champtercier": "minor",
    "Cravatte": "minor",
    "Count": "minor",
    "OldMan": "minor",
    "Labarre": "minor",
    "Valjean": "hero",
    "Marguerite": "minor",
    "MmeDeR": "minor",
    "Isabeau": "minor",
    "Gervais": "minor",
    "Tholomyes": "minor",
    "Listolier": "minor",
    "Fameuil": "minor",
    "Blacheville": "minor",
    "Favourite": "minor",
    "Dahlia": "minor",
    "Zephine": "minor",
    "Fantine": "major",
    "MmeThenardier": "major",
    "Thenardier": "major",
    "Cosette": "major",
    "Javert": "major",
    "Fauchelevent": "minor",
    "Bamatabois": "minor",
    "Perpetue": "minor",
    "Simplice": "minor",
    "Scaufflaire": "minor",
    "Woman1": "minor",
    "Judge": "minor",
    "Champmathieu": "minor",
    "Brevet": "minor",
    "Chenildieu": "minor",
    "Cochepaille": "minor",
    "Pontmercy": "minor",
    "Boulatruelle": "minor",
    "Eponine": "major",
    "Anzelma": "minor",
    "Woman2": "minor",
    "MotherInnocent": "minor",
    "Gribier": "minor",
    "Jondrette": "minor",
    "MmeBurgon": "minor",
    "Gavroche": "major",
    "Gillenormand": "minor",
    "Magnon": "minor",
    "MlleGillenormand": "minor",
    "MmePontmercy": "minor",
    "MlleVaubois": "minor",
    "LtGillenormand": "minor",
    "Marius": "major",
    "BaronessT": "minor",
    "Mabeuf": "minor",
    "Enjolras": "abc members",
    "Combeferre": "abc members",
    "Prouvaire": "abc members",
    "Feuilly": "abc members",
    "Courfeyrac": "abc members",
    "Bahorel": "abc members",
    "Bossuet": "abc members",
    "Joly": "abc members",
    "Grantaire": "abc members",
    "MotherPlutarch": "minor",
    "Gueulemer": "minor",
    "Babet": "minor",
    "Claquesous": "minor",
    "Montparnasse": "minor",
    "Toussaint": "minor",
    "Child1": "minor",
    "Child2": "minor",
    "Brujon": "minor",
    "MmeHucheloup": "minor"
}

for node in data['nodes']:
    # remove all attributes
    del node['attributes']['size']
    del node['attributes']['x']
    del node['attributes']['y']
    del node['attributes']['color']

    # add 'role' data from the above map
    node["attributes"]["data"] = {
        'role': map[node['attributes']['label']]
    }

# add multiple edges between Valjean and Myriel
data['edges'].append({
  "key": "13_2",
  "source": "0.0",
  "target": "11.0",
  "attributes": {
    "size": 5
  }
})

for edge in data['edges']:
    # move edge size to the 'scenes' data
    edge['attributes']['data'] = {'scenes': edge['attributes']['size']}
    del edge['attributes']['size']

config = {
    'maps': {
        'node_size': {'data': 'degree', 'min': 10, 'max': 30},  # map size to degree
        'node_color': {'data': 'role', 'map': {'hero': '#FEF0D9', 'major': '#FCA072', 'abc members': '#E05837', 'minor': '#B30000'}},  # map color to role
        'edge_size': {'data': 'scenes', 'min': 1, 'max': 30},  # map size to scenes
    },
    'filters': {
        'Node Filter': {'type': 'node', 'data': 'degree'},  # filter node size/degree
        'Edge Filter': {'type': 'edge', 'data': 'scenes'}   # filter edge size/scenes
    },
    'settings': {
    }
}

data = {'graph': data, 'config': config}


with open("demo_data.json", "w+") as file:
    json.dump(data, file)
