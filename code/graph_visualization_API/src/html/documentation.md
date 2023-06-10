# Introduction

## What is GraphAPI
GraphAPI is a high-level data visualization tool for complex graph structures. We provide a user interface for your website to display and manipulate any graph structure provided.
Check out the [Live Demo](/demo) for a full demonstration of the web-app. 

## Quick Start

### Using the Demo
The simplest way to start is to upload your own graph to the [Live Demo](/demo). This is a good way to test your graph data format to make sure it will display properly. See the [Data Format](Data Format) section for instructions on how to format your graph data.

Once you have created a correctly formatted data file, head over to the demo, click the three dots in the top left corner, click "Upload Graph", and select your file.

### Hosting your own graph
If you want to host the graph on your own website, you can instead send an HTTP request to `{{domain}}/create_graph` with your JSON graph data. The response will be raw HTML and JavaScript containing the GraphAPI web-app that you can embed within your website to display that graph.


### Full customization
If you want more detailed control over the features and functionality of the web-app through JavaScript, consider using the JS package. To do this, add the following script tag to the head of your webpage, then go to the [JacaScript API](JavaScript API) section for further instructions.

`<script src="{{domain}}/build/latest/js/graph.min.js"></script>`

<note>Warning</note> The above script tag will always request the latest version of GraphAPI, which may introduce breaking changes. If you want to avoid this, you can change the requested version by replacing "latest" in the above URL. For example, for version 0.0.1 use:
`<script src="{{domain}}/build/0.0.1/js/graph.min.js"></script>`


# Data Format
This section details the JSON structure required to submit data to GraphAPI.

<note>Note</note> In this section, "categorical" data properties refer to those whose values are all strings, and "continuous" data properties refer to those whose values are all numbers in JavaScript (int or floats).

The following is the basic skeleton, and the sections below will address each in detail.

```
{
    "graph": {
        "nodes": [],
        "edges": []
    }, 
    "config": {
        "maps": {}, 
        "filters": {}, 
        "settings": {}
    }
}
```

### graph.nodes
This is an array of node objects, each with the following structure:
`{"key": <string>, "attributes": {}}`

  - key: unique id for each node 
  - attributes: `{"label": <string>, "x": <float>, "y": <float>, "size": <float>, "color": <string>, "data": {}}`
    - label: visible node label in the graph
    - x/y: x and y position of the node in the graph
    - size: radius of the node
    - color: hex code to color the node
    - data: all custom key-value pairs assigned to the node
    
### graph.edges
This is an array of edge objects, each with the following structure:
`{"key": <string>, "source": <string>, "target", <string>, "attributes": {}}`

  - key: unique id for each node
  - source: unique id of the source node
  - target: unique id of the target node
  - attributes: `{"label": <string>, "size": <float>, "color": <string>, "data": {}}`
    - label: visible edge label in the graph
    - size: edge thickness
    - color: hex code to color the edge
    - data: all custom key-velue pairs assigned to the edge

    
### config.maps
*optional*

Within the maps object, define any of the following available property mappings:

node/edge color: `"node_color"` or `"edge_color"`

  - maps node/edge color to a node/edge categorical data property
  - syntax: `"<node|edge>_color": {"data": <string>, "map": {}}`
  - `data`: must be the name of a categorical node/edge custom data property (located in `attributes.data`)
  - `map`: Optional map of data category strings to their assigned color hex strings. If no map]() is given, mapping is done automatically. 

node/edge size: `"node_size"` or `"edge_size"`

  - maps node/edge size to a node/edge data property
  - syntax: `"<node|edge>_size": {"data": <string>, "min": <number>, "max": <number>, "map": {}}`
  - `data`: must be the name of a node/edge custom data property (located in `attributes.data`) or one of the following
      - "degree": number of edges connected to the node (not applicable to edges)
  - if the data property is continuous (i.e. values are numbers):
      - `min`: minimum possible size
      - `max`: maximum possible size
  - if the data property is categorical (i.e. values are strings):
      - `map`: map of data category strings to their assigned size value
      
node position: `"node_x"` or `"node_y"`

  - maps node X or Y position to a node data property
  - syntax: `"node_<x|y>": {"data": <string>, "min": <number>, "max": <number>, "map": {}}`
  - `data`: must be the name of a node data property (located in `attributes.data`) or one of the following
      - "degree": number of edges connected to the node (not applicable to edges)
  - if the data property is continuous (i.e. values are numbers):
      - `min`: minimum possible size
      - `max`: maximum possible size
  - if the data property is categorical (i.e. values are strings):
      - `map`: map of data category strings to their assigned size value
  - This map is incompatible with hierarchical clustering.

hierarchical clustering: `"cluster"`

  - syntax: `"cluster": [<string>, <string>, ...]` 
  - Structures the graph in a hierarchical manner according to the given list of node data properties. If the list is empty, the hierarchy will be ordered automatically.
  - This map is incompatible with node position mapping

hierarchy node/edge size: `"cluster_node_size"` or `"cluster_edge_size"`

  - Select a sizing method for hierarchy category nodes/edges.
  - By default, the graph acts as if, `type` is set to "max" as described below.
  - syntax: `cluster_<node|edge>_size: {"type": <string>, "min": <number>, "max": <number>}`
  - `type`:
      - "max": Maps the node/edge size to the maximum size of its sub-nodes/sub-edges (`min` and `max` size do not apply)
      - "avg": Maps the node/edge size to the average size of its sub-nodes/sub-edges (`min` and `max` size do not apply)
      - "count": Maps the node/edge size to the number of sub-nodes/sub-edges (must specify `min` and `max` sizes.)

### config.filters
*optional*

Filters create an interactive slider that the user can move to hide/show nodes and edges based on a data property you've defined.

Within the filters object, define custom names of filters with the following syntax:
`<name>: {"type": <string>, "data": <string>}`
  - `type`: "node", "edge", or "both". What to filter - nodes, edges, or both.
  - `data`: The data property to filter based on

### config.settings 
*optional*

Within the settings object, define any of the following:

Cluster Misc Category: `"cluster_misc": <"show" | "hide">`

- If present (and clustering is active), create a new category called MISC which contains all nodes that only have 1 category. Using "hide" will additionally remove those nodes from the graph.

Make Edge Filters Hide Nodes: `"edge_filteres_hide_nodes": <true | false>`

- Default false
- When true, if an edge filter would cause a node to have no visible edges, the node will be hidden as well.


## JSON Graph Examples

Provided are a few examples of properly formatted JSON data which can be submitted to Graph API.

Minimal example:

```
{
  "graph": {
    "nodes": [{"key": "node_1"}, {"key": "node_2"}, {"key": "node_3"}]
  }
}
```

Example with manual node/edge parameters: [graph_full_example.json](/documentation/example/graph_full_example.json)

Example with node/edge data mapping: [graph_mapping_example.json](/documentation/example/graph_mapping_example.json)

Blank Structure Template: [graph_blank_template.json](/documentation/example/graph_blank_template.json)



# JavaScript API
This section assumes you are requesting the full JS bundle from our servers within your webpage.
With the package included in your page, you will have access to the `Graph()` class constructor:

### The Graph() class
Constructor parameters:

`data`: This can be **either** a plain JS object containing your graph data or, a URL string where the JSON data can be retrieved.

`options`: An optional plain object containing the configuration options for the web-app. Details below.

Example:
`var graph = new Graph("https://my-website/data.json")`

#### Options
The following are available keywords that may be defined in the options object that is passed into the second argument of the constructor.

<table class="uk-table uk-table-divider">
<thead>
    <tr>
        <th>Keyword</th>
        <th>Type</th>
        <th>Default</th>
        <th>Description</th>
    </tr>
</thead>
<tbody>
    <tr>
        <td>container</td>
        <td>string</td>
        <td>"graphAPI-container"</td>
        <td>ID of the div you provide in which to insert the web-app</td>
    </tr>
    <tr>
        <td>ready</td>
        <td>function</td>
        <td>null</td>
        <td>Callback once the graph has finished initialization</td>
    </tr>
    <tr>
        <td>gravity</td>
        <td>number</td>
        <td>1</td>
        <td>Gravity strength of the physics simulation</td>
    </tr>
</tbody>
</table>

Example: `var graph = new Graph("https://my-website/data.json", {container: "my-container"})`

#### Methods

`tutorial(node_id)` 
Triggers the tutorial for the user interface on the currently loaded graph.
You may optionally provide a node ID to use for certain tutorial popups that require a node to be anchored to, but by default a random node will be selected.

`help()`
Opens the help menu.
