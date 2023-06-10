const $ = require('jquery')
const graphology = require("graphology")
const sigma = require("sigma")
const Simulator = require("./physics_simulator.js")
const Interaction = require("./interaction.js")
const Structure = require("./structure.js")
const Interface = require("./interface.js")
const utils = require("./utils.js")

// Require all CSS
const nouislider_css = require("../../node_modules/nouislider/dist/nouislider.min.css")
const graph_css = require("../css/graph.css")
const help_css = require("../css/help.css")
const menu_css = require("../css/menu.css")
const tippy_css = require("../../node_modules/tippy.js/dist/tippy.css")
const tippy_scale_css = require("../../node_modules/tippy.js/animations/scale-extreme.css")
const bootstrap_css = require("../../node_modules/bootstrap/dist/css/bootstrap.min.css")

class Plot {
    // Manages graph state and interaction with all tools
    constructor($root, options) {
        this.key_prefix = "_"  // prepend each node/edge key with this to ensure no overlap with branches added after import

        // elements
        this.$root = $root  // container within which to limit all document modification and JS

        this.options = options

        // TODO put the stuff that's in the state right now just into this plot object, and call the plot object the state instead
        // global graph state object.
        // Holds instances of every module that controls the application.
        // This object is then passed into each module so they can all access each other's properties if need be.
        this.state = {}

        this.init()
    }

    // initialize all the components of the plot
    init() {
        this.graph = new graphology.MultiUndirectedGraph();  // graph object
        let sigma_container = this.$root.find("#sigma-container")[0];  // get div for sigma
        this.sigma = new sigma.Sigma(this.graph, sigma_container, {  // sigma renderer
            renderLabels: true,
            renderEdgeLabels: true,
            enableEdgeClickEvents: true,
            enableEdgeWheelEvents: true,
            enableEdgeHoverEvents: "debounce",
            zIndex: true,
            allowInvalidContainer: true  // silence error about invalid container width and height
            //nodeProgramClasses: {
                //image: getNodeProgramImage(),
                //border: NodeProgramBorder,
            //},
        });

        this.state = {
            $root: this.$root,
            plot: this,
            graph: this.graph,
            sigma: this.sigma,
            settings: this.options,
            structure: null,
            tree: null,
            interaction: null,
            interface: null,
            simulation: null
        }

        // UI
        this.interface = new Interface(this.state)

        // graph and canvas interactivity
        this.interaction = new Interaction(this.state)

        // Simulate physics
        this.simulator = new Simulator(this.state);

        // controls the data structure and property mapping
        this.structure = new Structure(this.state)

        // set node/edge render conditions based on state
        this.sigma.setSetting("nodeReducer", (node, attrs) => {  // return conditional node properties
            attrs = this.structure.node_reducer(node, attrs)  // first apply value-mapped rendering
            attrs = this.interaction.node_reducer(node, attrs)  // then interaction rendering
            attrs = this.interface.node_reducer(node, attrs)  // then UI settings
            return attrs;
        });

        this.sigma.setSetting("edgeReducer", (edge, attrs) => {  // return conditional edge properties
            attrs = this.structure.edge_reducer(edge, attrs)  // first apply value-mapped rendering
            attrs = this.interaction.edge_reducer(edge, attrs)  // then interaction rendering
            attrs = this.interface.edge_reducer(edge, attrs)  // then UI settings
            return attrs;
        });
    }

    // import JSON data with a graph and config options
    import(data) {
        // Replace the existing graph with a new one
        if (data == undefined || data.graph == undefined) {
            this.interaction.error("No graph data given.", "Could not find the graph in the JSON data provided. See documentation for proper JSON structure.")
            return
        }

        // sanitize graph JSON and save as original
        data = this.sanitize_graph(data)

        this.graph.clear()  // clear current graphology graph

        try {
            this.graph.import(data.graph)  // initialize new graphology graph
        } catch (error) {
            this.interface.error("Error importing graph", error)
            return
        }

        this.interaction.init_graph()
        this.simulator.init_graph()
        this.structure.init_graph()
        this.interface.init_graph()

        // Optional Config
        if (data.config == undefined) {
            console.log("No optional config found.")
        }
        this.structure.import_config(data.config)  // call this anyway because the tree still needs to get created.
    }
    update(data) {
        // Update the existing graph
        if (data == undefined || data.graph == undefined) {
            this.interaction.error("No graph data given.", "Could not find the graph in the JSON data provided. See documentation for proper JSON structure.")
            return
        }

        // add the given nodes and edges to the current graph JSON data
        let new_data = this.structure.original_graph_json
        new_data.graph.nodes.push(...data.graph.nodes)
        new_data.graph.edges.push(...data.graph.edges)

        // now sanitize the full graph JSON and save as original
        new_data = this.sanitize_graph(new_data)

        try {
            this.graph.import(new_data.graph, true)  // import to graphology with merge=true
        } catch (error) {
            this.interface.error("Error importing new data", error)
            return
        }

        this.structure.validate_graph()  // make sure it's in the proper format
        this.structure.update_config()  // update mappings and filter
    }

    // make sure the graph JSON is in the proper format for graphology and sigma
    sanitize_graph(data) {
        let node_keys = new Set()  // hash of node keys
        let nodes = []  // new array of nodes
        for (let node of data.graph.nodes) {
            if (!node.hasOwnProperty('key')) {
                console.warn("Ignoring node without a key")
                continue
            }
            if (node_keys.has(node.key)) {
                console.warn(`Ignoring duplicate node key: "${node.key}"`)
                continue
            }

            node_keys.add(node.key)
            nodes.push(node)
        }

        // remove edges connected to nodes that don't exist, or that don't have connections
        let edge_keys = new Set()  // hash of edge keys
        let edges = []  // new array of edges
        for (let edge of data.graph.edges) {
            if (!edge.hasOwnProperty('key')) {  // no key
                console.warn(`Ignoring edge without a key: ${JSON.stringify(edge)}`)
                continue
            }
            if (edge_keys.has(edge.key)) {
                console.warn(`Ignoring duplicate edge key: "${edge.key}"`)
                continue
            }
            if (!edge.hasOwnProperty('target')) {
                console.warn(`Edge with key "${edge.key}" has no target node. Ignoring it.`)
                continue
            }
            if (!edge.hasOwnProperty('source')) {
                console.warn(`Edge with key "${edge.key}" has no source node. Ignoring it.`)
                continue
            }
            if (!node_keys.has(edge.target)) {
                console.warn(`Edge with key "${edge.key}" has target node that does not exist (key "${edge.target}"). Ignoring it.`)
                continue
            }
            if (!node_keys.has(edge.source)) {
                console.warn(`Edge with key "${edge.key}" has source node that does not exist (key "${edge.source}"). Ignoring it.`)
                continue
            }

            edge_keys.add(edge.key)
            edges.push(edge)
        }

        data.graph.nodes = nodes
        data.graph.edges = edges

        // finally, save a deep clone of the sanitized data for later retrieval
        this.structure.original_graph_json = utils.deep_clone(data)
        // get the current host url to append to JSON
        let url = window.location.href
        let path = window.location.pathname
        url = url.substring(0, url.lastIndexOf(path)) + "/documentation"
        // this is to try and force the documentation element to the front by making it the first inserted key.
        // This may only work on browsers that sort by insertion order.
        let temp = {"DOCUMENTATION": "To view the documentation on the structure of this file, visit " + url}
        this.structure.original_graph_json = Object.assign(temp, this.structure.original_graph_json)

        // prepend all node/edge keys with a prefix to ensure no overlap with keys that I may add
        let graph = data.graph
        for (let node of graph.nodes) {
            node.attributes.key = node.key  // store the original key in the node attributes so the host has access to it
            node.key = this.key_prefix+node.key
        }
        for (let edge of graph.edges) {
            edge.attributes.key = edge.key
            edge.key = this.key_prefix+edge.key
            edge.undirected = true  // ensure undirected (because we are using a multi-undirected graph)
            edge.source = this.key_prefix+edge.source
            edge.target = this.key_prefix+edge.target
        }

        return data
    }
}

// public API
module.exports = class Graph {
    constructor(data, options) {
        this._root;
        this._plot;         // main plot object

        this.options = options

        // init when DOM ready
        $(document).ready(function() {
            this._init(data)
        }.bind(this));
    }

    _init(data) {
        this._$root = $("body")

        this._load_css(bootstrap_css)
        this._load_css(tippy_css)
        this._load_css(tippy_scale_css)
        this._load_css(nouislider_css)
        this._load_css(graph_css)
        this._load_css(help_css)
        this._load_css(menu_css)


        console.assert(this._$root.height() > 0, "Graph Container must have a defined height and width. Currently:", this._$root.height(), this._$root.width())

        // load all HTML then initialize the plot object
        this._load_html()
        .then(() => {
            this._plot = new Plot(this._$root, this.options)
        })
        .then(() => {
            return this._load_data(data)  // load/fetch data form external source
        })
        .then((data) => {
            this._plot.import(data)
            this.options.ready()  // call the host's ready method
        })
    }

    // initialize all html necessary for the Plot
    _load_html() {
        return new Promise(resolve => {
            // load main html page into the container
            let html_url = "src/html/graph.html"
            this._$root.load(html_url, (responseText, textStatus, req) => {
                if (req.status !== 200) {
                    console.error(`Failed to load graph API HTML from "${html_url}". Status code: ${req.status}`)
                } else {
                    resolve()
                }
            });
        })
    }

    // request all css and load into shadow DOM
    _load_css(css) {
        $("<style>"+css+"</style>").appendTo($('head'))
    }

    // Either load a plain object or request if from a URL
    _load_data(data) {
        // If data is a plain object, return a deep clone of it.
        // If data is a URL, return the data from the response from that URL.
        return new Promise(resolve => {
            if (utils.is_plain_object(data)) {  // test if it's a plain object.
                // this is a fix for a weird problem that occurs when object are passed through the iframe boundary.
                // See https://github.com/graphology/graphology/issues/149
                // and http://perfectionkills.com/instanceof-considered-harmful-or-how-to-write-a-robust-isarray/
                // Note that my utils.is_plain_object() is the correct implementation, but the "standard" is used everywhere so I still have to get around it.
                // This solution just creates an entirely new copy of the object, bypassing the issue altogether.
                data = utils.deep_clone(data)
                resolve(data)
            } else if (typeof data == 'string') {  // if string, expecting data url
                console.log("Requesting graph data from:", data)
                $.ajax({url: data,
                    success: (response) => {  // successful response
                        if (utils.is_plain_object(response)) {
                            resolve(response)
                        } else {
                            this._plot.interface.error("Failed to request graph data.", `The request to "${data}" did not respond with a plain object.`)
                        }
                    },
                    error: (data) => {  // display error on fail
                        this._plot.interface.error("Failed to request graph data.", `The request to "${data}" responded with: <p>${data.status}: ${data.statusText}</p>`)
                    }
                });
            } else {  // something else
                this._plot.interface.error("Unexpected type for data argument.", "Data argument must be either an plain Object containing the graph data or the URL string at which to request it. Instead got: " + typeof data)
            }
        })
    }

    // Modify the Graph
    add(data) {
        // data should be {nodes: [], edges: []} in the same format as the original data.
        // Adds the given nodes and edges to the graph
        this._load_data(data).then(data => this._plot.update({graph: data}))
    }

    // Get node/edge information
    node(id) {
        // get node by id
        return this._plot.structure.get_node_attributes(id)
    }
    edge(id) {
        // get edge by id
        return this._plot.structure.get_edge_attributes(id)
    }
    extremities(id) {
        // get source and target node IDs of a given edge
        return this._plot.structure.get_edge_extremities(id)
    }
    edges(id) {
        // get a list of all edges attached to the given node
        return this._plot.structure.get_node_edges(id)
    }
    node_children(id) {
        // get all IDs of the children of the given node
        return this._plot.state.tree.get_node_children(id)
    }
    edge_children(id) {
        // get all IDs of the children of the given edge
        return this._plot.state.tree.get_edge_children(id)
    }
    node_parent(id) {
        // get ID of the parent node
        return this._plot.state.tree.get_node_parent(id)
    }
    node_parent(id) {
        // get ID of the parent edge
        return this._plot.state.tree.get_edge_parent(id)
    }

    // trigger events
    tutorial() {
        this._plot.interface.tutorial()
    }
    help() {
        this._plot.interface.help.toggle()
    }

    // Display the center popup modal with the given html
    center_display(title, body, footer, size, callback) {
        this._plot.interface.custom_modal.show(title, body, footer, size, callback)
    }

    // set content for the custom popup
    popup_display(callback, label, height, width) {
        this._plot.interface.custom_popup.set_content(callback, label, height, width)
    }

    // set callback for node/edge data displays
    node_display(callback, height, width) {
        this._plot.interface.data_display.set_node_display(callback, height, width)
    }
    edge_display(callback, height, width) {
        this._plot.interface.data_display.set_edge_display(callback, height, width)
    }

    // add items to the node/edge right-click menu
    // callback will be passed the data for the node/edge
    add_node_menu_item(name, description, callback) {
        this._plot.interface.right_click_menu.add_node_item(name, description, callback)
    }
    add_edge_menu_item(name, description, callback) {
        this._plot.interface.right_click_menu.add_edge_item(name, description, callback)
    }

    // trigger the alert modal
    error(title, message) {
        this._plot.interface.error(title, message)
    }
    warning(title, message) {
        this._plot.interface.warning(title, message)
    }
}
