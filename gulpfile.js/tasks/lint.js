var gulp = require('gulp');

var sassLint = require('gulp-sass-lint');
var pump = require('pump');

var watchConfig = require('../config.js').watchConfig;


gulp.task('lint', ['lint:styles']);

gulp.task('lint:styles', function(cb) {
    pump([
        gulp.src(watchConfig.stylesGlob),
        sassLint({
            rules: {
                'declarations-before-nesting': 1,
                'indentation': [ 1, { 'size': 4 } ],
                'no-ids': 0,
                'no-vendor-prefixes': 2,
                'property-sort-order': 0
            }
        }),
        sassLint.format(),
        sassLint.failOnError()
    ], cb);
});
