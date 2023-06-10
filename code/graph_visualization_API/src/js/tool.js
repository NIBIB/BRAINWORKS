const $ = require('jquery')
const utils = require("./utils.js")

module.exports = class Tool {
    // Base class for managing graph properties.
    // All other tools should inherit from this class.
    constructor(state) {
        this.state = state

        // convenient references to global state
        this.graph = state.graph;  // graphology graph object
        this.sigma = state.sigma;  // sigma object
        this.settings = state.settings;  // settings config
        this.$root = state.$root  // root container object to contextualize all JQuery usage

        this.last_time = null

    }

    // logging
    log(msg, time=false) {
        // logs a message and optionally show the amount of time passed since called last
        let now = window.performance.now()
        if (time && this.last_time) {
            let elapsed = now - this.last_time
            console.log(`${msg} (${elapsed}ms)`)
        } else {
            console.log(msg)
        }
        this.last_time = now
    }

    error(heading, msg) {
        this.state.interface.error(heading, msg)
    }

    warning(heading, msg) {
        this.state.interface.warning(heading, msg)
    }

    //
    // The following methods check the state of a node or edge
    // This state is obtained from the sigma data cache, not the graph, so it reflects reducer rendering changes.
    // Should NOT be used in node/edge reducers
    //

    get_node_property(node, property) {
        if (this.sigma.nodeDataCache[node] !== undefined)
            return this.sigma.nodeDataCache[node][property]
        return false
    }
    get_edge_property(edge, property) {
        if (this.sigma.edgeDataCache[edge] !== undefined)
            return this.sigma.edgeDataCache[edge][property]
        return false
    }

    // check various node properties
    is_node_fixed(node) {
        return this.get_node_property(node, 'fixed')
    }
    is_node_hidden(node) {
        return this.get_node_property(node, 'hidden')
    }
    is_node_obscured(node) {
        return this.get_node_property(node, 'obscured')
    }
    is_node_unfocused(node) {
        return this.get_node_property(node, 'unfocused')
    }
    is_node_out_of_range(node) {
        return this.get_node_property(node, 'out_of_range')
    }

    // check if edge is currently hidden
    is_edge_hidden(edge) {
        // TODO this is a hack until the bug is fixed
        let nodes = this.graph.extremities(edge)
        if (this.is_node_hidden(nodes[0]) && this.is_node_hidden(nodes[1])) return true;
        return this.get_edge_property(edge, 'hidden')
    }
    // check if edge is currently obscured
    is_edge_obscured(edge) {
        return this.get_edge_property(edge, 'obscured')
    }
    is_edge_unfocused(edge) {
        return this.get_edge_property(edge, 'unfocused')
    }
    is_edge_out_of_range(edge) {
        return this.get_edge_property(edge, 'out_of_range')
    }

    // whether the given node is a category tree node
    is_tree_node(node) {
        return this.graph.getNodeAttribute(node, "tree")
    }

    // whether the given node is a category tree node
    is_tree_edge(edge) {
        return this.graph.getEdgeAttribute(edge, "tree")
    }

    //
    // The following methods check/modify the state of a given attributes object.
    // This is because node/edge states should not be modified directly - only in reducers.
    // Should only be used in node/edge reducers.
    //

    is_hidden(attrs) {
        return attrs["hidden"]
    }
    is_obscured(attrs) {
        return attrs["obscured"]
    }
    is_unfocused(attrs) {
        return attrs["unfocused"]
    }
    is_highlighted(attrs) {
        return attrs["highlighted"]
    }
    if_fixed(attrs) {
        return attrs["fixed"]
    }
    is_out_of_range(attrs) {
        return attrs["out_of_range"]
    }
    is_out_of_tree(attrs) {
        return attrs["out_of_tree"]
    }

    hide(attrs) {
        attrs["hidden"] = true
    }
    obscure(attrs) {
        attrs["obscured"] = true
        attrs.label = undefined;
        attrs.zIndex = -1  // push to bottom
        attrs.color = "#f9f9f9";
    }
    unfocus(attrs) {
        if (!attrs["unfocused"]) {
            attrs.color = attrs.color ? utils.lighten(attrs.color, 0.9) : attrs.color
        }
        attrs["unfocused"] = true
        //attrs.label = undefined;
        attrs.zIndex = -1;
    }
    highlight(attrs) {
        attrs["highlighted"] = true
    }
    fix(attrs) {
        attrs["fixed"] = true
    }
    out_of_range(attrs) {
        attrs["out_of_range"] = true
    }
    out_of_tree(attrs) {
        attrs["out_of_tree"] = true
    }



    //
    // Reducers to be overwritten
    //

    // node reducer for rendering temporary states
    node_reducer(node, attrs) {
        // return temporary node properties
        return attrs;
    }

    // edge reducer for rendering temporary states
    edge_reducer(edge, attrs) {
        // return temporary edge properties
        return attrs;
    }

    init() {
        // runs on instantiating the object
    }

    init_graph() {
        // runs when the graph is loaded
    }

}

