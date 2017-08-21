var gulp = require('gulp');

var concat = require('gulp-concat');
var pump = require('pump');


gulp.task('scripts', ['scripts:vendor', 'scripts:app']);

gulp.task('scripts:vendor', function(cb) {
    pump([
        gulp.src([
            'node_modules/jquery/dist/jquery.js',
            'node_modules/popper.js/dist/umd/popper.js',
            'node_modules/bootstrap/dist/js/bootstrap.js',
            'node_modules/moment/moment.js',
            'node_modules/tempusdominus-bootstrap-4/build/js/tempusdominus-bootstrap-4.js'
        ]),
        concat('vendor.js'),
        gulp.dest('babyblotter/static/babyblotter/js/')
    ], cb);
});

gulp.task('scripts:app', function(cb) {
    pump([
        gulp.src([
            'babyblotter/static_site/js/babyblotter.js',
            'api/static/js/*.js',
            'core/static/js/*.js',
            'dashboard/static/js/*.js'
        ]),
        concat('app.js'),
        gulp.dest('babyblotter/static/babyblotter/js/')
    ], cb);
});
