const $ = require('jquery')
const sigma = require("sigma")
const bootstrap = require("bootstrap")
const tippy = require("tippy.js").default
const Tool = require("./tool.js")
const utils = require("./utils.js")

const NODE = 'node'
const EDGE = 'edge'

module.exports = class Interface extends Tool{
    // Manages user interface
    constructor(state) {
        super(state)

        // components
        this.menu = new Menu(this)
        this.help = new Help(this)
        this.settings_menu = new Settings(this)
        this.alert = new Alert(this)
        this.interactables = new Interactables(this)
        this.data_display = new DataDisplay(this)
        this.right_click_menu = new RightClickMenu(this)
        this.custom_popup = new CustomPopup(this)
        this.custom_modal = new CustomModal(this)

        // graph container
        this.$container = this.$root.find('#sigma-container')
        this.init()
        this.state.interface = this
    }

    init() {
        // put tooltips on anything with a title
        let with_titles = $("[title]")
        for (let elem of with_titles) {
            this.add_tooltip($(elem).attr('title'), $(elem), 'auto', 500)
            $(elem).attr('title', '')  // remove title
        }
    }

    init_graph() {
    }

    // show an error message
    error(heading, message) {
        this.alert.error(heading, message)
    }

    warning(heading, message) {
        this.alert.warning(heading, message)
    }

    // run the tutorial
    tutorial(node=null) {
    this.help.hide()
        // optionally specify a node key to target for appropriate tooltips
        let target_node = node
        if (!target_node) {  // if not given, just pick the first one
            target_node = this.state.graph.findNode(attrs => !attrs.hidden)
        }
        if (!target_node) {  // if node not found or hidden
            console.log(`Node with ID "${node}" not found or hidden.`)
        }
        console.log(`Using node with key "${target_node}" as target for the tutorial.`)

        // close the help div if it's open
        this.help.hide()

        // an invisible div to display a floating tooltip
        let a = $('<div id="tooltip-float"></div>').css({position: 'absolute', left: '80%', top: '50%', width: "5em", height: "0em"}).appendTo(this.$container)
        // console.log(a))
        Promise.resolve()
            .then(()=>{return this.tutorial_tip("node", target_node,        "top",   "Click a node to select it and highlight its neighbors, then click away to de-select it.", "Next")})
            //.then(()=>{return this.tutorial_tip("node", target_node,        "top",   "Right Click a node to see its properties, then click away to hide them.", "Next")})
            .then(()=>{return this.tutorial_tip("node", target_node,        "top",   "Click and drag a node to move it", "Next")})
            .then(()=>{return this.tutorial_tip("elem", "#tooltip-float",   "none",  "Use the scroll wheel to zoom in and out", "Next")})
            .then(()=>{return this.tutorial_tip("elem", "#tooltip-float",   "none",  "Click and drag the background to look around", "Next")})
            //.then(()=>{return this.tutorial_tip("elem", "button#menu-button", "bottom",    "Click here to open the main menu", "Next")})
            .then(()=>{return this.tutorial_tip("elem", "#center-button",    "bottom",    "Click here to center the graph and reset the zoom level", "Next")})
            .then(()=>{return this.tutorial_tip("elem", "#organize-button",  "bottom",    "Click here to instantly organize the graph", "Next")})
            .then(()=>{return this.tutorial_tip("elem", "#search-button",    "bottom",    "Click here to search for nodes or edges in the graph", "Next")})
            .then(()=>{return this.tutorial_tip("elem", "#search-input",     "bottom",    "Type here to search node names", "Next")})
            .then(()=>{return this.tutorial_tip("elem", "#search-type",      "bottom",    "Click here to switch between searching for nodes and edges", "Next")})
            .then(()=>{return this.tutorial_tip("elem", "#interactables-button", "bottom", "Click here to access various ways of manipulating the graph", "Next")})
            /*
            .then(()=>{
                this.tutorial_center(0)
                return this.tutorial_tip("elem", "#tree button#tree_up",      "left",    "Click here to expand/collapse the clusters of the graph", "Next")
            })
            .then(()=>{
                this.tutorial_center(1)
                return this.tutorial_tip("elem", "div.filter_container:last",    "bottom",  "Use the provided filters to hide/show a subset of nodes and edges", "Next")
            })
            */
            .then(()=>{
                this.menu.show()
                setTimeout(() => this.menu.show(), 10)  // clicking the "next" button actually closes the menu, so we need to open it again 10ms later.
                return this.tutorial_tip("elem", "div#menu li.dropdown-item:contains('Help')", "right", "For more detailed instructions, click here", "Done")
            })

    }
    async tutorial_center(depth, wait=false) {
        // center the graph and set a tree depth
        this.state.interaction.reset_camera()
        this.state.tree.set_depth(depth)
        if (wait) await utils.sleep(400);
    }
    async tutorial_tip(type, selector, placement, text, button_text) {
        var $element;
        if (type == "node") {  // giving a node key
            let node = selector

            let depth = this.graph.getNodeAttribute(node, "depth")
            await this.tutorial_center(depth, true)

            let attrs = this.graph.getNodeAttributes(node)
            let {x:x, y:y} = this.sigma.graphToViewport({x:attrs.x, y:attrs.y})
            let size = attrs.size
            $element = $(`<div></div>`).css({position: 'absolute', left: x, top: y-size,}).appendTo(this.$root)

        } else {  // targeting an element
            $element = this.$root.find(selector)
            // if element not found or hidden skip it
            if ($element.length == 0 || !$element.is(":visible")) {
                console.log(`Element with ID "${selector}" not found - skipping`)
                return new Promise(resolve => resolve())
            }
        }

        let arrow = true
        if (placement == "none") {
            // set to "top" and disable the arrow
            placement = "top"
            arrow = false
        }

        return new Promise(resolve => {
            let $text = $(`<span>${text}</span>`)
            let $next = $(`<button>${button_text}</button>`).appendTo($text)
            let tooltip = tippy($element[0], {
                content: $text[0],
                placement: placement,
                arrow: arrow,
                allowHTML: true,  // render HTML in content
                interactive: true,  // allow user to click the button inside
                theme: 'tutorial',  // use custom "tutorial" theme defined in graph.css
                animation: 'scale-extreme',  // pop out animation
                maxWidth: 220,
                trigger: 'manual',  // trigger with JS only
                hideOnClick: false,  // don't hide when user clicks away
                appendTo: document.body,  // silence warning about accessibility
            });
            tooltip.show()

            $next.one('click', () => {
                tooltip.hide()
                resolve();
            });
        })
    }

    snapshot() {
        const { width, height } = this.sigma.getDimensions();

        // This pixel ratio is here to deal with retina displays.
        // Indeed, for dimensions W and H, on a retina display, the canvases
        // dimensions actually are 2 * W and 2 * H. Sigma properly deals with it, but
        // we need to adapt here:
        const pixelRatio = window.devicePixelRatio || 1;

        const tmpRoot = document.createElement("DIV");
        tmpRoot.style.width = `${width}px`;
        tmpRoot.style.height = `${height}px`;
        tmpRoot.style.position = "absolute";
        tmpRoot.style.right = "101%";
        tmpRoot.style.bottom = "101%";
        document.body.appendChild(tmpRoot);

        // Instantiate sigma:
        const tmpRenderer = new sigma.Sigma(this.sigma.getGraph(), tmpRoot, this.sigma.getSettings());

        // Copy camera and force to render now, to avoid having to wait the schedule /
        // debounce frame:
        tmpRenderer.getCamera().setState(this.sigma.getCamera().getState());
        tmpRenderer.setCustomBBox(this.sigma.getCustomBBox() || this.sigma.getBBox())
        tmpRenderer.refresh();

        // Create a new canvas, on which the different layers will be drawn:
        const canvas = document.createElement("CANVAS");
        canvas.setAttribute("width", width*pixelRatio + "");
        canvas.setAttribute("height", height*pixelRatio + "");
        const ctx = canvas.getContext("2d")

        // Draw a white background first:
        ctx.fillStyle = "#fff";
        ctx.fillRect(0, 0, width*pixelRatio, height*pixelRatio);

        // For each layer, draw it on our canvas:
        const canvases = tmpRenderer.getCanvases();
        let layers = Object.keys(canvases);
        layers.forEach((id) => {
            ctx.drawImage(canvases[id], 0, 0, width*pixelRatio, height*pixelRatio, 0, 0, width*pixelRatio, height*pixelRatio);
        });

        // Save the canvas as a PNG image:
        canvas.toBlob((blob) => {
            if (blob) utils.download_image(blob, "graph.png");

            // Cleanup:
            tmpRenderer.kill();
            tmpRoot.remove();
            }, "image/png");
        }

    download_graph() {
        utils.download_json(this.state.structure.original_graph_json, "data.json")
    }

    upload_graph() {
        utils.upload_json(
            (data,name) => {  // success
                this.state.plot.import(data)
                //this.$upload_notification.text(`Uploaded File: ${name}`)
                //this.$upload_notification.show()
            },
            (err,name) => {  // error
                this.error("Failed to upload graph.",err)
                //this.$upload_upload_notification.hide()
            }
        )
    }

    // add a tooltip to the given element
    add_tooltip(text, $element, placement='top', delay_show=0, delay_hide=0, theme='') {
        let tooltip = tippy($element[0], {
            content: text,
            placement: placement,
            delay: [delay_show, delay_hide],
            theme: theme,  // use custom theme to be targeted by custom css
            maxWidth: '',  // disable default max width
            allowHTML: true,  // render HTML in content
            hideOnClick: true,  // hide when the user clicks the trigger element
            appendTo: document.body,  // silence warning about accessibility
        });
    }

    display_node_data(ID) {
        // show the data display for the given node ID
        data = this.graph.getNodeAttributes(ID)
        this.data_display()
    }
    display_edge_data(ID) {
        // show the data display for the given edge ID
    }

    // node reducer for rendering temporary states
    node_reducer(node, attrs) {  // return temporary node properties
        return attrs;
    }

    // edge reducer for rendering temporary states
    edge_reducer(edge, attrs) {  // return temporary edge properties
        return attrs;
    }

}


class Menu {
    // Main buttons and side menu

    constructor(ui) {
        this.ui = ui
        this.$root = ui.$root

        this.dropdown = new bootstrap.Dropdown($('button#menu-button')[0], {})

        this.$list = this.$root.find("div#menu ul.dropdown-menu")  // the menu dropdown
        this.$upload_notification = this.$root.find("div.interface div#uploaded_file")  // display uploaded file name

        // buttons
        this.$dropdown_button = $("#menu-button");
        this.$center_button = $("#center-button")
        this.$organize_button = $("#organize-button")
        this.$search_button = $("#search-button")
        this.$interactables_button = $("#interactables-button");

        this.$physics_button = $("#physics-button")
        this.$physics_button_start = this.$physics_button.find("img.start-img")
        this.$physics_button_stop = this.$physics_button.find("img.stop-img")

        this.init()
    }

    init() {
        // button functionality
        // TODO move interface functionality bindings from the interaction object to here
        this.$center_button.on('click', () => this.ui.state.interaction.reset_camera())
        this.$organize_button.on("click", () => this.ui.state.simulation.snap())
        this.$interactables_button.on('click', () => this.ui.interactables.show())
        this.$physics_button.on("click", () => {
            if (this.ui.state.simulation.toggle()) {  // successfully toggled
                this.$physics_button_start.toggle()
                this.$physics_button_stop.toggle()
            }
        })

        // add items to the dropdown
        this.add_item('Download Graph', 'Download current graph JSON data', () => this.ui.download_graph())
        this.add_item('Upload Graph', 'Upload JSON graph data file', () => this.ui.upload_graph())
        this.add_item('Screenshot', 'Take a screenshot of the graph', () => this.ui.snapshot())
        this.add_divider()
        this.add_item('Settings', 'Open the settings menu', () => this.ui.settings_menu.show())
        this.add_item('Help', 'Open the help menu', () => this.ui.help.show())
    }

    // add an action item to the menu
    add_item(label, description, callback) {
        let $item = $(`<li class="dropdown-item">${label}</li>`).appendTo(this.$list)
        this.ui.add_tooltip(description, $item, "right", 500, 0)
        $item.on('click', callback)
    }

    add_divider() {
        this.$list.append('<li><hr class="dropdown-divider"></li>')
    }

    show() {
        this.dropdown.show()
    }
    hide() {
        this.dropdown.hide()
    }
    toggle() {
        this.dropdown.toggle()
    }
}


class Settings {
    // Settings Menu
    constructor(ui) {
        this.ui = ui
        this.$root = ui.$root
        this.settings = ui.settings

        this.$container = this.$root.find("#settings")
        this.offcanvas;  // offcanvas object
        this.init()
    }

    init() {
        this.offcanvas = new bootstrap.Offcanvas(this.$container[0])

        this.add_checkbox('Show un-selected nodes', 'show_unfocused_nodes', true, "When a node is selected, other nodes not directly connected to it will be visible but slightly desaturated.")
        this.add_checkbox('Show out-of-range nodes', 'show_out_of_range_nodes', false, "When nodes are removed by a filter, keep them faintly visible.")
        //this.add_checkbox('Advanced data menu', 'advanced_data', false, "In the right-click menu, show all attributes of the node or edge. Mostly for debugging purposes.")
        this.add_checkbox('Smooth zooming', 'animate_zoom', true, "Enables smooth zooming transitions.")
    }

    // add a boolean setting with a checkbox
    add_checkbox(label, setting, default_value, description) {
        let body = this.$container.find(".offcanvas-body")  // modal body
        let $setting = $(`<div class="form-check form-switch"></div>`).appendTo(body)  // wrapping Bootstrap div
        let $checkbox = $(`<input class="form-check-input" type="checkbox" role="switch" id="${setting}">`).appendTo($setting)  // checkbox Bootstrap switch element
        let $label = $(`<label class="form-check-label" for="${setting}">${label}</label>`).appendTo($setting)  // Bootstrap label
        this.ui.add_tooltip(description, $label, "right", 500, 0)

        if (this.settings[setting] === undefined) {  // if this setting hasn't been given
            this.settings[setting] = default_value
        }

        $checkbox[0].checked = this.settings[setting]  // initial value
        $checkbox.on('change', (event) => {
            this.settings[setting] = $checkbox[0].checked  // change setting to checkbox value
            this.ui.sigma.refresh()  // re-render everything
        })

    }

    show() {
        this.offcanvas.show()
    }
    hide() {
        this.offcanvas.hide()
    }
    toggle() {
        this.offcanvas.toggle()
    }
}


class Help {
    // Help menu

    constructor (ui) {
        this.ui = ui
        this.$root = ui.$root

        // items on main graph page
        this.$help = this.$root.find("div#help")
        this.offcanvas;  // Bootstrap offcanvas object

        // from help.html
        this.$tutorial_button;  // button to trigger the tutorial

        // load help.html into the container
        this.$help.load("src/html/help.html", () => {
            this.init()  // then initialize
        })
    }

    init() {
        this.offcanvas = new bootstrap.Offcanvas($('div#help-menu')[0])
        this.$tutorial_button = this.$root.find('button#tutorial-button')  // button to trigger the tutorial
        this.$tutorial_button.on('click', () => this.ui.tutorial())

        // style all lists in help div with bootstrap
        this.$help.find('ul').addClass("list-group list-group-flush")
        this.$help.find('li').addClass("list-group-item")

        // wrap all images in special divs with class "display" to be targeted by css
        let $images = this.$help.find("div.page li img")  // images within instruction paragraphs in each section

        for (let img of $images) {
            let $p = $(img).parent()  // parent paragraph of the image
            this.ui.add_tooltip(img, $p, "right", 100, 0, 'help-gifs')
        }

        // different visible tabs for different sections
        var $tabs = this.$help.find("div.nav-tabs")  // div to contain all tabs
        let n = 0;  // tab number
        for (let page of this.$help.find("div.page")) {  // for each tab section
            let $page = $(page)
            let page_id = "help-page-"+n  // unique page ID
            let page_name = $page.attr("name") || "???" // name of page

            $page.attr('id', page_id)
            $page.addClass('tab-pane fade')
            $page.attr('role', 'tabpanel')

            let $tab = $(`<button data-bs-target="#${page_id}" class="nav-link" data-bs-toggle="tab" type="button" role="tab">${page_name}</button>`).appendTo($tabs)
            n += 1
        }

        this.$help.find("button.nav-link").first().addClass("active")  // set first tab to active
        this.$help.find("div.tab-pane").first().addClass("show active")  // set first page to active
    }

    show() {
        this.offcanvas.show()
    }
    hide() {
        this.offcanvas.hide()
    }
    toggle() {
        this.offcanvas.toggle()
    }
}


class Interactables {
    // Contains the filters and cluster tree interactables
    constructor(ui) {
        this.ui = ui
        this.offcanvas;  // bootstrap offcanvas object
        this.init()
    }

    init() {
        this.offcanvas = new bootstrap.Offcanvas($('div#interactables')[0])
    }
    show() {
        this.offcanvas.show()
    }
    hide() {
        this.offcanvas.hide()
    }
    toggle() {
        this.offcanvas.toggle()
    }
}


class RightClickMenu {
    // Right-click menu
    constructor(ui) {
        this.ui = ui
        this.$root = ui.$root

        // jQuery elements
        this.$node_dropdown = $('div#node-menu')
        this.$edge_dropdown = $('div#edge-menu')
        this.$node_list = this.$root.find("div#node-menu ul.dropdown-menu")
        this.$edge_list = this.$root.find("div#edge-menu ul.dropdown-menu")

        // Bootstrap dropdown objects
        this.node_dropdown = new bootstrap.Dropdown($('div#node-menu-toggle')[0], {})
        this.edge_dropdown = new bootstrap.Dropdown($('div#edge-menu-toggle')[0], {})

        this.current_id; // ID of the current node/edge selected
        this.has_node_items = false  // whether items have been added
        this.has_edge_items = false
        this.init()
    }

    init() {
        // In debug mode, add an option to view all node/edge attributes
        if (this.ui.state.settings.debug) {
            this.add_node_item("View Data", "", (id) => {
                this.ui.custom_modal.show("Data", "", "", 1, (container) => {
                    let attrs = this.ui.graph.getNodeAttributes(id)
                    this.ui.state.structure.generate_data_html($(container), attrs)
                })
            })
            this.add_edge_item("View Data", "", (id) => {
                this.ui.custom_modal.show("Data", "", "", 1, (container) => {
                    let attrs = this.ui.graph.getEdgeAttributes(id)
                    this.ui.state.structure.generate_data_html($(container), attrs)
                })
            })
        }
        // add default items to the dropdown
        //this.add_node_item('Test node menu', 'Test Node Description', () => {console.log("Test Node Item")})
        //this.add_edge_item('EDGE TEST', 'Test Edge Description', () => {console.log("TEST EDGE ITEM")})
    }

    // add an action item to the node menu
    add_node_item(label, description, callback) {
        // callback must take as input the node data
        let $item = $(`<li class="dropdown-item">${label}</li>`).appendTo(this.$node_list)
        if (description) this.ui.add_tooltip(description, $item, "right", 500, 0)
        this.has_node_items = true
        $item.on('click', () => {
            callback(this.current_id)
        })
    }

    // add an action item to the edge menu
    add_edge_item(label, description, callback) {
        // callback must take as input the edge data
        let $item = $(`<li class="dropdown-item">${label}</li>`).appendTo(this.$edge_list)
        if (description) this.ui.add_tooltip(description, $item, "right", 500, 0)
        this.has_edge_items = true
        $item.on('click', () => {
            callback(this.current_id)
        })
    }

    add_divider() {
        this.$list.append('<li><hr class="dropdown-divider"></li>')
    }

    show_node(id, x, y) {
        // show the dropdown for the given node ID at position
        if (!this.has_node_items) return;
        this.current_id = id
        this.$node_dropdown.css({left: x + "px", top: y + "px"});  // set position from click event position
        this.hide()  // hide all dropdowns first
        this.node_dropdown.show()
    }

    show_edge(id, x, y) {
        if (!this.has_edge_items) return;
        this.current_id = id
        this.$edge_dropdown.css({"left": x + "px", "top": y + "px"});  // set position based
        this.hide()  // hide all dropdown first
        this.edge_dropdown.show()
    }
    hide() {
        this.node_dropdown.hide()
        this.edge_dropdown.hide()
    }
}


class Alert {
    // Error popup
    constructor (ui) {
        this.ui = ui
        this.modal;  // bootstrap modal object

        this.$type;    // the modal type div
        this.$header;  // the modal header div
        this.$body;    // the modal body div

        this.init()
    }

    init() {
        this.modal = new bootstrap.Modal($('div#error')[0], {
            backdrop: 'static',  // clicking outside doesn't close it
            keyboard: false,  // pressing esc key doesn't close it
        })
        this.$type = $('div#error div.modal-header span#error-type')
        this.$header = $('div#error div.modal-header span#error-header')
        this.$body = $('div#error div.modal-body p#error-message')
    }

    error(header, message) {
        this.$type.html("Error:").addClass('text-danger')  // bootstrap danger class
        this.$header.html(header).addClass('text-danger')  // bootstrap danger class
        this.$body.html(message)
        console.error(header, message)
        this.modal.show()
    }

    warning(header, message) {
        this.$type.html("Warning:").addClass('text-warning')  // bootstrap danger class
        this.$header.html(header).addClass('text-warning')  // bootstrap danger class
        this.$body.html(message)
        console.warn(header, message)
        this.modal.show()
    }
}


class DataDisplay {
    // Popup display to show when clicking on a node/edge
    constructor (ui) {
        this.ui = ui
        this.collapse;  // Bootstrap collapse object
        this.$title;    // card title element (unused atm)
        this.$tabs;     // tabs  element
        this.$body;     // card body

        // callbacks set by host to manipulate display content
        this.node_callback;
        this.edge_callback;

        // size options for the node/edge displays
        this.node_height = "20em";
        this.node_width = "30em";
        this.edge_height = "20em";
        this.edge_width = "30em";

        this.init();
    }

    init() {
        this.collapse = new bootstrap.Collapse($('#data-display'), {
            toggle: false  // don't open when created
        })
        this.$title = $('#data-display .card-title')
        this.$tabs = $('#data-display div.nav-tabs')
        this.$body = $('#data-display div.card-body')
    }

    show_nodes(ids) {
        // show data display for each node in the given list of ids
        if (!this.node_callback) return;  // no callback provided by host
        this.show(NODE, ids)
    }

    show_edges(ids) {
        // show data display for each edge in the given list of ids
        if (!this.edge_callback) return;  // no callback provided by host
        this.show(EDGE, ids)
    }

    show(type, ids) {
        // given
        //  defining the node/edge data, html, and source and target data if an edge
        if (ids.length == 0) {  // no ids given
            this.hide()
            return
        }

        let returned;  // value returned from the callback

        this.clear()
        // If only 1 tab given, don't show tabs
        if (ids.length == 1) {
            returned = this.set_content(type, this.$body, ids[0])  // pass DOM object to callback
        }

        // show tabs when more than 1 page is given
        else {
            let n = 0  // unique tab index
            for (let id of ids) {
                let name = ''
                if (type == NODE) name = this.graph.getNodeAttribute(id, 'label');
                if (type == EDGE) name = this.graph.getEdgeAttribute(id, 'label');

                if (name.length > 15) name = name.substr(0, 12) + "..."  // truncate tab label
                $(`<button class="nav-link" type="button" role="tab" data-bs-toggle="tab" data-bs-target="#tab-${n}">${name}</button>`).appendTo(this.$tabs)
                let tab_pane = $(`<div class="tab-pane fade" role="tabpanel" id="tab-${n}"></div>`).appendTo(this.$body)
                returned = this.set_content(type, tab_pane, id)  // pass DOM object to callback
                n += 1
            }
            this.$tabs.find("button.nav-link").first().addClass("active")  // set first tab to active
            this.$body.find("div.tab-pane").first().addClass("show active")  // set first page to active
        }

        if (returned === false) this.collapse.hide()  // hide if returns false
        else this.collapse.show()  // show if anything else

    }

    // set the content of the display using the host's callback
    set_content(type, $container, id) {
        if (type == NODE) {
            this.set_size(this.node_height, this.node_width)
            return this.node_callback($container[0], id)
        } else {  // edge
            this.set_size(this.edge_height, this.edge_width)
            return this.edge_callback($container[0], id)
        }
    }

    // set the size based on the given sizing option
    set_size(height, width) {
        //TODO: plan to allow various sizing methods like "stretch" or whatever
        //TODO: maybe also add option for min/max values?

        // don't allow percentages in height/width
        //TODO: can we fix this? The problem with percentages is that setting card-body width x% makes the card take up 100% of the screen width for some reason.
        // And if you try to set the card itself to x%, it makes the outer interface div take up 100% screen width, which interrupts clicks in that part of the screen.
        // Also messing with the collapse element's height screws up the bootstrap animation.
        if (height.includes('%') || width.includes('%')) {
            this.ui.warning("Could not properly set node/edge display height/width.", "Percentage values not allowed.")
        }
        height.replace('%', 'em')
        width.replace('%', 'em')
        this.$body.css('height', height)
        this.$body.css('width', width)
    }

    hide() {
        this.collapse.hide()
    }
    toggle() {
        // show/hide the LAST instance displayed. Does NOT display new data.
        this.collapse.toggle()
    }
    clear() {
        // clear display content
        this.$tabs.empty()
        this.$body.empty()
    }

    // set the callbacks and sizing methods
    set_node_display(callback, height, width) {
        this.node_callback = callback
        if (height) this.node_height = height
        if (width) this.node_width = width
    }
    set_edge_display(callback, height, width) {
        this.edge_callback = callback
        if (height) this.edge_height = height
        if (width) this.edge_width = width
    }
}


class CustomPopup {
    // Popup display to show arbitrary custom HTML.
    // Call set_content() to define what's inside it.

    constructor (ui) {
        this.ui = ui
        this.collapse;  // Bootstrap collapse object
        this.$title;    // card title element (unused atm)
        this.$tabs;     // tabs element
        this.$body;     // card body
        this.$button;   // toggle button

        // defaults
        this.height = "20em"
        this.width = "30em"
        this.label =  ''
        this.callback;

        this.init();
    }

    init() {
        this.$collapse = $('#custom-popup')
        this.collapse = new bootstrap.Collapse(this.$collapse, {
            toggle: false  // Closed by default
        })
        this.$title = $('#custom-popup .card-title')
        this.$tabs = $('#custom-popup div.nav-tabs')
        this.$body = $('#custom-popup div.card-body')
        this.$close = $('#custom-popup button.btn-close')
        this.$button = $('button#custom-popup-button')

        // hide the button until set_content() is called
        this.$button.hide()

        // hide button on show
        this.$collapse[0].addEventListener('show.bs.collapse', () => {
          this.$button.hide()
        })

        // show button after collapsed
        this.$collapse[0].addEventListener('hidden.bs.collapse', () => {
          this.$button.show()
        })

        // bind toggle to button
        this.$button.on('click', () => {
            this.toggle()
        })
        this.$close.on('click', () => {
            this.hide()
        })

    }

    // public method to set the content
    set_content(callback, label, height, width) {
        // saving everything as member variables doesn't actually do anything here but might be useful later
        this.callback = callback
        if (label) this.label = label
        if (height) this.height = height
        if (width) this.width = width

        // actually set the content
        this.$title.html(label)
        this.$button.append(label)
        this.$button.show()  // show the button
        this.callback(this.$body[0])  // call the callback to set the content
        this.set_size(height, width)
    }

    // set the size based on the given sizing option
    set_size(height, width) {
        if (!height) height = this.height  // defaults
        if (!width) width = this.width
        //TODO: plan to allow various sizing methods like "stretch" or whatever
        //TODO: maybe also add option for min/max values?

        // don't allow percentages in height/width
        //TODO: can we fix this? The problem with percentages is that setting card-body width x% makes the card take up 100% of the screen width for some reason.
        // And if you try to set the card itself to x%, it makes the outer interface div take up 100% screen width, which interrupts clicks in that part of the screen.
        // Also messing with the collapse element's height screws up the bootstrap animation.
        if (height?.includes('%') || width?.includes('%')) {
            this.ui.warning("Could not properly set node/edge display height/width.", "Percentage values not allowed.")
        }
        if (height) {
            height.replace('%', 'em')
            this.$body.css('height', height)
        }
        if (width) {
            width.replace('%', 'em')
            this.$body.css('width', width)
        }
    }

    show() {
        this.collapse.show()
    }
    hide() {
        this.collapse.hide()
    }
    toggle() {
        // show/hide the LAST instance displayed. Does NOT display new data.
        this.collapse.toggle()
    }
    clear() {
        // clear display content
        this.$tabs.empty()
        this.$body.empty()
    }
}


class CustomModal {
    // Modal display to show arbitrary custom HTML

    constructor (ui) {
        this.ui = ui
        this.modal;  // Bootstrap collapse object
        this.$dialog;   // dialog element
        this.$title;    // title element
        this.$body;     // modal body
        this.$footer;   // modal footer

        this.init();
    }

    init() {
        this.modal = new bootstrap.Modal($('div#custom-modal')[0], {
            backdrop: true,  // dimmed backdrop
            keyboard: true,  // pressing esc key will close it
        })
        this.$dialog = $('div#custom-modal .modal-dialog')
        this.$title = this.$dialog.find('.modal-title')
        this.$body = this.$dialog.find('.modal-body')
        this.$footer = this.$dialog.find('.modal-footer')
    }

    show(title, body, footer, size=1, callback) {
        let size_class = ""   // default bootstrap modal size
        if (size == 0) size_class = "modal-sm"
        else if (size == 2) size_class = "modal-lg"
        else if (size == 3) size_class = "modal-xl"

        this.clear()
        this.$title.html(title)
        this.$body.html(body)
        this.$footer.html(footer)
        this.$dialog.addClass(size_class)
        this.modal.show()
        if (callback !== undefined) callback(this.$body[0])  // pass in the body DOM object
    }
    hide() {
        this.modal.hide()
    }
    toggle() {
        // show/hide the LAST instance displayed. Does NOT display new data.
        this.modal.toggle()
    }
    clear() {
        // clear display content
        this.$title.empty()
        this.$body.empty()
        this.$footer.empty()
        this.$dialog.removeClass('modal-sm modal-lg modal-xl')
    }
}
