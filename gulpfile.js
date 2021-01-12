var gulp = require('gulp');

var concat = require('gulp-concat');
var del = require('del');
var es = require('child_process').execSync;
var flatten = require('gulp-flatten');
var pump = require('pump');
var sass = require('gulp-sass');
var sassGlob = require('gulp-sass-glob');
var styleLint = require('gulp-stylelint');
var spawn = require('child_process').spawn;

var config = require('./gulpfile.config.js');

/**
 * Support functions for Gulp tasks.
 */

/**
 * Deletes local static files.
 *
 * @returns {*}
 */
function clean() {
    return del([
        '**/static',
        'static'
    ]);
}

/**
 * Runs coverage operations.
 *
 * @param cb
 */
function coverage(cb) {
    // Erase any previous coverage results.
    es('pipenv run coverage erase', {stdio: 'inherit'});

    // Run tests with coverage.
    spawn(
        'pipenv',
        [
            'run',
            'coverage',
            'run',
            'manage.py',
            'test',
            '--parallel',
            '--exclude-tag',
            'isolate'
        ],
        {
            stdio: 'inherit'
        }
    ).on('exit', function() {
        // Run isolated tests with coverage.
        config.testsConfig.isolated.forEach(function(test_name) {
            es(
                'pipenv run coverage run manage.py test ' + test_name,
                {stdio: 'inherit'}
            );
        })

        // Combine coverage results.
        es('pipenv run coverage combine', {stdio: 'inherit'});

        // Execute callback.
        cb();
    });
}

/**
 * Builds and copies "extra" static files to configured paths.
 *
 * @param cb
 */
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

/**
 * Runs linting on Python and SASS code.
 *
 * @param cb
 */
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

/**
 * Builds and copies JavaScript static files to configured paths.
 *
 * @param cb
 */
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

/**
 * Builds and copies CSS static files to configured paths.
 *
 * @param cb
 */
function styles(cb) {
    pump([
        gulp.src(config.stylesConfig.app),
        sassGlob({ignorePaths: config.stylesConfig.ignore}),
        sass().on('error', sass.logError),
        concat('app.css'),
        gulp.dest(config.stylesConfig.dest)
    ], cb);
}

/**
 * Runs all tests _not_ tagged "isolate".
 *
 * @param cb
 */
function test(cb) {
    var command = [
        'run',
        'python',
        'manage.py',
        'test',
        '--parallel',
        '--exclude-tag',
        'isolate'
    ];
    command = command.concat(process.argv.splice(3));
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', function() {
        // Run isolated tests.
        config.testsConfig.isolated.forEach(function(test_name) {
            es(
                'pipenv run python manage.py test ' + test_name,
                {stdio: 'inherit'}
            );
        })
        cb();
    });
}

/**
 * Watches for changes in configured files.
 */
function watch() {
    gulp.watch(config.watchConfig.scriptsGlob, scripts);
    gulp.watch(config.watchConfig.stylesGlob, styles);
}

/**
 * Django management command passthroughs.
 */

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

gulp.task('compilemessages', function(cb) {
    var command = ['run', 'python', 'manage.py', 'compilemessages'];
    command = command.concat(process.argv.splice(3));
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', cb);
});

gulp.task('createcachetable', function(cb) {
    var command = ['run', 'python', 'manage.py', 'createcachetable'];
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

gulp.task('makemessages', function(cb) {
    var command = ['run', 'python', 'manage.py', 'makemessages'];
    command = command.concat(process.argv.splice(3));
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', cb);
});

gulp.task('makemigrations', function(cb) {
    var command = ['run', 'python', 'manage.py', 'makemigrations'];
    command = command.concat(process.argv.splice(3));
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', cb);
});

/**
 * Runs the custom "reset" command to start a fresh database with fake data.
 */
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

gulp.task('runserver', function(cb) {
    var command = ['run', 'python', 'manage.py', 'runserver'];

    /**
     * Process any parameters. Any arguments found here will be removed from
     * the parameters list so other parameters continue to be passed to the
     * command.
     **/
    var parameters = process.argv.splice(2);
    for (var i = 0; i < parameters.length; i++) {
        /* May be included because this is the default gulp command. */
        if (parameters[i] === 'runserver') {
            delete parameters[i];
        }
        /* "--ip" parameter to set the server IP address. */
        else if (parameters[i] === '--ip') {
            command.push(parameters[i+1]);
            delete parameters[i];
            delete parameters[i+1];
            i++;
        }
    }

    /* Add parameters to command, removing empty values. */
    command = command.concat(parameters.filter(String));

    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', cb);
});

/**
 * Gulp commands.
 */

gulp.task('clean', clean);

gulp.task('coverage', coverage);

gulp.task('extras', extras);

gulp.task('lint', lint);

gulp.task('scripts', scripts);

gulp.task('styles', styles);

gulp.task('test', test);

gulp.task('watch', watch);

/**
 * Gulp compound commands.
 */

gulp.task('build', gulp.parallel('extras', 'scripts', 'styles'));

gulp.task('updatestatic', gulp.series('lint', 'clean', 'build', 'collectstatic'));

gulp.task('default', gulp.series('build', gulp.parallel('watch', 'runserver')));
