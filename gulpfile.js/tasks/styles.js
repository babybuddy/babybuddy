var gulp = require('gulp');

var concat = require('gulp-concat');
var pump = require('pump');
var sass = require('gulp-sass');
var sassGlob = require('gulp-sass-glob');

var stylesConfig = require('../config.js').stylesConfig;


gulp.task('styles', ['styles:vendor', 'styles:app']);

gulp.task('styles:vendor', function(cb) {
    pump([
        gulp.src(stylesConfig.vendor),
        concat('vendor.css'),
        gulp.dest(stylesConfig.dest)
    ], cb);
});

gulp.task('styles:app', function (cb) {
    pump([
        gulp.src(stylesConfig.app),
        sassGlob({ignorePaths: stylesConfig.ignore}),
        sass().on('error', sass.logError),
        concat('app.css'),
        gulp.dest(stylesConfig.dest)
    ], cb);
});
