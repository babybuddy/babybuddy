var gulp = require('gulp');

var concat = require('gulp-concat');
var csso = require('gulp-csso');
var pump = require('pump');
var sass = require('gulp-sass');
var uglify = require('gulp-uglify');

/* APP FILES */

gulp.task('app:scripts', function() {
    return gulp.src([
        'babyblotter/static_site/js/babyblotter.js',
        'api/static/js/*.js',
        'core/static/js/*.js',
        'dashboard/static/js/*.js'
    ])
        .pipe(concat('app.js'))
        .pipe(gulp.dest('babyblotter/static/babyblotter/js/'));
});

gulp.task('app:styles', function (cb) {
    pump([
            gulp.src('babyblotter/static_site/scss/babyblotter.scss'),
            sass().on('error', sass.logError),
            concat('app.css'),
            gulp.dest('babyblotter/static/babyblotter/css/')
        ],
        cb
    );
});

gulp.task('app', ['app:scripts', 'app:styles']);

/* VENDOR FILES */

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
        //'node_modules/bootstrap/dist/css/bootstrap.css',
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

/* COMPRESSION */

gulp.task('compress:app:scripts', function (cb) {
    pump([
            gulp.src('babyblotter/static/babyblotter/js/app.js'),
            concat('app.min.js'),
            uglify(),
            gulp.dest('babyblotter/static/babyblotter/js/')
        ],
        cb
    );
});

gulp.task('compress:app:styles', function (cb) {
    pump([
            gulp.src('babyblotter/static/babyblotter/css/app.css'),
            concat('app.min.css'),
            csso(),
            gulp.dest('babyblotter/static/babyblotter/css/')
        ],
        cb
    );
});

gulp.task('compress:vendor:scripts', function (cb) {
    pump([
            gulp.src('babyblotter/static/babyblotter/js/vendor.js'),
            concat('vendor.min.js'),
            uglify(),
            gulp.dest('babyblotter/static/babyblotter/js/')
        ],
        cb
    );
});

gulp.task('compress:vendor:styles', function (cb) {
    pump([
            gulp.src('babyblotter/static/babyblotter/css/vendor.css'),
            concat('vendor.min.css'),
            csso(),
            gulp.dest('babyblotter/static/babyblotter/css/')
        ],
        cb
    );
});

gulp.task('compress', [
    'compress:app:scripts',
    'compress:app:styles',
    'compress:vendor:scripts',
    'compress:vendor:styles'
]);

/* DEFAULT */

gulp.task('default', ['vendor', 'app']);