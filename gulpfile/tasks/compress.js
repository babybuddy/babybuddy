var gulp = require('gulp');

var concat = require('gulp-concat');
var csso = require('gulp-csso');
var pump = require('pump');
var uglify = require('gulp-uglify');


gulp.task('compress', [
    'compress:scripts:app',
    'compress:styles:app',
    'compress:scripts:vendor',
    'compress:styles:vendor'
]);

gulp.task('compress:scripts:app', ['scripts:app'], function (cb) {
    pump([
        gulp.src('babyblotter/static/babyblotter/js/app.js'),
        concat('app.min.js'),
        uglify(),
        gulp.dest('babyblotter/static/babyblotter/js/')
    ], cb);
});

gulp.task('compress:scripts:vendor', ['scripts:vendor'], function (cb) {
    pump([
        gulp.src('babyblotter/static/babyblotter/js/vendor.js'),
        concat('vendor.min.js'),
        uglify(),
        gulp.dest('babyblotter/static/babyblotter/js/')
    ], cb);
});

gulp.task('compress:styles:app', ['styles:app'], function (cb) {
    pump([
        gulp.src('babyblotter/static/babyblotter/css/app.css'),
        concat('app.min.css'),
        csso(),
        gulp.dest('babyblotter/static/babyblotter/css/')
    ], cb);
});

gulp.task('compress:styles:vendor', ['styles:vendor'], function (cb) {
    pump([
        gulp.src('babyblotter/static/babyblotter/css/vendor.css'),
        concat('vendor.min.css'),
        csso(),
        gulp.dest('babyblotter/static/babyblotter/css/')
    ], cb);
});
