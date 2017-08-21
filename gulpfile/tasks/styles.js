var gulp = require('gulp');

var concat = require('gulp-concat');
var pump = require('pump');
var sass = require('gulp-sass');
var sassGlob = require('gulp-sass-glob');


gulp.task('styles', ['styles:vendor', 'styles:app']);

gulp.task('scripts:vendor', function(cb) {
    pump([
        gulp.src([
            'node_modules/tempusdominus-bootstrap-4/build/css/tempusdominus-bootstrap-4.css',
            'node_modules/font-awesome/css/font-awesome.css'
        ]),
        concat('vendor.css'),
        gulp.dest('babyblotter/static/babyblotter/css/')
    ], cb);
});

gulp.task('app:styles', function (cb) {
    pump([
        gulp.src('babyblotter/static_site/scss/babyblotter.scss'),
        sassGlob(),
        sass().on('error', sass.logError),
        concat('app.css'),
        gulp.dest('babyblotter/static/babyblotter/css/')
    ], cb);
});
