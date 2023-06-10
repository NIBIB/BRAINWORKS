const $ = require('jquery')
const sleep = ms => new Promise(r => setTimeout(r, ms));

// deep clone an object
function deep_clone(o) {
    return $.extend(true, {}, o);
}

function is_object(o) {
    return Object.prototype.toString.call(o) === '[object Object]';
}

function is_plain_object(o) {
    var ctor, prot;
    if (is_object(o) === false) return false;

    // If has modified constructor
    ctor = o.constructor;
    if (ctor === undefined) return true;

    // If has modified prototype
    prot = ctor.prototype;
    if (is_object(prot) === false) return false;

    // If constructor does not have an Object-specific method
    if (prot.hasOwnProperty('isPrototypeOf') === false) {
    return false;
    }

    // Most likely a plain Object
    return true;
};

// Color manipulation
function hex_to_rgb(hex_code) {
    let colors = []
    colors[0] = parseInt(hex_code.substr(1, 2), 16) ?? 0
    colors[1] = parseInt(hex_code.substr(3, 2), 16) ?? 0
    colors[2] = parseInt(hex_code.substr(5, 2), 16) ?? 0
    return colors
}
function rgb_to_hex(red, green, blue) {
    var hex_code = "#"
    hex_code += parseInt(red).toString(16).padStart(2,'0')
    hex_code += parseInt(green).toString(16).padStart(2,'0')
    hex_code += parseInt(blue).toString(16).padStart(2,'0')
    return hex_code
}
function lighten(hex_code, val) {
    let colors = hex_to_rgb(hex_code)
    let red = colors[0]
    let green = colors[1]
    let blue = colors[2]

    red += (255 - red) * val
    green += (255 - green) * val
    blue += (255 - blue) * val
    return rgb_to_hex(red, green, blue)
}

var default_color_space = [[255,0,0],[255,255,0],[0,255,0],[0,255,255],[0,0,255],[255,0,255]]
//var color_space = [[150,0,90],[0,0,200],[0,25,255],[0,152,255],[44,255,150],[151,255,0],[255,234,0],[255,111,0],[255,0,0]]

function color_array(num, color_space=null) {
    // given a number <num> and a color map, generate an array of <num> evenly-spaced color points along the given color map.
    if (!color_space) {
        color_space = default_color_space
    }

    let vectors = []  // vectors for each linear color segment
    let lengths = []  // lengths of each color segment
    let total_length = 0  // total length
    for (let i = 0; i < color_space.length-1; i++) {
        let s1 = color_space[i]
        let s2 = color_space[i+1]
        let vector = [s2[0]-s1[0], s2[1]-s1[1], s2[2]-s1[2]]  // vector from start to end of segment
        let length = Math.sqrt(vector[0]**2 + vector[1]**2 + vector[2]**2)  // length of segment
        vectors.push(vector)
        lengths.push(length)
        total_length += length
    }

    var colors = []
    let step = total_length / num  // length of one step
    let position = 0  // length traversed in a given segment
    //console.log("total", total_length, num, step)
    let i = 0
    while (i < vectors.length) {
        let vector = vectors[i]
        let length = lengths[i]
        if (position >= length) {  // crossed a segment boundary
            position -= length  // subtract segment length
            i += 1  // move to next segment
            continue
        }

        // else next step is within this segment
        let frac = position / length  // fraction of the segment that this step took
        let color = [frac*vector[0]+color_space[i][0], frac*vector[1]+color_space[i][1], frac*vector[2]+color_space[i][2]]
        let hex = rgb_to_hex(color[0], color[1], color[2])
        colors.push(hex)
        //console.log(position, frac, vector, color, hex)
        position += step  // move forward

    }
    return colors
}

var red_blue = ["#ff5050", "#ffffff", "#3366ff"]
function color_gradient(min, mid, max, colors) {
    // given the min, middle, and max values possible, return a function that converts between value and hex colors according to the provided bounds and color space
    // colors is a list of 3 color hex codes
    // distance from the midpoint is treated equally no matter the position of the endpoints in color space.
    if (colors === undefined) colors = red_blue
    if (mid < min) mid = min  // cap midpoint
    if (mid > max) mid = max
    var size = Math.max(max-mid, mid-min)  // maximum magnitude away from midpoint

    let s = hex_to_rgb(colors[0])
    let m = hex_to_rgb(colors[1])
    let e = hex_to_rgb(colors[2])

    var sv = [s[0]-m[0], s[1]-m[1], s[2]-m[2]]  // vector from middle to start color
    var ev = [e[0]-m[0], e[1]-m[1], e[2]-m[2]]  // vector from middle to end color

    function convert(value) {
        if (value < min) value = min  // cap value
        if (value > max) value = max
        let mag = value - mid  // difference from middle
        let p = mag / size  // what proportion of maximum size
        let v = [0, 0, 0];  // vector from middle to new color
        if (mag < 0) {  // below middle
            v = [-p*sv[0], -p*sv[1], -p*sv[2]]
        } else if (mag > 0) {  // above middle
            v = [p*ev[0], p*ev[1], p*ev[2]]
        }
        let c = [m[0]+v[0], m[1]+v[1], m[2]+v[2]]  // total vector to color
        return rgb_to_hex(c[0], c[1], c[2])
    }
    return convert
}

// Math stuff
function decimals(scale) {
    // returns appropriate number of decimals to keep
    scale = Math.abs(scale)
    return scale >= 100 ? 0 : Math.ceil(-Math.log10(scale)+1)
}
function logbase(base, num) {
    return Math.log(num) / Math.log(base)
}
function array_mode(arr) {
    if(arr.length == 0)
        return null
    var counts = {}
    for(let val of arr) {
        if(counts[val] == undefined)
            counts[val] = 1;
        else
            counts[val]++;
    }
    return Object.keys(counts).reduce((a, b) => counts[a] > counts[b] ? a : b);
}
function array_mean(arr) {
    return arr.reduce((a,b) => a + b, 0) / arr.length
}

// download JSON object
function download_json(object, name) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL( new Blob([JSON.stringify(object)], {type:`text/json`}) );
  a.download = name;
  a.click();
}

// Download an image from the given blob
function download_image(blob, name) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
}

// upload JSON object and pass to callback
function upload_json(callback, error_callback) {
    let input = document.createElement('input');
    input.type = 'file';

    var reader = new FileReader();
    var file;
    input.onchange = event => {
        file = event.target.files[0];
        reader.readAsText(file,'UTF-8');
    }

    reader.onload = function(e) {
        try {
            var data = JSON.parse(reader.result)
        } catch(e) {
            error_callback(e, file.name)
            return;
        }
        callback(data, file.name)
    };
    input.click();
}

// replace a given element tag
function replace_tag($element, newElement){
    $element.wrap(newElement);
    var $newElement = $element.parent();
    $.each($element.prop('attributes'), function() {
        $newElement.attr(this.name,this.value);
    });
    $element.contents().unwrap();
    return $newElement;
}

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

module.exports = {
    is_object, is_plain_object, deep_clone, sleep,
    lighten, color_array, color_gradient,
    decimals, logbase,
    array_mode, array_mean,
    download_json, upload_json, download_image,
    replace_tag, detect_browser
}

