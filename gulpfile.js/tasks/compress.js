var gulp = require('gulp');

var concat = require('gulp-concat');
var csso = require('gulp-csso');
var pump = require('pump');
var uglify = require('gulp-uglify');

var basePath = require('../config.js').basePath;
var compressConfig = require('../config.js').compressConfig;


gulp.task('compress', [
    'compress:scripts:app',
    'compress:styles:app',
    'compress:scripts:vendor',
    'compress:styles:vendor',
    'compress:scripts:graph'
]);

gulp.task('compress:scripts:app', ['scripts:app'], function (cb) {
    pump([
        gulp.src(basePath + 'js/app.js'),
        concat('app.min.js'),
        uglify(),
        gulp.dest(compressConfig.scripts.dest)
    ], cb);
});

gulp.task('compress:scripts:vendor', ['scripts:vendor'], function (cb) {
    pump([
        gulp.src(basePath + 'js/vendor.js'),
        concat('vendor.min.js'),
        uglify(),
        gulp.dest(compressConfig.scripts.dest)
    ], cb);
});

gulp.task('compress:scripts:graph', ['scripts:graph'], function (cb) {
    pump([
        gulp.src(basePath + 'js/graph.js'),
        concat('graph.min.js'),
        uglify(),
        gulp.dest(compressConfig.scripts.dest)
    ], cb);
});

gulp.task('compress:styles:app', ['styles:app'], function (cb) {
    pump([
        gulp.src(basePath + 'css/app.css'),
        concat('app.min.css'),
        csso(),
        gulp.dest(compressConfig.styles.dest)
    ], cb);
});

gulp.task('compress:styles:vendor', ['styles:vendor'], function (cb) {
    pump([
        gulp.src(basePath + 'css/vendor.css'),
        concat('vendor.min.css'),
        csso(),
        gulp.dest(compressConfig.styles.dest)
    ], cb);
});
