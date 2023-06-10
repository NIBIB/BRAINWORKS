const { src, dest, series } = require('gulp');
const log = require('gulplog');
const uglify = require('gulp-uglify');
const replace = require('gulp-replace');
const browserify = require('browserify');
const browserify_css = require('browserify-css')
const watchify = require('watchify');
const source = require('vinyl-source-stream');
const buffer = require('vinyl-buffer');
const through = require('through2')

// package.json configuration
const PACKAGE = require('./package.json');

// what to name the minified js files
const LOADER_FILENAME = "graph.min.js"
const MAIN_FILENAME = "main.min.js"  // if you change this, also change the script src tag in loader.js

// domain name specified by the DOMAIN environment variable. If not set, defaults to localhost:5000
var DOMAIN   // host domain name
var VERSION  // version directory to

if (process.env.GULP_PROD) {  // if building production
    DOMAIN = require('./config/domain_name.json')
    VERSION = PACKAGE.version
} else {
    DOMAIN = "http://localhost:5000"
    VERSION = "local"
}

// To replace file assets with the host URL containing the right version
const DIR = `app/versions/${VERSION}`      // destination director

// select all stc/ URL file paths with these extensions
const asset_regex = /src\/([-\/\.\w]+\.(html|svg|png|gif|css|js))/g
const asset_replace = `${DOMAIN}/build/${VERSION}/$1`
const icon_regex = /src\/icons\/([-\.\w]+\.(svg|png))/g

console.log("Domain:", DOMAIN)
console.log("Version:", VERSION)
console.log("Destination:", DIR)
console.log("Asset URL:", asset_replace)

function load_icons(module_path) {
    // Gulp pipe function.
    // Looks through the given file for icons in node_modules/<module_path> and sends them to the destination directory if they are needed for the build.
    return through.obj((file, enc, callback) => {
        let content = String(file.contents)
        let match;
        while (match = icon_regex.exec(content)) {
            let icon_name = match[1]
            let path = `node_modules/${module_path}/${icon_name}`
            let stream = src(path, {allowEmpty: true})
                .on("data", () => {log.info(path)})
                .pipe(dest(DIR+'/icons'))
        }
        callback(null, file)
    })
}

function assets() {
  return src(['src/**/*.gif', 'src/**/*.svg', 'src/**/*.png'])
        .pipe(dest(DIR));  // output directly to version directory
}


function html() {
    return src(['src/html/*.html', 'src/html/*.md'])
        .pipe(load_icons('bootstrap-icons/icons'))
        .pipe(replace(asset_regex, asset_replace))  // replace asset urls
        .pipe(dest(DIR+'/html'));  // output to version directory
}

// documentation js file
function documentation_js() {
    var opts = Object.assign({}, watchify.args, {  // default arguments necessary for watchify to work
        entries: "./src/js/documentation.js",  // entry js file
        debug: false  // way faster
    });

    if (process.env.GULP_PROD) {
        var b = browserify(opts)
    } else {
        var b = watchify(browserify(opts));  // wrap in watchify extension to add ability to detect changes
    }

    b.on('update', bundle); // on any dep update, runs the bundle() function
    b.on('log', log.info); // output build logs to terminal

    function bundle() {
        let bun = b.bundle()  // bundle using browserify
            .on('error', log.error)  // necessary so watchify doesn't swallow errors
            .pipe(source("documentation.min.js"))  // vinyl source and destination file
            .pipe(buffer())  // vinyl buffer output from browserify
        if (process.env.GULP_PROD) bun = bun.pipe(uglify())
        bun = bun.pipe(dest(DIR+'/js'))  // output to version directory
        return bun
    }
    return bundle()
}

// loader js file
function loader_js() {
    var b = browserify({
        entries: "./src/js/loader.js",  // entry js file
        standalone: "Graph",  // put the Graph object in the window
        debug: false  // way faster
    })

    let bun = b.bundle()  // bundle using browserify
        .pipe(source(LOADER_FILENAME))  // vinyl destination file
        .pipe(buffer())  // vinyl buffer output from browserify
        .pipe(replace(asset_regex, asset_replace))
    if (process.env.GULP_PROD) bun = bun.pipe(uglify());
    bun = bun.pipe(dest(DIR+'/js'))  // output to version directory
    return bun
}

// all src js minified to /js
function js() {
    // set up the browserify instance with watchify configuration
    var opts = Object.assign({}, watchify.args, {  // default arguments necessary for watchify to work
        entries: "./src/js/graph.js",  // entry js file
        standalone: "Graph",  // put the Graph object in the window
        debug: false  // way faster
    });

    if (process.env.GULP_PROD) {
        var b = browserify(opts)
    } else {
        var b = watchify(browserify(opts));  // wrap in watchify extension to add ability to detect changes
    }

    // allow require() css files
    b.transform({
        global: true,  // allow pulling css from node_modules
        autoInject: false,  // disable injecting style tags into head of document (I do it myself to put them in the shadow DOM)
        minify: process.env.GULP_PROD == 'true',  // minify if in production
        rootDir: "."  // root directory from which to specify css files
    }, browserify_css)

    b.on('update', bundle); // on any dep update, runs the bundler
    b.on('log', log.info); // output build logs to terminal
    //b.on('file', log.info);

    function bundle() {
        let bun = b.bundle()  // bundle using browserify
        .on('error', log.error)  // necessary so watchify doesn't swallow errors
        .pipe(source(MAIN_FILENAME))  // vinyl source and destination file
        .pipe(buffer())  // vinyl buffer output from browserify
        .pipe(replace(asset_regex, asset_replace))
        if (process.env.GULP_PROD) bun = bun.pipe(uglify());
        bun = bun.pipe(dest(DIR+'/js'))  // output to version directory
        return bun
    }
    return bundle()
}

// perform each of these functions in series
exports.default = series(assets, html, loader_js, documentation_js, js)