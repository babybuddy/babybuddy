var basePath = 'babyblotter/static/babyblotter/';

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
            extras: 'node_modules/font-awesome/fonts/*'
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
        app: [
            'babyblotter/static_site/js/babyblotter.js',
            'api/static/js/*.js',
            'core/static/js/*.js',
            'dashboard/static/js/*.js'
        ]
    },
    stylesConfig: {
        dest: basePath + 'css/',
        vendor: [
            'node_modules/tempusdominus-bootstrap-4/build/css/tempusdominus-bootstrap-4.css',
            'node_modules/font-awesome/css/font-awesome.css'
        ],
        app: 'babyblotter/static_site/scss/babyblotter.scss'
    }
};
