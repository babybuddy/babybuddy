var gulp = require('gulp');

var concat = require('gulp-concat');
var del = require('del');
var flatten = require('gulp-flatten');
var pump = require('pump');
var sass = require('gulp-sass');
var sassGlob = require('gulp-sass-glob');
var sassLint = require('gulp-sass-lint');
var spawn = require('child_process').spawn;

var config = require('./gulpfile.config.js');


function extras(cb) {
    pump([
        gulp.src(config.extrasConfig.fonts.files),
        gulp.dest(config.extrasConfig.fonts.dest)
    ], cb);

    pump([
        gulp.src(config.extrasConfig.images.files),
        flatten({ subPath: 3 }),
        gulp.dest(config.extrasConfig.images.dest)
    ], cb);

    pump([
        gulp.src(config.extrasConfig.logo.files),
        flatten({ subPath: 3 }),
        gulp.dest(config.extrasConfig.logo.dest)
    ], cb);

    pump([
        gulp.src(config.extrasConfig.root.files),
        gulp.dest(config.extrasConfig.root.dest)
    ], cb);
}
gulp.task('extras', extras);

function scripts(cb) {
    pump([
        gulp.src(config.scriptsConfig.vendor),
        concat('vendor.js'),
        gulp.dest(config.scriptsConfig.dest)
    ], cb);

    pump([
        gulp.src(config.scriptsConfig.graph),
        concat('graph.js'),
        gulp.dest(config.scriptsConfig.dest)
    ], cb);

    pump([
        gulp.src(config.scriptsConfig.app),
        concat('app.js'),
        gulp.dest(config.scriptsConfig.dest)
    ], cb);
}
gulp.task('scripts', scripts);

function styles(cb) {
    pump([
        gulp.src(config.stylesConfig.vendor),
        concat('vendor.css'),
        gulp.dest(config.stylesConfig.dest)
    ], cb);

    pump([
        gulp.src(config.stylesConfig.app),
        sassGlob({ignorePaths: config.stylesConfig.ignore}),
        sass().on('error', sass.logError),
        concat('app.css'),
        gulp.dest(config.stylesConfig.dest)
    ], cb);
}
gulp.task('styles', styles);

gulp.task('build', gulp.parallel(extras, scripts, styles));

function watch() {
    gulp.watch(config.watchConfig.scriptsGlob, scripts);
    gulp.watch(config.watchConfig.stylesGlob, styles);
}
gulp.task('watch', watch);

function lint(cb) {
    var command = ['run', 'flake8', '--exclude=etc,migrations,manage.py,node_modules,settings'];
    command = command.concat(process.argv.splice(3));
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', cb);

    pump([
        gulp.src(config.watchConfig.stylesGlob),
        sassLint({
            rules: {
                'declarations-before-nesting': 1,
                'indentation': [ 1, { 'size': 4 } ],
                'no-ids': 0,
                'no-vendor-prefixes': 2,
                'placeholder-in-extend': 0,
                'property-sort-order': 0
            }
        }),
        sassLint.format(),
        sassLint.failOnError()
    ], cb);
}
gulp.task('lint', lint);

function test(cb) {
    var command = ['run', 'python', 'manage.py', 'test'];
    command = command.concat(process.argv.splice(3));
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', cb);
}
gulp.task('test', test);

function coverage(cb) {
    spawn(
        'pipenv',
        [
            'run',
            'coverage',
            'run',
            'manage.py',
            'test'
        ],
        {
            stdio: 'inherit'
        }
    ).on('exit', cb);
}
gulp.task('coverage', coverage);

gulp.task('collectstatic', function(cb) {
    var command = ['run', 'python', 'manage.py', 'collectstatic'];
    command = command.concat(process.argv.splice(3));
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', cb);
});

gulp.task('fake', function(cb) {
    var command = ['run', 'python', 'manage.py', 'fake'];
    command = command.concat(process.argv.splice(3));
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', cb);
});

gulp.task('migrate', function(cb) {
    var command = ['run', 'python', 'manage.py', 'migrate'];
    command = command.concat(process.argv.splice(3));
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', cb);
});

gulp.task('makemigrations', function(cb) {
    var command = ['run', 'python', 'manage.py', 'makemigrations'];
    command = command.concat(process.argv.splice(3));
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', cb);
});

gulp.task('reset', function(cb) {
    spawn(
        'pipenv',
        [
            'run',
            'python',
            'manage.py',
            'reset',
            '--no-input'
        ],
        {
            stdio: 'inherit'
        }
    ).on('exit', cb);
});

function clean() {
    return del([
        '**/static',
        'static'
    ]);
}

gulp.task('clean', clean);

gulp.task('runserver', function(cb) {
    var command = ['run', 'python', 'manage.py', 'runserver'];
    command = command.concat(process.argv.splice(3));
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', cb);
});

gulp.task('default', gulp.series('build', gulp.parallel(watch, 'runserver')));
