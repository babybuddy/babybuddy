var gulp = require('gulp');
var concat = require('gulp-concat');

gulp.task('vendor:scripts', function() {
    return gulp.src([
        'node_modules/jquery/dist/jquery.js',
        'node_modules/popper.js/dist/umd/popper.js',
        'node_modules/bootstrap/dist/js/bootstrap.js',
        'node_modules/moment/moment.js',
        'node_modules/tempusdominus-bootstrap-4/build/js/tempusdominus-bootstrap-4.js'
    ])
        .pipe(concat('vendor.js'))
        .pipe(gulp.dest('babyblotter/static/babyblotter/js/'));
});

gulp.task('vendor:styles', function() {
    return gulp.src([
        'node_modules/bootstrap/dist/css/bootstrap.css',
        'node_modules/tempusdominus-bootstrap-4/build/css/tempusdominus-bootstrap-4.css',
        'node_modules/font-awesome/css/font-awesome.css'
    ])
        .pipe(concat('vendor.css'))
        .pipe(gulp.dest('babyblotter/static/babyblotter/css/'));
});

gulp.task('vendor:fonts', function() {
    return gulp.src([
        'node_modules/font-awesome/fonts/*'
    ])
        .pipe(gulp.dest('babyblotter/static/babyblotter/fonts/'));
});

gulp.task('vendor', ['vendor:styles', 'vendor:scripts', 'vendor:fonts']);

gulp.task('default', ['vendor']);