var header_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
var unique_id = 0  // counter for unique ID assignment

// recursive function to construct the content navigation on the side of the page.
function construct_nav($root, $nav, level) {
    // first time called
    if (level === undefined) {
        for (let tag of header_tags) {  // look for highest level h tag
            let $children = $root.find(tag)
            if ($children.length == 0) continue;
            let $sub_nav = $(`<ul class="uk-nav uk-nav-parent-icon" uk-nav="multiple: true"></ul>`).appendTo($nav)  // create parent list for children
            for (let child of $children) {  // call recursively on each of the highest level h tags
                construct_nav($(child), $sub_nav, 0)
            }
            return;
        }
    }

    // if called recursively

    // assign a unique ID to the root
    $root.prop('id', unique_id)

    // turn into nav list element and link to the root
    let $li = $(`<li><a href="#${unique_id}" uk-scroll="offset: 80">${$root.html()}</a></li>`).appendTo($nav)
    unique_id += 1

    let tag = header_tags[level]
    let parents = header_tags.slice(0, level+1)
    let $children = $root.nextUntil(parents.join(', '), ':header')  // all smaller or equal h siblings until next larger tag

    if ($children.length > 0) {
        let $sub_nav = $(`<ul class="uk-nav-sub uk-nav-parent-icon" uk-nav></ul>`).appendTo($li)  // add a sub-list for these children
        $li.addClass("uk-parent")  // allow collapsing of parents
        let child_level;  // current level of child element
        let biggest = header_tags.length;  // biggest level of children elements reached (and by big I mean in terns of h tags, so 1 > 2 > 3)
        for (let child of $children) {
            child_level = header_tags.indexOf($(child).prop('tagName').toLowerCase())  // get level of child
            if (child_level <= biggest) {  // next child equal or bigger level: include it in this sub-list
                biggest = child_level
                construct_nav($(child), $sub_nav, child_level)  // recursively call on the child
            }
            // otherwise, this child is a smaller than previous children, so we don't include it because those higher children will.
        }
    }  // else, no children - base case

}

function convert_custom_links($docs) {
    // find the custom links and link them to their IDs assigned by construct_nav(), which must be called first.
    let $headers = $docs.find(":header")

    let $links = $docs.find("a")
    for (let link of $links) {
        let $link = $(link)
        let ref = $link.attr('href')
        if (!ref) return;
        if (ref[0] == "/") continue;  // ignore actual links

        let $to_search = $headers  // list of headers to search
        let match;
        for (let title of ref.split(";")) {  // for each name separated by a semicolon
            match = $to_search.filter(function() {
                return $(this).text().toLowerCase() === title.toLowerCase()  // first matching header
            })[0]
            if (!match) { // no match for this header
                console.log("No header found: ", $link.attr('href'))
                $link.replaceWith($link.html())  // remove link tag and replace with plain text
                return;
            }
            let larger = header_tags.slice(0, header_tags.indexOf($(match).prop('tagName').toLowerCase())+1)
            $to_search = $(match).nextUntil(larger.join(', '), ':header')  // all smaller h siblings until next larger tag
        }
        // if we got to here, a match was found
        let id = $(match).prop('id')  // ID assigned to this header
        $link.prop('href', `#${id}`)  // set link href to ID
        $link.attr("uk-scroll", "offset: 80")  // add UiKit scroll offset
    }
}

function format_notes($docs) {
    // find all <note> tags and style them
    let $notes = $docs.find("note")

    // style note divs
    for (let note of $notes) {
        let content = $(note).html().toUpperCase()
        let color = ''
        if (content == "SUCCESS") color = "uk-label-success"
        else if (content == "WARNING") color = "uk-label-warning"
        else if (content == "DANGER") color = "uk-label-danger"
        $(note).replaceWith($(`<span class="uk-label ${color}">${$(note).html()}</span>`))
    }
}

$(document).ready(() => {
    var $nav = $("#nav")
    var $docs = $("#docs")
    var $nav_overlay = $("#navbar-overlay div.uk-offcanvas-bar")

    // h1 is section header
    $('#docs h1').addClass('uk-text-center')  // center
    $('#docs h1').not(":first").before('<hr class="uk-divider-icon uk-margin-large">')  // add hr before section (except the first)

    construct_nav($docs, $nav)  // construct nav from the documentation HTML
    $($nav.html()).appendTo($nav_overlay)  // now copy it over to the nav overlay section for smaller screens

    convert_custom_links($docs)

    format_notes($docs)
})