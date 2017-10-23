var basePath = 'babybuddy/static/babybuddy/';

module.exports = {
    basePath: basePath,
    compressConfig: {
        scripts: {
            dest: basePath + 'js/'
        },
        styles: {
            dest: basePath + 'css/'
        }
    },
    extrasConfig: {
        fonts: {
            dest: basePath + 'fonts/',
            files: 'node_modules/font-awesome/fonts/*'
        },
        root: {
            dest: basePath + 'root/',
            files: 'babybuddy/static_src/root/*'
        }
    },
    scriptsConfig: {
        dest: basePath + 'js/',
        vendor: [
            'node_modules/jquery/dist/jquery.js',
            'node_modules/popper.js/dist/umd/popper.js',
            'node_modules/bootstrap/dist/js/bootstrap.js',
            'node_modules/moment/moment.js',
            'node_modules/tempusdominus-bootstrap-4/build/js/tempusdominus-bootstrap-4.js'
        ],
        graph: [
            'node_modules/plotly.js/dist/plotly-cartesian.js'
        ],
        app: [
            'babybuddy/static_src/js/babybuddy.js',
            'api/static_src/js/*.js',
            'core/static_src/js/*.js',
            'dashboard/static_src/js/*.js'
        ]
    },
    stylesConfig: {
        dest: basePath + 'css/',
        vendor: [
            'node_modules/tempusdominus-bootstrap-4/build/css/tempusdominus-bootstrap-4.css'
        ],
        app: 'babybuddy/static_src/scss/babybuddy.scss',
        ignore: [
            'babybuddy.scss'
        ]
    },
    watchConfig: {
        scriptsGlob: [
            '**/static_src/js/**/*.js',
            '!babybuddy/static/js/'
        ],
        stylesGlob: [
            '**/static_src/scss/**/*.scss'
        ]
    }
};
