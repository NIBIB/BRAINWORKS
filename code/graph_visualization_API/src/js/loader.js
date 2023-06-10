const $ = require('jquery')

// Script that is initially requested by the host.
// Creates main iframe and inner script tag that then requests the full JS application inside.


function detect_browser() {
    let userAgent = navigator.userAgent;

    if (userAgent.match(/chrome|chromium|crios/i)) {
        return "chrome"
    } else if (userAgent.match(/firefox|fxios/i)) {
         return "firefox"
    } else if (userAgent.match(/safari/i)){
        return "safari"
    } else if (userAgent.match(/opr/i)){
        return "opera"
    } else if (userAgent.match(/edg/i)){
        return "edge"
    } else {
        return
    }
}

module.exports = class Graph {
    constructor(data, options={}) {
        this._data = data    // raw data or data URL
        this._$host;        // container provided by host (ID from "container" in the options)
        this._$iframe;      // main iframe
        this._$body;   // iframe body
        this._$head;   // iframe head

        this.options = {
            container: "graphAPI-container",  // ID of the given host div
            gravity: 1,  // physics gravity setting
            ready: () => {}, // Function called when the inner Graph has been initialized and is ready for its methods to be called
            debug: false,
            ...options
        }

        // init when DOM ready
        $(document).ready(function() {
            this._init()
        }.bind(this));
    }

    _init() {
        // get the container with the given ID
        this._$host = $(`#${this.options.container}`)
        if (!this._$host.length) {
            console.error(`No div with ID "${this.options.container}" was found.`)
            return
        }

        this._$iframe = $('<iframe frameBorder="0"></iframe>').appendTo(this._$host)


        if (detect_browser() == "firefox") {
            this._$iframe.on('load', () => {this.init_iframe()})  // firefox has to do an async load first for some reason
        } else {
            this.init_iframe()  // otherwise just load
        }

    }

    init_iframe() {
        this._$document = this._$iframe.contents()
        this._$body = $(this._$document[0].body)
        this._$head = $(this._$document[0].head)

        //this._$iframe.attr('style', this._$host.attr('style'))  // copy css from host to container
        this._$iframe.attr('style', "height: 100%; width: 100%; min-height: inherit; min-width: inherit;")

        // Ok, so normally, the strat here would be to create a script tag within the iframe whose source is the actual script that needs to be loaded.
        // That way, the "scope" of the loaded script is entirely within the iframe, so all css frameworks and such can use the iframe's document body and such without leaking out.
        // HOWEVER for some reason this causes a problem where the script is loaded into the OUTER scope, rather than the inner scope for some reason.
        // The workaround is to just manually request the JS file and inject it directly into the script tag.

        let req = new XMLHttpRequest();
        req.addEventListener("load", () => {
            this.inject_script(req.response)
        });
        req.open("GET", "src/js/main.min.js");
        req.send();
    }



    inject_script(graph_script) {
        let iframe_window = this._$iframe[0].contentWindow  // window object of iframe
        let iframe_document = this._$iframe[0].contentDocument  // document object of iframe
        let script_tag = iframe_document.createElement("script")
        let content = iframe_document.createTextNode(graph_script)
        script_tag.appendChild(content)
        iframe_document.head.appendChild(script_tag)

        // check container height
        if (this._$host.height() <= 0 || this._$host.width <= 0) {
            console.error("Graph Container must have a defined height and width. Currently:", this._$host.height(), this._$host.width())
        }

        // in the outer window, look for an instance of this class and swap it out for its inner window Graph object.
        // There may be multiple instances each with its own iframe, so we need to check to see if the iframe matches this one.
        let found = false
        for (let [name, object] of Object.entries(window)) {
            if (object instanceof Graph && object._$iframe === this._$iframe) {
                console.log("loader class found")
                window[name] = new iframe_window.Graph(object._data, object.options)
                found = true
            }
        }
        if (!found) {
            console.error("Could not find graph instance in the window. Make sure you initialize a new Graph() object in the global scope.")
        }
    }

    ready(callback) {
        // set the callback
        this.options.ready = callback
    }
}
