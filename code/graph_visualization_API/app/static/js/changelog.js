$(document).ready(() => {
    $('h1').addClass('uk-text-center')  // center title

    // H2 is the version number and date
    for (let h2 of $('h2')) {
        $h2 = $(h2)
        let html = $h2.html()
        let i = html.indexOf(' ')
        let num = ''
        let date = ''
        if (i == -1) {
            num = html
        } else {
            num = html.substr(0, i)
            date = html.substr(i+1)
        }
        $h2.html(`${num} <span class="uk-text-lighter uk-text-muted">${date}</span>`)
    }

    // add labels to list items under a their particular h3
    for (let h3 of $('h3')) {
        let $h3 = $(h3)
        let label = $h3.html().toUpperCase()
        let $ul = $h3.next('ul')
        $h3.remove()
        $ul.addClass("uk-list")
        let $list = $ul.find('li')

        let type = "primary"
        if (label == "ADDED") {
            type = "success"
        } else if (label == "FIXED") {
            type = "primary"
        } else if (label == "CHANGED") {
            type = "warning"
        } else if (label == "REMOVED") {
            type = "danger"
        }

        for (let li of $list) {
            $(li).wrapInner("<div></div>")
            $(li).addClass("uk-flex uk-flex-top")
            $(`<span class="uk-label uk-label-${type} uk-text-center uk-margin-right">${label}</span>`).prependTo($(li))
        }
    }


})