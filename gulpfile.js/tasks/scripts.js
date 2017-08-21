var gulp = require('gulp');

var concat = require('gulp-concat');
var pump = require('pump');

var scriptsConfig = require('../config.js').scriptsConfig;


gulp.task('scripts', ['scripts:vendor', 'scripts:app']);

gulp.task('scripts:vendor', function(cb) {
    pump([
        gulp.src(scriptsConfig.vendor),
        concat('vendor.js'),
        gulp.dest(scriptsConfig.dest)
    ], cb);
});

gulp.task('scripts:app', function(cb) {
    pump([
        gulp.src(scriptsConfig.app),
        concat('app.js'),
        gulp.dest(scriptsConfig.dest)
    ], cb);
});
