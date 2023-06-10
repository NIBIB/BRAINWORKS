import * as $ from "jquery";
import DOMPurify from "dompurify";
const NA = "<span class='fw-lighter fst-italic'>Unavailable</span>";

// show the loading div
function start_loading() {
  $("div#popup-loading").show();
}
function stop_loading() {
  $("div#popup-loading").hide();
}

function display_percentile(num) {
  // cap a percentile with 1 decimal of precision
  return Math.max(Math.min(num, 99.9), 0.1).toFixed(1).toLocaleString("en-US");
}

// show the tutorial modal
function tutorial_prompt() {
  $(document).ready(function () {
    let $accept = $("#accept-tutorial");
    let $modal = $("#accept-tutorial-modal");
    // let modal = UIkit.modal($modal);
    // modal.show();
    // $accept.click((event) => {
    //   // when modal continue button is clicked
    //   graph.tutorial(); // trigger the tutorial
    // });
  });
}

// Embed the given zip file data in the page to be downloaded
function set_zip(data) {
  $(document).ready(function () {
    let $export_data = $("#export-data"); // where to embed the data
    let encoded = "data:application/octet-stream;base64," + data;
    $export_data[0].href = encoded;
  });
}

// GraphAPI Callbacks

// create a bootstrap-styled link that opens in a new window
function link(text, url, _class) {
  if (_class == undefined) _class = "";
  _class = _class + " text-decoration-none";
  _class = _class.trim();
  return `<a href=${url} target="_blank" rel="noreferrer noopener" class="${_class}">${text}</a>`;
}

// get a bootstrap-styled iframe that displays the paper_triples page
function paper_info_iframe(pmid) {
  let url = `/paper-info?pmid=${pmid}`;
  return $(`<div class="ratio ratio-1x1"><iframe src=${url}></iframe></div>`);
}

// Generate HTML for a section with node statistics
function node_statistics(node) {
  return `
    <hr>
    <span class="fw-bold">Node Statistics</span>
    <p>
        Degree: ${node.data.degree?.toLocaleString("en-US")} <br>
        Degree Centrality: ${node.data.degree_centrality?.toLocaleString(
          "en-US"
        )} <br>
        Closeness Centrality: ${node.data.closeness_centrality?.toLocaleString(
          "en-US"
        )} <br>
    </p>
    `;
  // Eccentricity: ${node.data.eccentricity.toLocaleString("en-US")} <br>
  // Eigenvector Centrality: ${node.data.eigenvector_centrality?.toLocaleString("en-US")} <br>
}

// Generate HTML for a section with edge statistics
function edge_statistics(edge) {
  return `
    <hr>
    <span class="fw-bold">Edge Statistics</span>
    <p>
        Simmelian Strength: ${edge.data.simmelian_strength.toLocaleString(
          "en-US"
        )} <br>
    </p>
    `;
}

// configure the Graph API
export function configure_graph(data, representation) {
  // data is the entire graph data to be given to the graph.
  // representation is the string that is the data representation type used. "paper_citations" or "triples"

  // Used to track how many times requests are made to add nodes to the graph
  window.extra_map = {};

  let ready_callback; // function to call when graphAPI is ready
  let gravity = 1;
  if (representation == "paper_citations") {
    ready_callback = citation_configuration;
  } else if (representation == "triples") {
    ready_callback = triples_configuration;
  } else if (representation == "topic_co_occurrences") {
    ready_callback = co_occurrences_configuration;
    gravity = 0.2;
  }

  // initialize graph object
  window.graph = new window.Graph(data, {
    gravity: gravity,
  });

  // add help menu trigger
  window.graph.ready(() => {
    // $("#trigger-help").on("click", () => window.graph.help()); // bind nav bar help button to the GraphAPI help menu
    ready_callback(window.graph);
  });
}

// Triples graph
function triples_configuration(graph) {
  window.graph.node_display(triples_node_data, "30em", "30em");
  window.graph.edge_display(triples_edge_data, "30em", "30em");
  window.graph.popup_display(triples_legend, "Legend", "30em", "30em");
  //graph.add_node_menu_item("Add Connections", "Search for more connections to this topic", add_topic_connections)
}

function triples_node_data(container, node) {
  let html = `<h4>${node.label}</h4>`;
  if (node.tree) {
    html += "<p class='fst-italic'>(double-click to expand)</p>";
  } else {
    var time = new Date(node.data.time * 1000); // earliest date
    let topics = [];
    let definitions = [];
    for (let [key, val] of Object.entries(node.data)) {
      if (val && key.toLowerCase().includes("topic-")) {
        topics.push(val);
      }
      if (val && key.toLowerCase().includes("definition-")) {
        definitions.push(val);
      }
    }

    let def_html = "";
    for (let i = 0; i < topics.length; i++) {
      let t = topics[i];
      let d = definitions[i] || NA;
      def_html += `<p><span class="fw-bold">${t}:</span> <span>${d}</span></p>`;
    }

    html += `
            <p>
                Topics: ${topics.join(", ")} <br>
                Earliest Date: ${time.toUTCString()}
            </p>
            ${node_statistics(node)}
            <hr>
            ${def_html}
        `;
  }

  $(container).html(html); // set html of the container
}

function triples_edge_data(container, edge, source, target) {
  if (edge.tree) {
    // TODO display list of papers
    return false; // don't show the popup
  }

  let time;
  if (edge.data.time) time = new Date(edge.data.time * 1000).toUTCString();
  else time = NA;
  let title = edge.data.title;
  if (edge.data.doi) title = link(edge.data.title, edge.data.doi);

  let abstract = edge.data.abstract || NA;
  // Highlight the sentence in the abstract where this triple came from
  if (edge.data.abstract) {
    let highlighted = "";
    let start = edge.data.start_char;
    let end = edge.data.end_char;
    highlighted = abstract.slice(0, start);
    highlighted += `<mark>${abstract.slice(start, end)}</mark>`;
    highlighted += abstract.slice(end, abstract.length);
    abstract = highlighted;
  }

  let html = `
        <p>
            <span class="fw-bold">Finding: </span>"...${
              edge.data.triple
            }..." <br>
            <hr>
            <span class="fw-bold">Article:</span> ${title} <br>
            <span class="fw-bold">Published:</span> ${time} <br>
            <span class="fw-bold">PMID:</span> ${edge.data.pmid} <br>
            <span class="fw-bold">Journal:</span> ${
              edge.data.journal_title
            } <br>
            <span class="fw-bold">Citations:</span> ${edge.data.citations} <br>
            <span class="fw-bold">Authors:</span> ${edge.data.authors} <br>
        </p>
        ${edge_statistics(edge)}
        <hr>
        <span class="fw-bold">Abstract:</span>
        <p class="fs-6">${abstract}</p>
    `;

  $(container).html(html); // set html of container

  // trigger center modal with triple display on button click
  $(container)
    .find(".view-triples")
    .click(() => {
      show_triples_popup(edge, source, target);
    });
}

function show_triples_popup(data, source, target) {
  let $iframe = paper_info_iframe(data.data.pmid);
  window.graph.center_display("", "", "", 3, (container) => {
    // trigger the graphAPI center display
    $(container).append($iframe);
  });
}

function triples_legend(container) {
  $(container).parent().parent().prev().click()  // click the legend button
  let umls_link = link(
    "UMLS",
    "https://www.nlm.nih.gov/research/umls/index.html"
  );

  $(container).html(`
        <h4 class="fw-bold">Nodes:</h4>
        <ul>
            <li>Nodes represent noun-phrases extracted from scientific abstracts related to your search terms.</li>
            <li>Node colors differentiate topical clusters.</li>
            <li>Node size corresponds to the number of attached edges.</li>
            <li>Click a node to see the ${umls_link} concepts and definitions within the corresponding noun phrase.</li>
        </ul>
        <h4 class="fw-bold">Edges:</h4>
        <ul>
            <li>Edges represent relationships extracted from scientific abstracts that connect two noun-phrases.</li>
            <li>Edge thickness corresponds to the number of citations that paper has.</li>
            <li>Click an edge to view the scientific abstract the relationship was extracted from.</li>
            <li>Edges are colored according to the type of relationship:<br>
                <span style="color: blue;">Blue = Positive</span><br>
                <span style="color: red;">Red = Negative</span><br>
                <span style="color: black;">Black = Associative</span>
            </li>
        </ul>
    `);
}

// Citation graph
function citation_configuration(graph) {
  window.graph.node_display(citations_node_data, "30em", "30em");
  window.graph.popup_display(citations_legend, "Legend");
}

function citations_node_data(container, node) {
  let title = node.data.title || NA;
  if (node.data.doi) title = link(node.data.title, node.data.doi);

  let time;
  if (node.data.time) time = new Date(node.data.time * 1000).toUTCString();
  else time = NA;

  let html = `
    <p>${title}</p><hr>
    <p>
        <span class="fw-bold">Published:</span> ${time}<br>
        <span class="fw-bold">Journal:</span> ${
          node.data.journal_title || NA
        }<br>
        <span class="fw-bold">Authors:</span> ${node.data.authors || NA}<br>
    </p>
    ${node_statistics(node)}
    <hr>
    <span class="fw-bold">Abstract:</span>
    <p>${node.data.abstract || NA}</p>
    `;
  $(container).html(html);
}

function citations_edge_data(container, edge) {}

function citations_legend(container) {
  $(container).parent().parent().prev().click()  // click the legend button
  $(container).html(`
        <h4 class="fw-bold">Nodes:</h4>
        <ul>
            <li>Each <span style="color: red;">Red</span> node is a published paper relating to your search terms</li>
            <li>Each <span style="color: orange;">Orange</span> node is a published paper that cites any of the papers you searched for</li>
            <li>Click a node to view the publication information.</li>
        </ul>
        <h4 class="fw- bold">Edges:</h4>
        <ul>
            <li>Each edge represents a citation between papers.</li>
        </ul>
        `);
}

// Topic Co-occurrences graph
function co_occurrences_configuration(graph) {
  window.graph.node_display(topic_co_occurrences_node_data, "30em", "30em");
  window.graph.edge_display(topic_co_occurrences_edge_data, "30em", "30em");
  window.graph.popup_display(
    topic_co_occurrences_legend,
    "Legend",
    "30em",
    "30em"
  );
  window.graph.add_node_menu_item(
    "See More",
    "Search for more connections to this topic",
    add_co_occurrence_connections
  );
}

function topic_co_occurrences_node_data(container, node) {
  let total = node.data.total.toLocaleString("en-US");
  let perc = display_percentile(node.data.percentile)
  let cat = node.data.category
  let definition = node.data.definition || NA;
  let start_date = node.data.start_date
  let end_date = node.data.end_date

  $(container).html(`
        <h4>${node.label}</h4>
        <span class="fw-bold">Category:</span> ${cat}<br>
        <p>
          <hr>
          From ${start_date} - ${end_date}, this topic appeared <span class="fw-bold">${total}</span> times, which is more than
          approximately <span class="fw-bold">${perc}%</span> of all topics.
          <hr>
          <span class="fw-bold">Definition:</span><br>
          ${definition}
          ${node_statistics(node)}
        </p>
    `);

  // trigger center modal when clicked
  $(container)
    .find("#paper-list-modal")
    .click(() => {
      paper_list_button(node);
    });

  // TODO eventually show a line/bar chart of how frequently this topic occurred in papers over time.
}

function topic_co_occurrences_edge_data(container, edge, source, target) {
  // TODO: eventually display a line chart here to show the change in co-occurrences over time
  // Right now we only calculate this at two points in time, but when we add more this will be useful.
  let total = (edge.data.total).toLocaleString("en-US");
  let freq_perc = display_percentile(edge.data.frequency_percentile)
  let change_prop = Math.abs(edge.data.delta.toFixed(1)).toLocaleString("en-US");
  let change_perc = display_percentile(edge.data.delta_percentile)
  let change_word = edge.data.delta > 0 ? "increased" : "decreased"
  let start_date = edge.data.start_date
  let end_date = edge.data.end_date

  $(container).html(`
        <h4>
            ${source.label} <br>
            and <br>
            ${target.label}
        </h4>
        <p>
            <hr>
            From ${start_date} - ${end_date}, this pair of topics appeared together in <span class="fw-bold">${total}</span> publications,
            which is more than <span class="fw-bold">${freq_perc}%</span> of all topic pairs. Over this time period, the frequency of this topic pair
            has <span class="fw-bold">${change_word}</span> by <span class="fw-bold">${change_prop}%</span>,
            which is more than <span class="fw-bold">${change_perc}%</span> of all topic pairs.
        </p>
    `);

  // trigger center modal when clicked
  // $(container)
  //   .find("#paper-list-modal")
  //   .click(() => {
  //     paper_list_button(edge, source, target);
  //   });
}

function paper_list_button(data, source, target) {
  let topics = [];
  if (source && target) {
    // edge
    topics = [source.label, target.label];
  } else {
    // node
    topics = [data.label];
  }

  let query_string = "?";
  for (let topic of topics) {
    query_string = query_string + "&topics=" + topic;
  }

  start_loading();
  $.ajax({
    method: "GET",
    url: "/quick_search_papers_by_mesh_topic" + query_string,
    dataType: "json",
    success: (data) => {
      show_paper_list(data, topics);
      stop_loading();
    },
    error: (e) => {
      console.log("Failed to request paper list");
      stop_loading();
    },
  });
}

function show_paper_list(paper_list, topics) {
  let html = `
        <table class="table">
        <tr>
            <th>Cited</th>
            <th>Title</th>
            <th>Triples</th>
        </tr>
    `;
  for (let paper of paper_list) {
    let title = paper.title;
    if (paper.doi) title = link(paper.title, paper.doi);

    let triple_button = NA;
    if (paper.triple)
      triple_button = `<a class="btn btn-sm btn-success" data-pmid="${paper.pmid}">View Triples</a>`;

    html += `
        <tr>
            <td>${paper.citations || 0}</td>
            <td class="fw-bold">${title}</td>
            <td>${triple_button}</td>
        </tr>
        `;
  }
  html += "</table>";

  for (let i = 0; i < topics.length; i++) {
    topics[i] = `"${topics[i]}"`;
  }
  let modal_title = "Publications on topics: " + topics.join(", ");

  // trigger the graphAPI center display
  window.graph.center_display(modal_title, html, "", 2, (container) => {
    let $buttons = $(container).find("a.btn[data-pmid]");
    for (let button of $buttons) {
      // get all buttons with a pmid data attribute
      let $button = $(button);
      let pmid = $button.data("pmid");
      $button.click(() => {
        // on click, call the modal containing the Paper Info iframe.
        let $iframe = paper_info_iframe(pmid);
        start_loading();
        $iframe.find("iframe").on("load", stop_loading);
        window.graph.center_display("", "", "", 3, (container) => {
          let $container = $(container);
          $iframe.appendTo($container);
        });
      });
    }
  });
}

function topic_co_occurrences_legend(container) {
  $(container).parent().parent().prev().click()  // click the legend button
  let mesh_link = link(
    "Medical Subject Headings (MeSH)",
    "https://www.nlm.nih.gov/mesh/meshhome.html"
  );

  const dirtyHTML = `
        <p>
            This plot compares research topic connectivity over recent months.
            The topics shown are ${mesh_link} developed by the NIH.
        </p>
        <h4 class="fw-bold">Nodes:</h4>
        <ul>
            <li>Each node represents a research topic.</li>
            <li>Node size corresponds to the total number of times that topic occurred in the literature in recent months.</li>
            <li>Node color corresponds to the high-level MeSH term category:<br>
                <span style="color: #a6d75b;">Diseases</span>,
                <span style="color: #24a824;">Organisms</span>,
                <span style="color: #2e9e84;">Anatomy</span>,
                <span style="color: #54bebe;">Humanities</span>,
                <span style="color: #007399;">Human Groups</span>,
                <span style="color: #005df9;">Social Phenomena</span>,
                <span style="color: #1a8cdd;">Psychiatry and Psychology</span>,
                <span style="color: #8184fb;">Phenomena and Processes</span>,
                <span style="color: #766aaf;">Techniques and Equipment</span>,
                <span style="color: #ab3da9;">Chemicals and Drugs</span>,
                <span style="color: #d65c81;">Health Care</span>,
                <span style="color: #fe5a01;">Information Science</span>,
                <span style="color: #eeb711;">Technology, Industry, and Agriculture</span>,
                <span style="color: #ece000;">Disciplines and Occupations</span>,
                <span style="color: #814a0c;">Geographicals</span>,
                <span style="color: #503f3f;">Other</span>.
            </li>
        </ul>
        <h4 class="fw-bold">Edges:</h4>
        <ul>
            <li>Each edge means that the connected topics both appeared in the same published papers.</li>
            <li>Edge thickness corresponds to how frequently this co-occurrence was found in recent months, relative to other edges.</li>
            <li>Edges are colored by whether this co-occurrence increased or decreased in recent months, relative to other edges.<br>
                <span style="color: #5370c6;">Blue = Increase</span><br>
                <span style="color: #cf1717";">Red = Decrease</span><br>
                <span style="color: grey;">Grey = Relatively Little Change</span>
            </li>
        </ul>
    `;
  const sanitize = DOMPurify.sanitize(dirtyHTML);
  $(container).html(sanitize);
}

function add_co_occurrence_connections(node) {
  // Add more connections to this node
  let n = 10; // how many to add
  let start = window.extra_map[node.key] || 0; // gets starting index
  window.extra_map[node.key] = start + n; // increment
  console.log(node.key)

  $.ajax({
    method: "GET",
    url: `/graph/command/extra_topic_co_occurrences?topic=${node.label}&start=${start}&num=${n}`,
    dataType: "json",
    success: (data) => {
      if (data.nodes.length) {
        // spread out the new nodes around the selected one
        let positions = [];
        let angle = (2 * Math.PI) / data.nodes.length; // angle to spread out by
        let i = 0;
        for (let new_node of data.nodes) {
          new_node.x = node.x + node.size * Math.cos(angle * i);
          new_node.y = node.y + node.size * Math.sin(angle * i);
          i++;
        }
      }

      if (data.nodes.length || data.edges.length) {
        window.graph.add(data);
      } else {
        window.graph.warning(
          "No data found",
          "No more co-occurrences were found within your search constraints.."
        );
      }
    },
    error: (e) => {
      window.graph.warning("Error retrieving co-occurrence data", e);
    },
  });
}
