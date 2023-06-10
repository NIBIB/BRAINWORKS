const $ = require('jquery')
const Animate = require("sigma/utils/animate.js")
const metrics = require("graphology-metrics")
const noUiSlider = require("nouislider")

const Tool = require("./tool.js")
const utils = require("./utils.js")

// TODO: Currently doesn't support nested data keys beyond the initial attributes["data"].
//  - This means that the data object cannot have any nests, which isn't a huge problem at the moment,
//    but I can imagine it might be needed later down the road.
//  - In order to implement this, the methods that assign a mapping need to be able to specify data keys within nested keys,
//    and I haven't decided how that's going to work.
//  - Should it be syntactical like a directory structure? e.g. mapper.node_size('property1/subprop4/subsub2',0,1)
//  - Should it be like a list instead? e.g. mapper.node_size(['property1','subprop4','subsbu2'],0,1)
//  - Or should it be explicitly related to JSON? e.g. mapper.node_size({'property1': {'subprop4': 'subsub2'}},0,1)
//  - Also, the validate_graph() method will need to ensure that all nodes have the same data tree, even if nests have
//    all null values. Currently doesn't do this.
//  - However, I did implement full recursive traversal for the InteractiveTool when displaying node properties in
//    the right-click menu, so theres that. yay.

// NOTE: This class adds a global "degree" attribute to each node, which can be used as a node property for mapping purposes.
// TODO: If we ever implement dynamic adding of nodes/edges, make sure to update the node degree attribute: this.graph.setNodeAttribute(node, 'degree', this.graph.degree(node))

// NOTE: when referring to "attributes", these are any key-value pairs, including the built-ins used by sigma.
//      "data" refers to the "data" attribute, a nested object with custom assigned key-value pairs.


// constants
const CATEGORICAL = 'cat'
const CONTINUOUS = 'cont'
const FILTER = 'filter'
const NODE = 'node'
const EDGE = 'edge'
const BOTH = 'both'

// HTML element class that all added tags receive so they can be removed all at once
const MAPPER = 'added_mapper_element'

// node expansion/collapse animation time
const TREE_ANIMATE_DURATION = 500

module.exports = class Structure extends Tool {
    // provides methods for mapping node/edge data to visual graph dimensions
    constructor(state) {
        super(state)

        // Fully JSON representation of the original graph (before modifications made due to clustering, etc)
        this.original_graph_json;
        this.original_config_json;

        // index of all data properties and whether they are categorical or continuous
        this.data = {[NODE]: {}, [EDGE]: {}}

        // index of applied maps and their settings
        // key: map name (same as class method name)
        // value: {data: <string>, args: []}
        this.maps = {}
        this.map_methods = ['node_size', 'node_color', 'node_x', 'node_y', 'edge_size', 'edge_color', 'cluster', 'cluster_node_size', 'cluster_edge_size']

        // index of filter filters {<filter_name>: {node:<bool>, edge:<bool>, data:<data_key>, format:<string>, min: <current_min>, max: <current_max>, abs_min: <min>, abs_max:<max>}}
        this.filters = {}
        this.filter_types = ['node', 'edge', 'both']

        // elements
        this.$filters = this.$root.find("#filters")

        this.state.structure = this
        this.init();
    }

    init() {
    }

    init_graph() {
        // Initialize a new graph
        this.clear_mappings()  // clear all current mappings
        this.validate_graph()  // make sure it's in the proper format
        // write a function to check only a single node/edge, then call those in validate_graph.
        this.state.tree = new Tree(this.state, this)  // initialize tree

    }
    validate_graph() {
        // Ensures that all nodes all have the same set of data keys, and all edges have the same set of data keys.
        // If a node/edge is missing a certain data key, assign null
        // Ensure that all nodes have an accurate "degree" data key
        // Checks whether each data key has continuous or categorical data.
        //    - If any values in a key are not numerical, the whole set is categorical.

        // loop through all nodes to collect full set of data keys and check type
        this.graph.forEachNode((node, attributes) => {
            if (!attributes["data"]) return;  // if no data attribute, ignore
            for (let [key, val] of Object.entries(attributes["data"])) {
                let types = this.data[NODE]
                if (typeof val !== "number") {  // if any value is not a number, this data key is categorical
                    types[key] = CATEGORICAL
                } else if (this.data[NODE][key] === undefined) {  // if a number AND not checked yet, its continuous
                    types[key] = CONTINUOUS
                }
            }
        });

        // loop through all edges to collect full set of data keys
        this.graph.forEachEdge((edge, attributes) => {
            if (!attributes["data"]) return;  // if no data attribute, ignore
            for (let [key, val] of Object.entries(attributes["data"])) {
                let types = this.data[EDGE]
                if (typeof val !== "number") {  // if any value is not a number, this data key is categorical
                    types[key] = CATEGORICAL
                } else if (types[key] === undefined) {  // if a number AND not checked yet, its continuous
                    types[key] = CONTINUOUS
                }
            }
        });

        // make sure all nodes have all node data keys
        this.graph.updateEachNodeAttributes((node, attributes) => {
            var data = attributes["data"] || {}
            Object.keys(this.data[NODE]).forEach((key) => {
                if (!data.hasOwnProperty(key)) {
                    data[key] = null
                }
            })
            attributes["data"] = data  // set new data
            return attributes;
        });

        // make sure all edges have all edge data keys
        this.graph.updateEachEdgeAttributes((edge, attributes) => {
            var data = attributes["data"] || {}
            Object.keys(this.data[EDGE]).forEach((key) => {  // for each key, make sure this node has it
                if (!data.hasOwnProperty(key)) {
                  data[key] = null;  // assign null to new data key
                }
            })
            attributes["data"] = data  // set new data
            return attributes;
        });

        // set data values that aren't set manually.
        this.add_default_data()
    }
    add_default_data() {
        // Adds/updates attributes values to each node/edge that do not have to be manually set.
        // Don't forget to add it to this.data[NODE] or this.data[EDGE] if it is a data value

        this.data[NODE]["degree"] = CONTINUOUS
        this.data[NODE]["eccentricity"] = CONTINUOUS
        this.data[NODE]["betweenness_centrality"] = CONTINUOUS
        this.data[NODE]["closeness_centrality"] = CONTINUOUS
        this.data[NODE]["degree_centrality"] = CONTINUOUS
        this.data[EDGE]["simmelian_strength"] = CONTINUOUS

        let betweenness_cents = metrics.centrality.betweenness(this.graph, {getEdgeWeight: null});
        let closeness_cents = metrics.centrality.closeness(this.graph);
        let degree_cents = metrics.centrality.degree(this.graph);
        // let eigenvector_cents = metrics.centrality.eigenvector(this.graph, {getEdgeWeight: null});  // sometimes fails to converge

        this.graph.forEachNode((node, attributes) => {
            this.graph.setNodeAttribute(node, "depth", 0)  // tree depth
            if (!this.graph.hasNodeAttribute(node, "filters")) {
                this.graph.setNodeAttribute(node, "filters", {})  // set filters if not already
            }

            // statistics
            this.set_node_data(node, "degree", this.graph.degree(node))
            this.set_node_data(node, "eccentricity", metrics.node.eccentricity(this.graph, node))
            this.set_node_data(node, "betweenness_centrality", betweenness_cents[node])
            this.set_node_data(node, "closeness_centrality", closeness_cents[node])
            this.set_node_data(node, "degree_centrality", degree_cents[node])
        });

        let strengths = metrics.edge.simmelianStrength(this.graph);

        this.graph.forEachEdge((edge, attrs) => {
            if (!this.graph.hasEdgeAttribute(edge, "filters")) {
                this.graph.setEdgeAttribute(edge, "filters", {})  // set filters if not already
            }

            // statistics
            this.set_edge_data(edge, "simmelian_strength", strengths[edge])
        })

        // if node doesn't have coords, assign random.
        // If no size, assign default.
        // If no color, assign default.

        this.graph.updateEachNodeAttributes((node, attr) => {
            attr.x = (attr.x !== undefined) ? attr.x : (Math.random()-0.5)*100
            attr.y = (attr.y !== undefined) ? attr.y : (Math.random()-0.5)*100
            //attr.zIndex = 1
            attr.size = (attr.size !== undefined) ? attr.size : 10
            attr.color = (attr.color !== undefined) ? attr.color : "#C0C0C0"
            return attr;
        });

        this.graph.updateEachEdgeAttributes((edge, attr) => {
            attr.color = (attr.color !== undefined) ? attr.color : "#C0C0C0"
            attr.size = (attr.size !== undefined) ? attr.size : 5
            return attr;
        });
    }

    // Construct HTML to display all attributes of a node/edge
    generate_data_html($parent_element, attributes) {
        // recursively generate html for the object structure, given a parent jQuery element
        let $element = $(`<div class='menu-section'></div>`).css("margin-left", "1em")
        let objects = {}  // objects to be recursively displayed

        // if attributes exist
        if (attributes !== undefined && Object.keys(attributes).length > 0) {
            for (let [key, val] of Object.entries(attributes)) {  // for each attribute
                if (val === null && !this.settings["advanced_data"]) {  // don't display null if not advanced menu
                    continue;
                } else if (typeof val === 'object' && val !== null) {  // if an object, store for later
                    objects[key] = val
                } else {  // display normally
                    $(`<div><span>${key}: </span><span>${val}</span></div>`).appendTo($element)
                }
            }
            // now display the object (after all normal properties)
            for (let [key, val] of Object.entries(objects)) {
                $(`<div><span>${key}: </span></div>`).appendTo($element)
                this.generate_data_html($element, val)  // generate sub object html recursively
            }
        } else {  // no attributes
            $("<div><span>No data</span></div>").appendTo($element).css({'font-style': 'italic', 'color':'grey'})
        }
        // add this element to its parent
        $element.appendTo($parent_element)
    }

    // Given a node/edge attributes object, get a specific custom data key
    get_data(attributes, key=null) {
        // If key is not given, return all data keys
        if (key === null)
            return attributes["data"]
        return attributes["data"][key]
    }
    // given a node/edge, set a specific custom data key and value
    set_node_data(node, key, value) {
        let data = this.graph.getNodeAttribute(node, "data")
        data[key] = value
        this.graph.setNodeAttribute(node, "data", data)
    }
    set_edge_data(edge, key, value) {
        let data = this.graph.getEdgeAttribute(edge, "data")
        data[key] = value
        this.graph.setEdgeAttribute(edge, "data", data)
    }

    // get node/edge attributes
    get_node_attributes(node) {
        return this.graph.getNodeAttributes(node)
    }
    get_edge_attributes(edge) {
        return this.graph.getEdgeAttributes(edge)
    }
    get_node_edge(node) {
        return this.graph.edges(node)
    }
    get_edge_extremities(edge) {
        return this.graph.extremities(edge)
    }

    // Given a node/edge attributes object, get a specific filter value
    get_filter(attributes, key=null) {
        // If key is not given, return all filter keys
        if (!attributes.filters) return {}
        if (key === null)
            return attributes.filters
        return attributes.filters[key]

    }
    // given a node/edge and filter name, set that node/edge filters value
    set_node_filter(node, key, value) {
        // given a node, set a filter value
        let data = this.graph.getNodeAttribute(node, "filters")
        if (data !== undefined) {
            data[key] = value
        } else {
            data = {[key]: value}
        }
        this.graph.setNodeAttribute(node, "filters", data)
    }
    set_edge_filter(edge, key, value) {
        // given a edge, set a filters value
        let data = this.graph.getEdgeAttribute(edge, "filters")
        data[key] = value
        this.graph.setEdgeAttribute(edge, "filters", data)
    }

    // given whether 'node' or 'edge' data, return the type of the given data key
    get_data_type(element_type, key) {
        if (element_type !== NODE && element_type !== EDGE) {
            throw Error(`Specify node or edge for the data to retrieve. Got "${element_type}"`)
        }
        if (this.data[element_type][key] === undefined) {
            console.error(`No ${element_type==NODE?"nodes":"edges"} have the data key "${key}"`)
            return false
        }
        return this.data[element_type][key]
    }
    // finds the statistics for a specific data key across the given nodes/edges
    data_statistics(type, key, elements=[]) {
        /*
        If categorical:
            - stats.total: total number
            - stats.frequency: frequency map of categories
            - stats.categories: array of categories
        If continuous:
            - stats.min: minimum value
            - stats.max: maximum value
        */
        if (elements.length == 0) {  // if elements not specified, use whole graph
            elements = (type == NODE) ? this.graph.nodes() : this.graph.edges()
        }
        let getAttributes = (type == NODE) ? node => this.graph.getNodeAttributes(node) : edge => this.graph.getEdgeAttributes(edge)
        let stats = {}
        if (this.data[type][key] === CONTINUOUS) {  // continuous data
            for (let elem of elements) {
                let attr = getAttributes(elem)
                let value = this.get_data(attr, key)  // get value for this data key
                if (value != undefined) {
                    if (stats.min === undefined || value < stats.min)
                        stats.min = value;
                    if (stats.max === undefined || value > stats.max)
                        stats.max = value;
                }
            }
        } else {  // categorical data
            stats.frequency = {}  // maps categories to their frequency
            for (let elem of elements) {
                let attr = getAttributes(elem)
                let value = this.get_data(attr, key)  // get value for this data key
                if (value != undefined) {
                    stats.frequency[value] = stats.frequency[value] === undefined ? 1 : stats.frequency[value]+1
                }
            }

            // also just a sorted list of all the categories
            stats.categories = Array.from(Object.keys(stats.frequency)).sort()

            // total number of elements
            stats.total = 0
            for (let [cat,num] of Object.entries(stats.frequency)) {
                stats.total += num
            }
        }

        return stats
    }

    // reducers for rendering temporary states
    node_reducer(node, attrs) {
        // hide node if not visible in the tree
        if (this.is_out_of_tree(attrs)) {
            this.hide(attrs)
            //this.obscure(attrs)
        }

        // put nodes out of range based on filter setting
        for (let [name, filter] of Object.entries(this.filters)) {  // for each filter
            if (!filter[NODE]) continue;  // filter not mapped to nodes
            if (!this.is_tree_node(node)) {  // regular node
                if (this.get_filter(attrs, name) == undefined || this.get_filter(attrs, name) < filter.min || this.get_filter(attrs, name) > filter.max) {
                    this.out_of_range(attrs)  // if this node's mapped filter value is outside the filter range (or undefined), it's out of range
                }
            } else {  // tree branches have a min and max value
                if (this.get_filter(attrs, name) == undefined || this.get_filter(attrs, name).max < filter.min || this.get_filter(attrs, name).min > filter.max) {
                    this.out_of_range(attrs)  // if this tree node's min and max filter values are outside the filter range (or undefined), it's out of range
                }
            }
        }

        // put nodes out of range if connected to all out-of-range edges
        if (this.state.settings.edge_filters_hide_nodes) {
            let any_in_range_edge = this.graph.findEdge(node, (edge) => {
                return !this.is_edge_out_of_range(edge)
            })
            // if no in-range edges are found, hide the node
            if (any_in_range_edge === undefined) this.out_of_range(attrs)
        }

        // if this node's size or color is undefined, it's out of range
        if (attrs.color == undefined || attrs.size == undefined) {
            this.out_of_range(attrs)
        }

        if (this.is_out_of_range(attrs)) {
            if (this.settings.show_out_of_range_nodes) {
                this.obscure(attrs)
            } else {
                this.hide(attrs)
            }
        }

        return attrs;
    }
    edge_reducer(edge, attrs) {  // return temporary edge properties
        let nodes = this.graph.extremities(edge)  // source and target nodes

        // hide edges based on filter settings
        for (let [name, filter] of Object.entries(this.filters)) {  // for each filter
            if (!filter[EDGE]) continue;
            if (!this.is_tree_edge(edge)) {
                if (this.get_filter(attrs, name) == undefined || this.get_filter(attrs, name) < filter.min || this.get_filter(attrs, name) > filter.max) {
                    this.out_of_range(attrs)  // if this edge's mapped filter value is outside the filter range, or is undefined, hide it
                }
            } else {  // tree edges have a min and max value
                if (this.get_filter(attrs, name) == undefined || this.get_filter(attrs, name).max < filter.min || this.get_filter(attrs, name).min > filter.max) {
                    this.out_of_range(attrs)  // if this tree edge's min and max filter values are outside the filter range (or undefined), hide it.
                }
            }
        }
        // if this edge is connected to an obscured node, hide it
        if (this.is_node_obscured(nodes[0]) || this.is_node_obscured(nodes[1])) {
            this.hide(attrs)
        }

        if (this.is_out_of_range(attrs)) {
            if (this.settings.show_out_of_range_edges) {
                this.obscure(attrs)
            } else {
                this.hide(attrs)
            }
        }

        return attrs;
    }

    //
    // maps
    //

    linear_map(val, input_min, input_max, output_min, output_max) {
        // map a value linearly between input and output, given two points
        if (val == undefined) return undefined;
        if (input_min == input_max) return (output_max+output_min)/2  // undefined slope
        let slope = (output_max - output_min) / (input_max - input_min)
        return slope * (val - input_min) + output_min
    }

    generate_categorical_color_map(type, data) {
        // type is NODE or EDGE
        // data is the data attribute to generate a color map for
        if (this.data[type][data] !== CATEGORICAL) {
            throw "Data property must be categorical in order to generate a color map"
        }

        let stats = this.data_statistics(type, data)

        // only color categories with more than 1 node
        var categories = []
        for (let category of stats.categories) {
            if (stats.frequency[category] > 1) {
                categories.push(category)
            }
        }

        let colors = utils.color_array(categories.length)
        let map = {}
        for (let i=0; i<colors.length; i++) {
            let category = categories[i]
            map[category] = colors[i]
        }
        return map
    }


    //
    // General mapping methods
    //

    // mapping data keys to various types of dimensions
    map_dimension(element_type, key, dimension, dimension_type, map) {
        // element_type is either NODE or EDGE
        // key is the data key to map
        // dimension is the dimension to map to
        // dimension_type is CONTINUOUS, CATEGORICAL, or FILTER
        // map is the appropriate mapping from key to dimension
        let data_type = this.get_data_type(element_type, key)  // data key type. CATEGORICAL or CONTINUOUS
        if (!data_type) return;  // this data key doesn't exist anywhere - don't apply any mappings
        let stats = null;

        // retrieve statistics on the given data key
        stats = this.data_statistics(element_type, key)

        // get either node or edge iterator
        let updateIterator = element_type == NODE ? node => this.graph.updateEachNodeAttributes(node) : edge => this.graph.updateEachEdgeAttributes(edge)

        // continuous to continuous mapping
        if (data_type == CONTINUOUS && dimension_type == CONTINUOUS) {
            this.continuous_to_continuous(updateIterator, key, dimension, stats, map)
        }
        // continuous to categorical mapping
        if (data_type == CONTINUOUS && dimension_type == CATEGORICAL) {
            console.error("Continuous to Categorical mapping not yet implemented")
        }
        // categorical to continuous and categorical to categorical (same)
        if (data_type == CATEGORICAL && (dimension_type == CATEGORICAL || dimension_type == CONTINUOUS)) {
            this.categorical_to_categorical(updateIterator, key, dimension, map)
        }

        // filters
        if (dimension_type === FILTER) {
            this.to_filter(element_type, data_type, key, dimension, stats)
        }
    }

    map_dimension_function(element_type, key, dimension, map) {
        // element_type is either NODE or EDGE
        // key is the data key to map
        // dimension is the dimension (node/edge property) to map to
        // map is a function that accepts a data value and returns the desired dimension value
        let data_type = this.get_data_type(element_type, key)  // data key type
        let updateIterator = element_type == NODE ? node => this.graph.updateEachNodeAttributes(node) : edge => this.graph.updateEachEdgeAttributes(edge)
        updateIterator((elem, attr) => {
            let value = this.get_data(attr, key)  // get data value of this key on this node/edge
            let mapped = map(value)
            if (mapped) attr[dimension] = mapped  // set mapped dimension value
            return attr;
        });
    }

    // remove all mappings and html elements
    clear_mappings() {
        this.data = {[NODE]: {}, [EDGE]:{}}
        this.maps = {}
        this.filters = {}

        // all added DOM elements for mapping have the MAPPER class
        this.$root.find(`.${MAPPER}`).remove()

        // hide tree buttons
        this.$root.find("div#tree").hide()
    }

    // specific element mapping functions
    continuous_to_continuous(updateIterator, key, dimension, stats, map) {
        // get a node/edge iterator, map this data key to this dimension
        updateIterator((elem, attr) => {
            let value = this.get_data(attr, key)  // get data value of this key
            attr[dimension] = this.linear_map(value, stats.min, stats.max, map.min, map.max)
            return attr;
        });
    }
    continuous_to_categorical(updateIterator, key, dimension, map) {
        // map a continuous data value with a categorical dimension
        // map [object]:
        //  - keys: DATA VALUE WHERE THE CATEGORY STARTS
        //  - values: DIMENSION CATEGORY

        // TODO: what to use as map input? Can't use object because object keys cannot be numbers.
        // maybe take in the same map as categorical_to_continuous - a map of dimension categories to data values.
        // Then automatically calculate uniform ranges to assign? greater than, less than, middle, etc.
        //  A Map object can associate numbers with values. maybe that?
        //   Maybe require a function to be input as a map? takes in a number and outputs a category

        updateIterator((node, attr) => {
            let value = this.get_data(attr, key)  // data value of this node
            // TODO: find which dimension category this value should be mapped to

            attr[dimension]
            return attr;
        });
    }
    categorical_to_categorical(updateIterator, key, dimension, map) {
        // map a categorical data key to a continuous dimension
        // map [Object]:
        //  - keys: DATA CATEGORY VALUE (strings)
        //  - values: DIMENSION VALUE (numbers)
        // If a data value is not given in the mapping, the value will be undefined
        updateIterator((node, attr) => {
            let value = this.get_data(attr, key)  // get data value of this key
            if (map[value] !== undefined) {
                attr[dimension] = map[value]  // get mapped dimension value
            }
            return attr;
        });
    }

    to_filter(element_type, data_type, key, filter_name, stats) {
        // iterate over either nodes or edges
        let elementIterator = element_type == NODE ? func => this.graph.forEachNode(func) : func => this.graph.forEachEdge(func)
        let setElementSlider = element_type == NODE ? (...args) => this.set_node_filter(...args) : (...args) => this.set_edge_filter(...args)

        // continuous to filter mapping
        if (data_type == CONTINUOUS) {
            this.continuous_to_filter(elementIterator, setElementSlider, key, filter_name, stats)
        }
        // continuous to filter mapping
        if (data_type == CATEGORICAL) {
            this.categorical_to_filter(elementIterator, setElementSlider, key, filter_name, stats)
        }

    }
    continuous_to_filter(elementIterator, setElementSlider, key, filter_name, stats) {
        elementIterator((node, attr) => {
            let filter_value = this.get_data(attr, key)  // get data value of this key
            setElementSlider(node, filter_name, filter_value)  // set element filter value
        });

        let filter = this.filters[filter_name]
        let min = stats.min
        let max = stats.max

        // if the absolute minimum has already been set, that means another filter already exists
        if (filter.abs_min === undefined) {  // no filter already exists
            filter.abs_min = min  // set absolute min and max
            filter.abs_max = max
        } else {  // a filter has already been created
            // update absolute min and max instead
            filter.abs_min = filter.abs_min < min ? filter.abs_min : min
            filter.abs_max = filter.abs_max > max ? filter.abs_max : max
        }
        this.add_continuous_filter(filter_name, filter.abs_min, filter.abs_max)  // create new filter
    }
    categorical_to_filter(elementIterator, setElementSlider, key, filter_name, stats) {
        // will automatically collect all data categories and assign filter positions
        let map = {}  // map categories to a filter value
        for (var i=0; i<stats.categories.length; i++) {
            map[stats.categories[i]] = i
        }
        elementIterator((node, attr) => {
            let data_value = this.get_data(attr, key)  // get data value of this key
            let filter_value = map[data_value]
            setElementSlider(node, filter_name, filter_value)  // set dimension value
        });
        // mapping filter values to data categories
        let reverse_map = new Map(Object.entries(map).map(entry => entry.reverse()))
        this.add_categorical_filter(filter_name, reverse_map)
    }

    // Filter filters with noUiSlider
    add_continuous_filter(name, min, max) {
        var decimals = 1  // number of decimal places to show
        if (max - min > 0) {
            decimals = utils.decimals(max-min)  // scale number of decimals to display based on range
        } else {  // if max not greater than min
            console.error(`Failed to implement filter "${name}". Minimum and Maximum values are the same (the only data value present is: ${min}). This filter will not be shown.`)
            return
        }

        // pad min and max so values don't get rounded out of range
        let range_pad = Math.pow(0.1, decimals)
        max = max + range_pad
        min = (min >= 0 && min-range_pad < 0) ? 0 : min - range_pad  // ensure min doesn't go below zero if it isn't already
        decimals = utils.decimals(max-min)  // update precision to include the padding

        // default formatter function
        let format_func = function(value) {
            return value.toFixed(decimals).toString()  // round values
        }

        let format = this.filters[name]['format']
        if (format == 'date') {
            format_func = function(value) {  // data assumed to be unix time in SECONDS

                let now = new Date(value*1000)
                let year = now.getUTCFullYear()
                let month = now.getUTCMonth()
                let day = now.getUTCDate()
                return `${month}/${day}/${year}`
            }
        }

        let filter = this.create_filter_html(name)
        noUiSlider.create(filter, {
            start: [min, max],  // starting positions of handles
            range: {'min': min, 'max': max},
            connect: [false, true, false],  // whether to fill in areas between handles
            behaviour: 'drag',  // allow dragging area between handles
            format: {
                to: String,  // function returning formatted value
                from: Number  // function returning float
            },
            tooltips: {  // also visually controlled with css .noUi-tooltip
                to: format_func  // handle tooltips
            },
            pips: {  // tick marks
                mode: 'count',
                values: 5,  // number of pip major ticks
                density: 5,  // 1 minor tick every 5 percent
                format: {
                    to: format_func  // pip values
                }
            }
        });

        filter.noUiSlider.on("update", (values, handle) => {  // bind the filter update event
            this.filter_slider_event(name, values[0], values[1])  // pass in name, min val, and max val
        })
    }
    add_categorical_filter(name, map) {
        // adds a filter element to the page
        // map must be a map that maps filter values to categories
        let filter = this.create_filter_html(name)

        let keys = Array.from(map.keys())  // array of numerical keys
        let min = Math.min(...keys)  // minimum
        let max = Math.max(...keys)  // maximum

        // values of the string format "10%", "42.69%", etc.
        // also must have a "min" and "max" value.
        var percents = {}

        // how to show the pips below the sliders
        var pips = {}

        if (Object.keys(keys).length == 1) {  // there's only 1 category
            filter.setAttribute('disabled', true);  // disable the slider
            percents = {'min':-1, '50%':0, 'max':1}
            pips = {
                mode: 'steps',
                filter: (value, type) => {  // only show the one value that's there
                    if (value !== 0) return -1;  // don't show
                    return 1;  // show large
                },
                density: 100,  //  only tick exactly at each range step
                format: {  // convert numerical value to category string
                    to: (value) => map.get(value)
                }
            }
        } else {
            for (let i=0; i<keys.length; i++) {
                let p;
                if (i==0) p="min";
                else if (i==keys.length-1) p="max";
                else p=`${100*keys[i]/max}%`;
                percents[p] = keys[i]
            }
            pips = {  // tick marks
                mode: 'range',
                density: 100,  //  only tick exactly at each range step
                format: {  // convert numerical value to category string
                    to: (value) => map.get(value)
                }
            }
        }

        noUiSlider.create(filter, {
            start: [min],  // starting positions of handles
            range: percents,
            tooltips: false,  // also visually controlled with css .noUi-tooltip
            snap: true,  // snap handle to range values
            pips: pips
        });

        filter.noUiSlider.on("update", (values, handle) => {  // bind the filter update event
            this.filter_slider_event(name, values[0], values[0])  // min and max value are the same for one filter
        })
    }
    create_filter_html(name) {
        // adds a slider element to the page
        let id = name.replaceAll(' ', '')
        let old_div = this.$root.find(`div.filter_container#${id}`)
        if (old_div[0]) {  // if a filter div for this ID already exists
            old_div.remove()  // remove it
        }
        let $filter_div = $(`<div class="filter_container ${MAPPER}" id="${id}"><span>${name}:</span></div>`).appendTo(this.$filters)
        let $slider = $(`<div class="slider"></div>`).appendTo($filter_div)
        return $slider[0]  // html dom element
    }
    filter_slider_event(name, min_value, max_value) {
        // called by a filter slider when it's value is changed
        this.filters[name].min = min_value
        this.filters[name].max = max_value
        this.sigma.refresh()

        // Node reducers go before edge reducers, so nodes aren't properly hidden when the edge slider moves.
        // We need an extra refresh for the node reducers to get the updated edge information
        if (this.settings.edge_filters_hide_nodes) this.sigma.refresh()
    }

    // Tree cluster slider
    // TODO: tree slider doesn't work well because the animations can't skip a level.
    add_tree_slider() {
        // adds a slider element to the page for cluster tree traversal
        let id = "tree_slider"
        let old_div = this.$root.find(`div#${id}`)
        if (old_div[0]) {  // a div for this ID already exists
            old_div.remove()  // remove it
        }
        let $slider_div = $(`<div class="${MAPPER}" id="${id}"><p>Cluster Tree</p></div>`).appendTo("body")//("#interface")
        let $slider = $(`<div class="slider"></div>`).appendTo($slider_div)//("#interface")

        let levels = []  // indexes are levels and values are the levels names, plus an extra "all" level.
        let i = 0
        for (let level of this.state.tree.levels) {
            levels[i] = level
            i++
        }
        levels[i] = "all"  // last level is is where all nodes are open. doesn't have a name associated with it
        let max = levels.length-1  // max level number

        let percents = {}  // object of percentage values mapping to numerical values for noUiSlider
        for (let i=0; i<levels.length; i++) {
            let p;
            if (i==0) p="min";
            else if (i==max) p="max";
            else p=`${100*i/(max)}%`;
            percents[p] = i
        }

        // noUiSlider needs the html dom element, not the jquery object.
        noUiSlider.create($slider[0], {
            start: [1],  // starting positions of handles
            range: percents,
            orientation: 'vertical',
            tooltips: true,  // visually controlled with css .noUi-tooltip
            snap: true,  // snap handle to range values
            pips: {  // tick marks
                mode: 'range',
                density: 100,  //  only tick exactly at each range step
                format: {
                    to: () => ""
                }
            },
            format: {  // convert numerical slider value to category
                to: (i) => levels[i],
                from: (val) => levels.indexOf(val)
            }
        });

        $slider[0].noUiSlider.on("update", (values) => {  // bind the slider update event
            this.state.tree.set_depth(levels.indexOf(values[0]))
        })
    }
    add_tree_buttons() {
        let $div = this.$root.find("div#tree").show()
        let $up = this.$root.find("div#tree button#tree_up")
        let $down = this.$root.find("div#tree button#tree_down")

        $up.on("click", () => {
            //if (this.slow_down_clicks(TREE_ANIMATE_DURATION))
                this.state.tree.modify_depth(1)
        })
        $down.on("click", () => {
            //if (this.slow_down_clicks(TREE_ANIMATE_DURATION))
                this.state.tree.modify_depth(-1)
        })
    }
    slow_down_clicks(interval) {
        // returns true if called long enough after the last call
        let now = Date.now();
        if (this.last_click_time && now - this.last_click_time < interval) {
            return false;
        }
        this.last_click_time = now;
        return true;
    }


    //
    // Dealing with importing config maps
    //
    // import JSON config for default mappings
    // Basically translates an object to the function calls in the external methods section below and verifies inputs
    import_config(config) {
        this.original_config_json = config
        if (config !== undefined) {
            // all settings from config
            if (config.settings !== undefined) {
                this.cluster_misc = config.settings.cluster_MISC  // TODO move these to this.state.settings and add documentation for them.
                this.cluster_level = config.settings.cluster_level
                this.state.settings.edge_filters_hide_nodes = config.settings.edge_filters_hide_nodes
                this.settings.gravity = config.settings.gravity
            }

            // get all filters from config
            // filters must be applied before maps so clustering can see the filtering of sub nodes.
            if (config.filters !== undefined) {
                for (let [name, args] of Object.entries(config.filters)) {  // for each given filter method
                    this.filter({'name': name, ...args})
                }
            }

            // get all maps from config
            if (config.maps !== undefined) {
                for (let [key, args] of Object.entries(config.maps)) {  // for each given map method
                    if(!this.map_methods.includes(key)) {
                        console.error(`Mapping "${key}" does not exist. Possible maps are: ${this.map_methods}`)
                        continue;
                    }
                }

                this.validate_map_arguments(config.maps)  // validate input to all config maps
                this.apply_maps()  // apply config maps
            }
        }

        // regardless of config, create the cluster tree
        if (!this.state.tree.created) {  // if the tree wasn't created (no clustering specified in config, or no config)
            this.state.tree.create_tree([])  // create tree with no levels.
        }
        this.state.tree.update_tree_attributes()  // update branch node/edge properties given any new data mappings
    }
    update_config(config) {
        if (!config) config = this.original_config_json
        if (config !== undefined) {
            // all settings from config
            if (config.settings !== undefined) {
                this.cluster_misc = config.settings.cluster_MISC
                this.cluster_level = config.settings.cluster_level
                this.state.settings.edge_filters_hide_nodes = config.settings.edge_filters_hide_nodes
                this.settings.gravity = config.settings.gravity
            }

            // get all filters from config
            // filters must be applied before maps so clustering can see the filtering of sub nodes.
            if (config.filters !== undefined) {
                for (let [name, args] of Object.entries(config.filters)) {  // for each given filter method
                    this.filter({'name': name, ...args})
                }
            }

            // get all maps from config
            if (config.maps !== undefined) {
                for (let [key, args] of Object.entries(config.maps)) {  // for each given map method
                    if(!this.map_methods.includes(key)) {
                        console.error(`Mapping "${key}" does not exist. Possible maps are: ${this.map_methods}`)
                        continue;
                    }
                }

                this.validate_map_arguments(config.maps)  // validate input to all config maps
                this.apply_maps()  // apply config maps
            }
        }

        this.state.tree.update_tree()  // update tree
    }
    validate_map_arguments(maps) {
        // validate the input for the given index of maps from the input config
        let keys = Object.keys(maps)
        if (keys.includes('cluster') && (keys.includes('node_x') || keys.includes('node_y'))) {
            console.error('The "cluster" map is incompatible with "node_x" and "node_y". Using cluster will override any positional mapping.')
        }
        for (let [method, args] of Object.entries(maps)) {
            switch (method) {
                case "node_size":
                case "edge_size":
                    if (!(args.data !== undefined && ((args.min !== undefined && args.max !== undefined) || args.map !== undefined))) {
                        console.error(`Config Error: ${method} map requires arguments "data" and (("min" and "max") or "map")`)
                        continue;
                    }
                    break;
                case "node_x":
                case "node_y":
                    if (!(args.data !== undefined && ((args.min !== undefined && args.max !== undefined) || args.map !== undefined))) {
                        console.error(`Config Error: ${method} map requires arguments "data" and (("min" and "max") or "map")`)
                        continue;
                    }
                    break;
                case "node_color":
                case "edge_color":
                    if (args.data === undefined) {
                        console.error(`Config Error: ${method} map requires argument "data".`)
                        continue;
                    }
                    break;
                case "cluster":
                    if (!Array.isArray(args) || args.length == 0) {
                        args = undefined  // if not an array (or empty array), make undefined (clusters automatically)
                    }
                    break;
                case "cluster_node_size":
                case "cluster_edge_size":
                    var allowed = ['avg', 'max', 'count']
                    if (!allowed.includes(args.type)) {
                        console.error(`Config Error: ${method} type "${args.type}" not recognized. Valid options are: ${allowed}`)
                        continue;
                    }
                    if (args.type === "count" && (args.type === undefined || args.min === undefined || args.max === undefined)) {
                        console.error(`Config Error: ${method} map must define arguments "min" and "max" when the "type" is "count".`)
                        continue;
                    }
                    break;
            }

            // if no problems, add to maps
            this.maps[method] = args
        }
    }
    apply_maps() {
        // apply the imported config
        for (let [method, args] of Object.entries(this.maps)) {
            try {
                let defaulted = false
                switch (method) {
                    case "node_size":
                    case "edge_size":
                        if (args.map !== undefined) {
                            this[method](args.data, args.map)
                        } else {
                            this[method](args.data, {min: args.min, max: args.max})
                        }
                        break;
                    case "node_x":
                    case "node_y":
                        if (this.maps['cluster'])  // don't map if clustering is set
                            break;
                        if (args.map !== undefined) {
                            this[method](args.data, args.map)
                        } else {
                            this[method](args.data, {min: args.min, max: args.max})
                        }
                        break;
                    case "node_color":
                    case "edge_color":
                        this[method](args.data, args.map)
                        break;
                    case "cluster":
                        this.cluster(args)
                        break;
                    case "cluster_node_size":
                    case "cluster_edge_size":
                        break;
                    default:
                        defaulted = true;
                }
            } catch (error) {
                this.state.interaction.error(`problem applying map "${method}"`, error)
            }
        }
    }


    //
    // All mapping methods for external use
    //

    node_size(data, map) {
        this.map_dimension(NODE, data, 'size', CONTINUOUS, map)
    }
    edge_size(data, map) {
        this.map_dimension(EDGE, data, 'size', CONTINUOUS, map)
    }
    node_x(data, map) {
        this.map_dimension(NODE, data, 'x', CONTINUOUS, map)
    }
    node_y(data, map) {
        this.map_dimension(NODE, data, 'y', CONTINUOUS, map)
    }
    node_color(data, map) {
        let data_type = this.get_data_type(NODE, data)  // data key type
        if (data_type == CATEGORICAL) {
            // map expected to map categories to color values
            if (map === undefined || Object.keys(map).length === 0)  // no mapping given
                map = this.generate_categorical_color_map(NODE, data)
            this.map_dimension(NODE, data, 'color', CATEGORICAL, map)

        } else {  // continuous
            // map expected to contain a min, mid, and max value to map
            let stats = this.data_statistics(NODE, data)
            let func = utils.color_gradient(stats.min, 0, stats.max)  // get color gradient function with midpoint at 0
            this.map_dimension_function(NODE, data, 'color', func)
        }

    }
    edge_color(data, map) {
        let data_type = this.get_data_type(EDGE, data)  // data key type
        if (data_type == CATEGORICAL) {
            // map expected to map categories to color values
            if (map === undefined || Object.keys(map).length === 0) {  // no mapping given
                map = this.generate_categorical_color_map(EDGE, data)
            }
            this.map_dimension(EDGE, data, 'color', CATEGORICAL, map)

        } else {  // continuous
            // map expected to contain a mid value, and 3 colors to form the gradient.
            let stats = this.data_statistics(EDGE, data)
            let func = utils.color_gradient(stats.min, map.mid, stats.max, map.colors)  // get color gradient function with given midpoint
            this.map_dimension_function(EDGE, data, 'color', func)
        }

    }

    filter(args) {
        if (args.data === undefined || args.type === undefined) {
            this.error("Error applying filter", `Filter "${name}" requires arguments "data" and "type".`)
            return
        }
        if (!this.filter_types.includes(args.type)) {
            this.error("Config Error", `Filter type "${args.type}" not recognized. Possible types are: ${this.filter_types}`)
            return
        }
        // defaults
        let opts = {
            "name": `${args.data} Filter`,
            "format": null,
            ...args
        }

        // if this filter name already exists, it will be overwritten.
        var filter = {[NODE]:false, [EDGE]:false, data:opts.data, format:opts.format}
        if (opts.type === BOTH) {
            if (this.get_data_type(EDGE, opts.data)) {  // check if any edges actually have this data key
                filter[EDGE] = true
                this.filters[opts.name] = filter
                this.map_dimension(EDGE, opts.data, opts.name, FILTER)
            }
            if (this.get_data_type(NODE, opts.data)) {  // check if any nodes actually have this data key
                filter[NODE] = true
                this.filters[opts.name] = filter
                this.map_dimension(NODE, opts.data, opts.name, FILTER)
            }
        } else if (this.get_data_type(opts.type, opts.data)) {  // check if any nodes/edges actually have this data key
            filter[opts.type] = true
            this.filters[opts.name] = filter
            this.map_dimension(opts.type, opts.data, opts.name, FILTER)
        }
    }

    cluster(keys) {
        // given a list of data keys, create a tree structure with one level for each key
        let success = this.state.tree.create_tree(keys)
        if (success) this.add_tree_buttons()
    }

}

class Tree extends Tool {
    constructor(state, structure) {
        super(state)
        this.state = state
        this.structure = structure  // reference to Structure class
        this.trunk = {}  // nested structure of branches
        this.root_key = 'root'  // unique node key of the tree root
        this.branch_map = new Map() // map of node keys to their branch object
        this.depth_map = new Map()  // map of tree depth to an array of node keys at each depth
        this.parent_map = new Map()  // map node keys (both nodes and branches) to their parent's key
        this.edge_map = new Map()  // map edge IDs (both edges and branch edges) to its parent edge and children edges
        this.opened = new Map()  // map of node keys to arrays with all sub-nodes of that node
        this.height = 0  // current height of the tree
        this.depth = 0  // current viewing depth
        this.cluster_cache = {}  // keys: branch node, values: {nodes: [], edges: [], degrees: Map, depth: int, graph: graph}
        this.levels = []  // list of levels in this tree
        this.created = false  // whether the tree has been generated

        this.state.tree = this  // set the reference to itself when created

        this.init()
    }

    init() {
        this.clear_trunk()
    }

    // reset trunk to default properties
    clear_trunk() {
        this.trunk.nodes = this.graph.nodes()  // start with all the graph nodes
        this.trunk.branches = []  // begin with no branches
        this.trunk.depth = 0  // this is the root branch
        this.trunk.level = null
        this.trunk.name = null
        this.trunk.node_key = this.root_key
    }

    // given a node, return all it's sub-branch and sub-node keys in an array
    get_cluster(node) {
        let branch = this.branch_map.get(node)
        let nodes = []
        if (!(branch.branches == undefined || branch.branches.length == 0)) {
            nodes = nodes.concat(branch.branches.map(branch => branch.node_key))
        }
        if (!(branch.nodes == undefined || branch.nodes.length == 0)) {
            nodes = nodes.concat(branch.nodes)
        }
        return nodes
    }

    // return array of all open branch node keys
    get_open_branches() {
        return Array.from(this.opened.keys())
    }

    // add new levels to the tree, splitting nodes according to categories
    add_levels(levels) {
        if (levels === undefined) {  // if no levels given
            levels = this.get_optimal_levels()
        }
        this.levels = []
        for (let level of levels) {
            if (this.structure.data[NODE][level] !== CATEGORICAL) continue;  // must be categorical
            this.add_level(level, this.trunk)  // add each level to the structure
            this.levels.push(level)
        }
        // adjust levels to account for the height that was actually achieved
        this.levels = this.levels.slice(0, this.height)
    }
    add_level(key, branch) {
        if (branch.name == 'MISC')
            return;  // don't add levels to MISC branchess
        if (branch.branches == undefined || branch.branches.length == 0) {  // base case: no sub-branches
            let {categories} = this.structure.data_statistics(NODE, key, branch.nodes)  // values of this data key
            branch.branches = []

            // get the split of nodes in each category
            let [split, leftover] = this.split_leaves(branch.nodes, key, categories)

            // update height if necessary
            if (branch.depth+1 > this.height)
                this.height = branch.depth+1

            // create all category branches
            for (let [cat, nodes] of Object.entries(split)) {
                let new_branch = {
                    parent: branch.node_key,  // parent branch key
                    depth: branch.depth + 1,
                    level: key,  // data property key
                    name: cat,   // data property category
                    nodes: nodes,
                    node_key: branch.node_key + `-${key}-${cat}`
                }
                branch.branches.push(new_branch)  // add new branch to its parent
            }
            branch.nodes = leftover  // this branches nodes are now only what's left over from the split
        } else {  // otherwise, recursively call on each branch until base case
            for (let twig of branch.branches) {  // for each sub-branch
                this.add_level(key, twig)
            }
        }
    }
    split_leaves(nodes, key, categories) {
        // split given nodes into separate categories of the given data key
        // returns object with keys of each category, and values are lists of all nodes in that category
        let leaves = {}
        for (let cat of categories) {
            leaves[cat] = []
        }
        let leftover = []  // for nodes without this data value

        for (let node of nodes) {
            let attrs = this.graph.getNodeAttributes(node)
            let category = this.structure.get_data(attrs, key)
            if (category === null || category === undefined)
                leftover.push(node)
            else
                leaves[category].push(node)  // add node to appropriate category
        }

        // TODO temporary until I can connect nodes to branches
        // if any category only has one node, instead put it in the 'MISC' category
        console.log('Cluster MISC setting:', this.structure.cluster_misc)
        if (this.structure.cluster_misc) {
            leaves['MISC'] = []
            for (let [cat,nodes] of Object.entries(leaves)) {
                if (nodes.length == 1 && cat != 'MISC') {
                    leaves['MISC'].push(nodes[0])
                    delete leaves[cat]
                }
            }
            if (leaves['MISC'].length == 0) {
                delete leaves['MISC']
            }
        }

        if (this.structure.cluster_misc == 'hide') {
            if (Object.keys(leaves).length == 1 && leaves['MISC'] != undefined) {
                console.log("The MISC category is the only one available, but cluster_MISC is set to 'hide'. Showing the MISC category anyway.")
                return [leaves, leftover]
            } else {
                for (let node of Object.values(leaves['MISC'])) {
                    this.structure.graph.dropNode(node)  // drop this misc node
                }
                delete leaves['MISC']
            }
        }
        return [leaves, leftover]
    }
    // determines the optimal hierarchical structure, and returns an array of category names in that order.
    get_optimal_levels() {
        let levels = {}  // all categorical data keys mapped to how many categories it has
        for (let [data, type] of Object.entries(this.structure.data[NODE])) {
            if (type !== CATEGORICAL) continue;  // must be categorical
            let stats = this.structure.data_statistics(NODE, data)
            if (stats.categories.length > 1)  // only make it a level if there is more than 1 category
                levels[data] = {nodes: stats.total, cats: stats.categories.length}
        }
        // sort by number of nodes in each level (high to low), then by number of categories in that level (low to high)
        console.log("Category Distribution: ", levels)
        return Object.keys(levels).sort((a, b) => {
            let compare = levels[b].nodes - levels[a].nodes
            if (compare == 0)  // if no node difference
                compare = levels[a].cats - levels[b].cats  // compare number of categories
            return compare
        })
    }

    log_tree() {
        if (this.levels == undefined || this.levels.length == 0) return;
        this.depth_map.forEach((value, key) => {
            if (key === 0 || key === this.height+1) return;  // top or bottom
            let level = this.levels[key-1]
            console.log(level+': ', value)
        })
    }

    // add a new tree node/edge to the graph
    add_new_node(key, attrs) {
        let defaults = {
            x: 0,
            y: 0,
            size: 100,
            color: "#111111",
            data: {},
            filters: {},
            tree: true
        }
        this.graph.addNode(key, Object.assign(defaults, attrs))
    }
    add_new_edge(key, source, target, attrs) {
        let defaults = {
            size: 1,
            color: "#111111",
            data: {},
            filters: {},
            tree: true
        }
        // add this edge if it doesn't exist. If it does, update it's properties.
        this.graph.mergeUndirectedEdgeWithKey(key, source, target, Object.assign(defaults, attrs))
    }

    // creates all lookup maps for the tree
    create_maps() {
        this.branch_map = new Map()  // clear maps
        this.depth_map = new Map()
        this.parent_map = new Map()
        this.edge_map = new Map()
        this.opened = new Map()
        this.update_branch_map(this.trunk)  // recursively update branch_map and parent_map
        this.update_depth_map()  // update depth_map
    }
    update_branch_map(branch, parent) {
        this.branch_map.set(branch.node_key, branch)  // map the node key to it's branch
        if (branch.branches != undefined) {  // sub branches
            for (let twig of branch.branches) {  // for each sub-branch
                this.update_branch_map(twig, branch)  // recursively update the map for these sub-branches
            }
        }
        // also update parent_map while we're here
        this.parent_map.set(branch.node_key, parent ? parent.node_key:parent)  // map the node key to the parent key
        if (branch.nodes != undefined) {  // sub nodes
            for (let node of branch.nodes) {  // for each sub-node
                this.parent_map.set(node, branch.node_key)  // map the node key to the parent key
            }
        }
        // base case is no sub branches
    }
    update_depth_map() {
        this.branch_map.forEach((branch, key) => {
            if (this.depth_map.has(branch.depth)) {  // update depth map
                this.depth_map.get(branch.depth).push(branch.node_key)
            } else {
                this.depth_map.set(branch.depth, [branch.node_key])
            }

            // also add non-branch nodes to depth below it
            if (!this.depth_map.has(branch.depth+1)) {
                this.depth_map.set(branch.depth+1, [])
            }
            for (let node of branch.nodes) {
                this.depth_map.get(branch.depth+1).push(node)
            }
        })
    }
    update_node_depth() {
        this.depth_map.forEach((nodes, depth) => {
            for (let node of nodes) {
                this.graph.setNodeAttribute(node, "depth", depth)  // set node depth attribute
            }
        })
    }

    // remove all current branch nodes from the graph
    remove_from_graph() {
        this.branch_map.forEach((mapping, node) => {
            this.graph.dropNode(node)
        })
    }

    // adding and updating tree branch/edge properties
    add_to_graph(branch) {
        // recursively add all branch nodes to the graph
        let attributes = {
            label: branch.name,
            level: branch.level,
            depth: branch.depth,
            name: branch.name  // data category
        }
        if (branch.depth == 0) {  // root branch
            attributes.label = 'tree-root'
            attributes.size = 0
            attributes.hidden = true
            attributes.fixed = true
        } else {
            attributes.data = {
                [branch.level]: branch.name  // assign to it's mapped data category
            }
        }
        this.add_new_node(branch.node_key, attributes)  // add it to the graph

        if (branch.branches == undefined) {  // base case: no sub-branches
            return;
        } else {  // otherwise, recursively call on each branch until base case
            for (let twig of branch.branches) {  // for each sub-branch
                this.add_to_graph(twig)
            }
        }
    }

    update_branch_attributes() {
        // make branch nodes reflect attributes of their sub-nodes
        let attribute_map = new Map()  // map of branch keys to their attribute list
        this.get_cluster_attributes(this.trunk.node_key, attribute_map)  // populate it


        // if cluster_node_size has been mapped
        var method
        if (this.structure.maps.cluster_node_size) {  // node size has been mapped
            method = this.structure.maps.cluster_node_size.type
            if (method === 'count') {
                var min_count = Infinity, max_count = 0  // get min and max counts
                attribute_map.forEach((attributes, key) => {
                     if (attributes.count < min_count) min_count = attributes.count;
                     if (attributes.count > max_count) max_count = attributes.count;
                })
            }
        } else {  // not mapped - use max as default
            method = 'max'
        }

        // assign node attributes from attribute_map
        attribute_map.forEach((attributes, key) => {
            let size
            if (method === 'avg') {
                size = utils.array_mean(attributes.sizes)
            } else if (method === 'max') {
                size = Math.max(...attributes.sizes)
            } else if (method === 'count') {
                let min_size = this.structure.maps.cluster_node_size.min  // get min and max
                let max_size = this.structure.maps.cluster_node_size.max
                size = this.structure.linear_map(attributes.count, min_count, max_count, min_size, max_size)
            }

            this.graph.setNodeAttribute(key, 'size', size)
            this.graph.setNodeAttribute(key, 'count', attributes.count)

            let most_color = utils.array_mode(attributes.colors)  // most common sub node color
            this.graph.setNodeAttribute(key, 'color', most_color)

            let filters = {}  // min and max of each filter
            for (let [name, vals] of Object.entries(attributes.filters)) {
                let min_val = Math.min(...vals)
                let max_val = Math.max(...vals)
                filters[name] = {min:min_val, max:max_val}
            }
            this.graph.setNodeAttribute(key, 'filters', filters)
        })
    }
    get_cluster_attributes(node, attribute_map) {
        // recursively populate attribute map
        // attribute_map: keys are branch node keys, values are object with nodes as keys and the following attrs object as values
        // filters has filter names as keys and a list of all filter values as value
        let branch = this.branch_map.get(node)
        let attrs = attribute_map.get(node) || {count: 0, sizes: [], colors: [], filters: {}}

        // populate node filters
        for (let name of Object.keys(this.structure.filters)) {
            if (!this.structure.filters[name][NODE]) continue;  // if not a node filter
            attrs.filters[name] = []
        }

        if (branch.branches !== undefined) {  // has sub branches
            for (let twig of branch.branches) {  // for each sub-branch
                this.get_cluster_attributes(twig.node_key, attribute_map)  // recursively get attributes
                // add child attrs lists to parent attrs lists
                let child_attrs = attribute_map.get(twig.node_key)
                attrs.sizes = attrs.sizes.concat(child_attrs.sizes)
                attrs.colors = attrs.colors.concat(child_attrs.colors)
                attrs.count += child_attrs.count
                for (let name of Object.keys(child_attrs.filters)) {
                    attrs.filters[name] = attrs.filters[name].concat(child_attrs.filters[name])
                }

            }
            attribute_map.set(node, attrs)
        }  // base case is it has no sub branches'

        // has sub nodes
        if (branch.nodes !== undefined) {
            for (let sub_node of branch.nodes) {
                attrs.count += 1
                attrs.sizes.push(this.graph.getNodeAttribute(sub_node, 'size'))
                attrs.colors.push(this.graph.getNodeAttribute(sub_node, 'color'))
                for (let [name,val] of Object.entries(this.graph.getNodeAttribute(sub_node, 'filters'))) {
                    attrs.filters[name].push(val)
                }
            }
            attribute_map.set(node, attrs)
        }

    }

    update_branch_edges() {
        // make branch edges reflect attributes of their sub-edges
        let attribute_map = this.get_cluster_edges()

        // if cluster_edge_size has been mapped,
        var method
        if (this.structure.maps.cluster_edge_size) {  // node size has been mapped
            method = this.structure.maps.cluster_edge_size.type
            if (method === 'count') {
                var min_count = Infinity, max_count = 0  // get min and max counts
                for (let node of Object.keys(attribute_map)) {
                    for (let [other_node, attributes] of Object.entries(attribute_map[node])) {
                        if (attributes.count < min_count) min_count = attributes.count;
                        if (attributes.count > max_count) max_count = attributes.count;
                    }
                }
            }
        } else {  // not mapped - use max as default
            method = 'max'
        }

        // add/merge edge attributes from edge attributes map
        for (let [node, edges] of Object.entries(attribute_map)) {  // for each branch
            let node_label = this.graph.getNodeAttribute(node, 'label')
            for (let [other_node, edge] of Object.entries(edges)) {  // for each other connected branch
                if (node == other_node) continue;  // skip if it's a self-edge
                if (edge.count === 0) continue;  // if no connections, don't create a branch edge
                let other_node_label = this.graph.getNodeAttribute(other_node, 'label')

                let size  // map size depending on cluster_edge_size
                if (method === 'avg') {
                    size = utils.array_mean(edge.sizes)
                } else if (method === 'max') {
                    size = Math.max(...edge.sizes)
                } else if (method === 'count') {
                    let min_size = this.structure.maps.cluster_edge_size.min  // get min and max
                    let max_size = this.structure.maps.cluster_edge_size.max
                    size = this.structure.linear_map(edge.count, min_count, max_count, min_size, max_size)
                }

                // attributes for new branch edge
                let attributes = {
                    tree: true,
                    //label: node_label + "<->" + other_node_label  // default branch edge label  // TODO put back in when overlapping label issue is solved.
                    count: edge.count,  // number of sub edges
                    color: utils.array_mode(edge.colors),  // most common color
                    size: size,  // average size
                    filters: {},
                }
                for (let [name, vals] of Object.entries(edge.filters)) {
                    let min_val = Math.min(...vals)
                    let max_val = Math.max(...vals)
                    attributes.filters[name] = {min:min_val, max:max_val}
                }

                this.add_new_edge(edge.key, node, other_node, attributes)

                // set the parent and children of this new edge
                this.edge_map.set(edge.key, {
                    parent: edge.parent,
                    children: edge.children
                })

                // for each sub-edge of this new edge
                for (let sub_edge of edge.children) {
                    if (this.edge_map.has(sub_edge)) continue;   // this sub-edge is in the edge map, which means it's a branch edge
                    this.edge_map.set(sub_edge, {parent: edge.key, children: []})  // otherwise, it's a normal edge and has no children
                }
            }
        }
    }
    get_cluster_edges() {
        // populate a map of branch edges
        // maps each branch node to all other branch nodes, with edge properties between them
        // first level keys are node keys, second level are connecting node keys, third level are edge attributes.
        let edges = {}
        var filters_template = {}  // edge filter map template
        for (let name of Object.keys(this.structure.filters)) {
            if (!this.structure.filters[name][EDGE]) continue;  // if not an edge filter
            filters_template[name] = []
        }
        for (let depth=this.height; depth>0; depth--) {  // start at bottom tree branch depth, and go up to depth 1
            for (let node of this.depth_map.get(depth)) {  // for each node at this depth
                let branch = this.branch_map.get(node)  // get branch object for this node key
                if (branch == undefined) continue; // this is a regular node, move on

                // keep track of all edges from this branch
                edges[node] = {}
                for (let other_node of this.depth_map.get(depth)) {  // for all other branch nodes at this depth
                    // if other_node is already connected to this node, and if they are different nodes. (don't double count the same connection)
                    if (node !== other_node && edges[other_node] !== undefined) continue;
                    edges[node][other_node] = {
                        key: `${node}<->${other_node}`,  // unique key for this edge
                        parent: null,  // parent ID
                        children: [],  // list of IDs of IMMEDIATE sub-edges
                        count: 0,  // number of ALL sub-edges (including non-immediate)
                        colors: [],  // list of ALL sub-edge colors
                        sizes: [],  // list of ALL sub-edge sizes
                        filters: $.extend(true, {}, filters_template)  // deep copy the filter template
                    }
                }

                // collect edge attributes from immediate regular children (non-branches)
                if (branch.nodes != undefined) {
                    let checked_edges = new Set()  // temporarily keep track of edges checked so as not to double count
                    for (let sub_node of branch.nodes) {  // for each sub node
                        this.graph.forEachEdge(sub_node, (edge) => {  // for each edge of this sub node
                            if (!checked_edges.has(edge)) { // haven't checked this edge yet
                                let attrs = this.graph.getEdgeAttributes(edge)  // edge attributes
                                let adj = this.graph.opposite(sub_node, edge)  // get adjacent node
                                let other_node = this.parent_map.get(adj)  // get parent of adjacent node
                                if (edges[node][other_node] !== undefined) {  // this connection is defined, add all sub-node attributes
                                    edges[node][other_node].count += 1
                                    edges[node][other_node].children.push(edge)
                                    edges[node][other_node].colors.push(attrs.color)
                                    edges[node][other_node].sizes.push(attrs.size)
                                    for (let [name, val] of Object.entries(attrs.filters)) {
                                        edges[node][other_node].filters[name].push(val)
                                    }
                                }
                                checked_edges.add(edge)  //  mark edge as checked
                            }
                        })
                    }
                }

                // collect sub-edge attributes from sub-branch node connections
                // for each sub-edge that is also a branch, add that sub-edge's stats to the parent
                if (branch.branches != undefined) {
                    for (let sub_branch of branch.branches) {  // for each sub branch
                        for (let [other_sub_node, sub_edge] of Object.entries(edges[sub_branch.node_key])) {  // for each connection of this sub branch
                            let other_node = this.parent_map.get(other_sub_node)  // get parent of sub branch connection
                            if (edges[node][other_node] !== undefined) {  // if this connection is defined, append all sub-edge attributes
                                sub_edge.parent = edges[node][other_node].key  // set the parent of this sub_edge to this branch edge
                                edges[node][other_node].children.push(sub_edge.key)  // append this sub_edge to the children of the parent
                                edges[node][other_node].count += sub_edge.count
                                edges[node][other_node].colors = edges[node][other_node].colors.concat(sub_edge.colors)
                                edges[node][other_node].sizes = edges[node][other_node].sizes.concat(sub_edge.sizes)
                                for (let [name, val] of Object.entries(sub_edge.filters)) {
                                    edges[node][other_node].filters[name] = edges[node][other_node].filters[name].concat(val)
                                }
                            }
                        }
                    }
                }

            }
        }

        return edges
    }
    update_tree_attributes() {
        // update both branches and edges
        this.update_branch_attributes()
        this.update_branch_edges()
    }

    // retrieves info about the sub-graph of a given branch. Uses this.cluster_cache
    get_cluster_info(branch) {
        if (this.cluster_cache[branch] == undefined) {  // none stored
            let nodes = new Set(this.get_cluster(branch))  // get cluster (this branch's children)
            this.cluster_cache[branch] = new Cluster(this.state, nodes, branch)  // store new cluster in cache
        }
        return this.cluster_cache[branch]  // return cached cluster
    }

    //
    // External methods
    //

    // creates the tree structure given an array of levels (data keys), top to bottom
    create_tree(levels, update=false) {
        this.remove_from_graph()  // remove all nodes in branch_map from the graph, if they exist

        this.clear_trunk()  // clear branch structure
        this.cluster_cache = {}  // clear edge cache

        this.add_levels(levels)  // add the given levels to the tree
        this.create_maps()  // create maps from the new tree structure

        this.add_to_graph(this.trunk)  // recursively add all branch nodes in the structure to the graph
        this.update_tree_attributes()  // branch/edge attributes reflect sub node/edge attributes

        this.update_node_depth() // set depth of nodes from depth_map and set out_of_tree state

        this.log_tree()  // output tree structure to console

        this.sigma.refresh()  // force the sigma.nodeDataCache to populate so the physics simulator works in the first open_node()

        if (update) return;

        // initialize state of tree
        if (this.structure.maps['node_x'] || this.structure.maps['node_y']) {  // if any positional mapping specified
            this.opened.set(this.root_key, this.get_cluster(this.root_key))  // mimic opening the root node, but don't do any of the cluster stuff
            this.sigma.setCustomBBox(this.sigma.getBBox())  // set bounding box to encompass entire opened graph
            this.state.interaction.set_home_bbox()  // set this state as the default bbox
        } else {  // no positional mapping
            this.branch_map.forEach((branch, key) => {
                this.open_node(key, false)  // all start open with physics sim, no animation
            })

            this.sigma.setCustomBBox(this.sigma.getBBox())  // set bounding box to encompass entire opened graph
            this.state.interaction.set_home_bbox()  // set this state as the default bbox

            this.close_node(this.root_key, false)  // close the whole tree, starting at the root (ensures all branches collapse their sub nodes)
            this.set_depth(this.structure.cluster_level || 0, false)  // set starting depth of the tree from settings (or default to 0)
            this.state.simulation.iterate_FA2(200)  // add some extra physics iterations of the FA2 to start
        }

        this.sigma.refresh()
        this.created = true  // mark as created even if no levels were added.

        // whether creation was successful (at least one tree level created)
        if (this.levels.length > 0) return true;
        else return false
    }
    update_tree() {
        let old_opened = this.opened
        let old_depth = this.depth
        this.create_tree(this.levels, true)  // re-create tree given new data
        this.opened = old_opened  // maintain same opened clusters
        this.depth = old_depth  // maintain same viewing depth
    }

    // Get branch information by node/edge ID
    get_node_children(node) {
        let branch = this.state.tree.branch_map.get(node)
        if (!branch) return [];  // regular nodes aren't in the branch map and have no children
        let nodes = branch.nodes  // list of node IDs
        let branches = []  // list of branch node IDs
        if (branch.branches) {
            for (let b of branch.branches) {
                branches.push(b.node_key)
            }
        }
        return branches.concat(nodes)
    }
    get_edge_children(edge) {
        return this.state.tree.edge_map.get(edge).children
    }
    get_node_parent(node) {
        return this.state.tree.branch_map.get(node).parent
    }
    get_edge_parent(edge) {
        return this.state.tree.edge_map.get(edge).parent
    }

    // set entire tree open to a given depth
    set_depth(depth, animate=true) {
        if (typeof depth != 'number') depth = 0  // invalid input - default to 0
        depth = Math.round(depth)  // integer
        // can't set depth beyond from 0 to height
        if (depth < 0) {
            depth = 0;
        } else if (depth > this.height) {
            depth = this.height;
        }
        this.depth = depth  // track current depth
        // close all nodes one depth lower
        if (this.height > depth) {
            for (let node of this.depth_map.get(depth+1)) {
                this.close_node(node, animate)
            }
        }
        // open all nodes at this depth
        for (let node of this.depth_map.get(depth)) {
            this.open_node(node, animate)
        }
    }
    // modify current viewing depth by n
    modify_depth(n=1) {  // default is increase by 1
        this.set_depth(this.depth+n)
    }

    // open a branch node - add it and its immediate sub-nodes to this.opened, as well as every parent branch.
    open_node(node, animate=true) {
        // if it's already open, or it's not a tree node at all, do nothing else
        if (this.opened.get(node) != undefined || !this.structure.is_tree_node(node)) return;

        if (this.branch_map.get(node).parent != undefined) {  // if the node has a parent
            this.open_node(this.branch_map.get(node).parent, animate)  // recursively open all parents
        }
        // this.depth = this.branch_map.get(node).depth
        // TODO This can only work if the tree is able to go from any level to any other level (and have the animations work).

        this.opened.set(node, this.get_cluster(node))

        // expand the cluster
        let cluster = this.get_cluster_info(node)
        cluster.expand(animate)
    }

    // closes the branch node - removes it and ALL its sub nodes (recursively) from this.opened
    close_node(node, animate=false) {
        // if already closed, or not even a tree node, do nothing
        if (this.opened.get(node) == undefined || !this.structure.is_tree_node(node)) return;

        for (let sub_branch of this.opened.get(node)) {  // close all sub branches first
            this.close_node(sub_branch, animate)
        }

        this.opened.delete(node)  // remove from this.opened

        // collapse the cluster
        var cluster = this.get_cluster_info(node)
        cluster.collapse(animate)



    }
}

class Cluster {
    // A cluster of nodes with it's own graphology graph that contains only internal edges
    constructor(state, nodes, node) {
        this.state = state
        this.sigma = state.sigma
        this.tree = state.tree
        this.global_graph = state.tree.graph

        this.graph;  // dynamic graph that updates the global graph position
        this.optimal_graph = null  // constant version of the graph with nodes in optimal positions

        this.degree_map = new Map()
        this.depth = this.global_graph.getNodeAttribute(node, 'depth')
        this.scale = this.state.simulation.scale(this.depth)  // get the physics sim scale for this cluster from the given depth

        this.parent = node
        this.starting_local_positions = {}  // starting local positions for expanding

        // functions to cancel the current animation and timeout
        this._cancel_animation = null
        this._cancel_timeout = null

        this.init(nodes)
    }

    // Create the subgraph from the given node IDs from the global_graph
    init(nodes) {
        let edges = new Set()
        this.graph = this.global_graph.nullCopy()  // sub-graph for this cluster. Copies global graph type & properties, but not nodes or edges

        for (let node of nodes) {  // for each node
            let attrs = this.global_graph.getNodeAttributes(node)
            this.graph.addNode(node, (({x,y,size})=>({x,y,size}))(attrs))  // add node (and x,y,size attrs) to subgraph
            this.global_graph.forEachEdge(node, (edge) => {edges.add(edge)})  // collect all edges
        }
        for (let edge of edges) {  // for each edge
            let extremities = this.global_graph.extremities(edge)  // nodes at each end
            if (!(nodes.has(extremities[0]) && nodes.has(extremities[1]))) {  // if either extremity isn't in the cluster
                edges.delete(edge)  // remove from edge collection
            } else {  // both extremities are in the cluster
                this.graph.addEdgeWithKey(edge, extremities[1], extremities[0])  // TODO is the ordering of these guaranteed? should I use .source and .target instead?
            }
        }

        //cluster.graph = graph
        //cluster.depth = this.branch_map.get(branch).depth
        this.update()  // update positions
    }

    // Get optimal positions for this node cluster
    // Should be called right after graph is fully created or the nodes in this cluster are added/removed
    update() {
        this.optimal_graph = this.graph.copy()  // copy the local graph
        // need to spread out nodes a bit for physics to work
        let angle = 2*Math.PI / this.graph.order  // angle to spread cluster out by
        let radius = 1 / (100*this.scale)  // radius to spread cluster out by
        let n = 0
        this.optimal_graph.updateEachNodeAttributes((node, attr) => {
            attr.x = radius * Math.cos(angle*n)
            attr.y = radius * Math.sin(angle*n)
            n += 1
            return attr
        })
        this.state.simulation.simulate(this.optimal_graph, 50, true)  // run some iterations of FA to place nodes
    }

    global_to_local(global_positions, assign=true) {
        // convert the given global node positions to local node positions, and optionally assign them
        // if none given, use current global positions and assign them
        let parent_pos = this.global_graph.getNodeAttributes(this.parent)  // get parent position
        let local_positions = {}
        if (!global_positions) {
            global_positions = {}
            this.graph.forEachNode((node, attrs) => {
                global_positions[node] = this.global_graph.getNodeAttributes(node)  // get GLOBAL attrs of this node
            })
        }

        for (let [node, pos] of Object.entries(global_positions)) {
            let x = (pos.x - parent_pos.x) * this.scale
            let y = (pos.y - parent_pos.y) * this.scale
            local_positions[node] = {x:x, y:y}
            if (assign) this.graph.mergeNodeAttributes(node, {x:x, y:y})
        }
        return local_positions
    }
    local_to_global(local_positions, assign=true) {
        // convert the given local node positions to global node positions and optionally assign those positions
        // if none given, use current local positions and assign them
        let parent_pos = this.global_graph.getNodeAttributes(this.parent)  // get parent position
        let global_positions = {}
        if (!local_positions) {
            local_positions = {}
            this.graph.forEachNode((node, attrs) => {
                local_positions[node] = attrs  // get LOCAL attrs of this node
            })
        }
        for (let [node, pos] of Object.entries(local_positions)) {
            let x = pos.x/this.scale + parent_pos.x
            let y = pos.y/this.scale + parent_pos.y
            global_positions[node] = {x:x, y:y}
            if (assign && !this.tree.is_node_fixed(node)) this.global_graph.mergeNodeAttributes(node, {x:x, y:y})
        }
        return global_positions
    }

    set_animation(cancel_function) {
        // cancel_function is the function returned by Sigma animateNodes()
        this._cancel_animation = cancel_function
    }
    set_timeout(timeout_id) {
        this._cancel_timeout = () => {clearTimeout(timeout_id)}
    }
    cancel_animation() {
        if (this._cancel_animation) this._cancel_animation()
        if (this._cancel_timeout) this._cancel_timeout()
    }

    // TODO: more modular way of modifying node attributes. Right now the tool.fix() is the one that sets the 'fixed' attr, and it's only meant to be used in reducers.
    // Since I am manually setting the 'fixed' attr here, I have to be sure to manually unset it as well.

    expand_start() {
        for (let node of this.graph.nodes()) {
            this.global_graph.setNodeAttribute(node, 'fixed', true)  // prevent physics
            this.global_graph.setNodeAttribute(node, "out_of_tree", false)  // now in the tree
        }
        this.global_graph.setNodeAttribute(this.parent, "out_of_tree", true)  // parent is now out of the tree
    }
    expand_stop() {
        for (let node of this.graph.nodes()) {
             this.global_graph.setNodeAttribute(node, 'fixed', false)    // allow physics
        }
    }
    collapse_start() {
        for (let node of this.graph.nodes()) {
            this.global_graph.setNodeAttribute(node, 'fixed', true)  // prevent physics
        }
    }
    collapse_stop() {
        for (let node of this.graph.nodes()) {
             this.global_graph.setNodeAttribute(node, 'fixed', false)    // allow physics
             this.global_graph.setNodeAttribute(node, "out_of_tree", true)  // put out of tree
        }
        this.global_graph.setNodeAttribute(this.parent, "out_of_tree", false)  // parent comes back into tree
    }

    expand(animate=true) {
        // Expand cluster outward from parent node.
        // Optionally animate the expansion.
        this.cancel_animation()  // cancel any current animations

        // Move all global nodes to parent position.
        // This is so that they appear to expand outward from the parent position.
        let parent_pos = this.global_graph.getNodeAttributes(this.parent)
        for (let node of this.graph.nodes()) {
            this.global_graph.setNodeAttribute(node, 'x', parent_pos.x)
            this.global_graph.setNodeAttribute(node, 'y', parent_pos.y)
        }

        // set optimal local cluster node positions
        this.graph = this.optimal_graph.copy()

        this.expand_start()  // set starting conditions
        if (animate) {
            let global_positions = this.local_to_global(null, false)  // convert to global positions, but don't assign to global graph
            this._cancel_animation = Animate.animateNodes(this.global_graph, global_positions, {duration: TREE_ANIMATE_DURATION, easing: "quadraticOut"}, this.expand_stop.bind(this), true);
        } else {
            this.local_to_global()  // update global instantly from local positions
            this.expand_stop()
        }
    }
    collapse(animate=true) {
        // animate cluster collapsing in toward the parent
        this.cancel_animation()  // cancel any current animations
        let parent_pos = this.global_graph.getNodeAttributes(this.parent)  // get parent position

        let global_positions = {}
        for (let node of this.graph.nodes()) {
            global_positions[node] = {x:parent_pos.x, y:parent_pos.y}  // all nodes collapse to parent position
        }
        let local_positions = {}
        for (let node of this.graph.nodes()) {
            local_positions[node] = {x:0, y:0}  // all nodes collapse to parent position
        }
        this.collapse_start()
        if (animate) {
            this._cancel_animation = Animate.animateNodes(this.global_graph, global_positions, {duration: TREE_ANIMATE_DURATION, easing: "quadraticOut"}, this.collapse_stop.bind(this));
        } else {
            this.local_to_global(local_positions, true)
            this.collapse_stop()
        }
    }

}
