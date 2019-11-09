var gulp = require('gulp');

var concat = require('gulp-concat');
var del = require('del');
var flatten = require('gulp-flatten');
var pump = require('pump');
var sass = require('gulp-sass');
var sassGlob = require('gulp-sass-glob');
var styleLint = require('gulp-stylelint');
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
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', function (code) {
        if (code) process.exit(code);
        cb();
    });

    pump([
        gulp.src(config.watchConfig.stylesGlob),
        styleLint({
            config: {
                extends: 'stylelint-config-recommended-scss',
                plugins: [
                    'stylelint-order',
                    'stylelint-scss'
                ],
                rules: {
                    'at-rule-no-vendor-prefix': true,
                    'indentation': 4,
                    'media-feature-name-no-vendor-prefix': true,
                    'order/order': [
                        'declarations',
                        'rules'
                    ],
                    'property-no-vendor-prefix': true,
                    'selector-no-vendor-prefix': true,
                    'value-no-vendor-prefix': true
                }
            },
            reporters: [
                { formatter: 'string', console: true }
            ]
        })
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

    /* Use base settings if no settings parameter is supplied. */
    var parameters = process.argv.splice(3);
    var noSettings = true;
    for (var i = 0; i < parameters.length; i++) {
        if (parameters[i].substring(0, 10) === '--settings') {
            noSettings = false;
            break;
        }
    }
    if (noSettings) {
        parameters.push('--settings=babybuddy.settings.base');
    }

    command = command.concat(parameters);
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

gulp.task('makemessages', function(cb) {
    var command = ['run', 'python', 'manage.py', 'makemessages'];
    command = command.concat(process.argv.splice(3));
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', cb);
});

gulp.task('compilemessages', function(cb) {
    var command = ['run', 'python', 'manage.py', 'compilemessages'];
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
