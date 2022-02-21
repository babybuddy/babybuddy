const basePath = 'babybuddy/static/babybuddy/';

module.exports = {
    basePath: basePath,
    extrasConfig: {
        fonts: {
            dest: basePath + 'font/',
            files: 'babybuddy/static_src/fontello/font/*'
        },
        images: {
            dest: basePath + 'img/',
            files: '**/static_src/img/**/*'
        },
        logo: {
            dest: basePath + 'logo/',
            files: 'babybuddy/static_src/logo/**/*'
        },
        root: {
            dest: basePath + 'root/',
            files: 'babybuddy/static_src/root/*'
        }
    },
    glyphFontConfig: {
        configFile: 'babybuddy/static_src/fontello/config.json',
        dest: 'babybuddy/static_src/fontello'
    },
    scriptsConfig: {
        dest: basePath + 'js/',
        vendor: [
            'node_modules/pulltorefreshjs/dist/index.umd.js',
            'node_modules/jquery/dist/jquery.js',
            'node_modules/popper.js/dist/umd/popper.js',
            'node_modules/bootstrap/dist/js/bootstrap.js',
            'node_modules/moment/moment.js',
            'node_modules/moment/locale/de.js',
            'node_modules/moment/locale/en-gb.js',
            'node_modules/moment/locale/es.js',
            'node_modules/moment/locale/fi.js',
            'node_modules/moment/locale/fr.js',
            'node_modules/moment/locale/it.js',
            'node_modules/moment/locale/nl.js',
            'node_modules/moment/locale/pl.js',
            'node_modules/moment/locale/pt.js',
            'node_modules/moment/locale/sv.js',
            'node_modules/moment/locale/tr.js',
            'node_modules/moment/locale/zh-cn.js',
            'node_modules/moment-timezone/builds/moment-timezone-with-data-10-year-range.js',
            'node_modules/tempusdominus-bootstrap-4/build/js/tempusdominus-bootstrap-4.js'
        ],
        graph: [
            'node_modules/plotly.js/dist/plotly-cartesian.js',
            'node_modules/plotly.js/dist/plotly-locale-de.js',
            'node_modules/plotly.js/dist/plotly-locale-es.js',
            'node_modules/plotly.js/dist/plotly-locale-fi.js',
            'node_modules/plotly.js/dist/plotly-locale-fr.js',
            'node_modules/plotly.js/dist/plotly-locale-it.js',
            'node_modules/plotly.js/dist/plotly-locale-nl.js',
            'node_modules/plotly.js/dist/plotly-locale-pl.js',
            'node_modules/plotly.js/dist/plotly-locale-pt-br.js',
            'node_modules/plotly.js/dist/plotly-locale-pt-pt.js',
            'node_modules/plotly.js/dist/plotly-locale-sv.js',
            'node_modules/plotly.js/dist/plotly-locale-tr.js',
            'node_modules/plotly.js/dist/plotly-locale-uk.js',
            'node_modules/plotly.js/dist/plotly-locale-zh-cn.js',
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
        app: 'babybuddy/static_src/scss/babybuddy.scss',
        ignore: [
            'babybuddy.scss'
        ]
    },
    testsConfig: {
      isolated: [
          'babybuddy.tests.formats.tests_en_us.FormatsTestCase.test_use_24_hour_time_format'
      ],
    },
    watchConfig: {
        scriptsGlob: [
            '*/static_src/js/**/*.js',
            '!babybuddy/static/js/'
        ],
        stylesGlob: [
            '*/static_src/scss/**/*.scss'
        ]
    }
};
