const gulp = require('gulp');

const concat = require('gulp-concat');
const del = require('del');
const es = require('child_process').execSync;
const flatten = require('gulp-flatten');
const fontello = require('gulp-fontello');
const pump = require('pump');
const removeSourcemaps = require('gulp-remove-sourcemaps');
const sass = require('gulp-sass')(require('sass'));
const sassGlob = require('gulp-sass-glob');
const styleLint = require('gulp-stylelint');
const spawn = require('child_process').spawn;

const config = require('./gulpfile.config.js');

/**
 * Support functions for Gulp tasks.
 */

function _runInPipenv(command, cb) {
    command.unshift('run');
    command = command.concat(process.argv.splice(3));
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', function (code) {
        if (code) process.exit(code);
        cb();
    });
}

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
            '--settings=babybuddy.settings.test',
            '--parallel',
            '--exclude-tag',
            'isolate'
        ],
        {
            stdio: 'inherit'
        }
    ).on('exit', function(code) {
        // Run isolated tests with coverage.
        if (code === 0) {
            try {
                config.testsConfig.isolated.forEach(function (test_name) {
                    es(
                        'pipenv run coverage run manage.py test ' + test_name,
                        {stdio: 'inherit'}
                    );
                })
            } catch (error) {
                console.error(error);
                cb();
                process.exit(1);
            }

            // Combine coverage results.
            es('pipenv run coverage combine', {stdio: 'inherit'});
        }

        cb();
        process.exit(code)
    });
}

/**
 * Builds the documentation site locally.
 *
 * @param cb
 */
function docsBuild(cb) {
    _runInPipenv(['mkdocs', 'build'], cb);
}

/**
 * Deploys the documentation site to GitHub Pages.
 *
 * @param cb
 */
function docsDeploy(cb) {
    _runInPipenv(['mkdocs', 'gh-deploy'], cb);
}

/**
 * Serves the documentation site, watching for changes.
 *
 * @param cb
 */
function docsWatch(cb) {
    _runInPipenv(['mkdocs', 'serve'], cb);
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
 * Runs Black formatting on Python code.
 *
 * @param cb
 */
function format(cb) {
    _runInPipenv(['black', '.'], cb);
}

/**
 * Runs linting on Python and SASS code.
 *
 * @param cb
 */
function lint(cb) {
    _runInPipenv(['black', '.', '--check', '--diff', '--color'], cb);

    pump([
        gulp.src(config.watchConfig.stylesGlob),
        styleLint({
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
        removeSourcemaps(),
        concat('vendor.js'),
        gulp.dest(config.scriptsConfig.dest)
    ], cb);

    pump([
        gulp.src(config.scriptsConfig.graph),
        removeSourcemaps(),
        concat('graph.js'),
        gulp.dest(config.scriptsConfig.dest)
    ], cb);

    pump([
        gulp.src(config.scriptsConfig.app),
        removeSourcemaps(),
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
    let command = [
        'run',
        'python',
        'manage.py',
        'test',
        '--settings=babybuddy.settings.test',
        '--parallel',
        '--exclude-tag',
        'isolate'
    ];
    command = command.concat(process.argv.splice(3));
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', function(code) {
        if (code === 0) {
            // Run isolated tests.
            config.testsConfig.isolated.forEach(function(test_name) {
                try {
                    es('pipenv run python manage.py test ' + test_name, {stdio: 'inherit'});
                } catch (error) {
                    console.error(error);
                    cb();
                    process.exit(1);
                }
            })
        }
        cb();
        process.exit(code);
    });
}

/**
 * Updates glyphs font data from Fontello.
 */
function updateglyphs(cb) {
    pump([
        gulp.src(config.glyphFontConfig.configFile),
        fontello({ assetsOnly: false }),
        gulp.dest(config.glyphFontConfig.dest)
    ], cb);
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
    let command = ['run', 'python', 'manage.py', 'collectstatic'];

    /* Use base settings if no settings parameter is supplied. */
    const parameters = process.argv.splice(3);
    let noSettings = true;
    for (let i = 0; i < parameters.length; i++) {
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
    _runInPipenv(['python', 'manage.py', 'compilemessages'], cb);
});

gulp.task('createcachetable', function(cb) {
    _runInPipenv(['python', 'manage.py', 'createcachetable'], cb);
});

gulp.task('fake', function(cb) {
    _runInPipenv(['python', 'manage.py', 'fake'], cb);
});

gulp.task('migrate', function(cb) {
    _runInPipenv(['python', 'manage.py', 'migrate'], cb);
});

gulp.task('makemessages', function(cb) {
    _runInPipenv(['python', 'manage.py', 'makemessages'], cb);
});

gulp.task('makemigrations', function(cb) {
    _runInPipenv(['python', 'manage.py', 'makemigrations'], cb);
});

gulp.task('reset', function(cb) {
    _runInPipenv(['python', 'manage.py', 'reset', '--no-input'], cb);
});

gulp.task('runserver', function(cb) {
    let command = ['run', 'python', 'manage.py', 'runserver'];

    /**
     * Process any parameters. Any arguments found here will be removed from
     * the parameters list so other parameters continue to be passed to the
     * command.
     **/
    const parameters = process.argv.splice(2);
    for (let i = 0; i < parameters.length; i++) {
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

gulp.task('generateschema', function(cb) {
    _runInPipenv([
        'python',
        'manage.py',
        'generateschema',
        '--title',
        'Baby Buddy API',
        '--file',
        'openapi-schema.yml'
    ], cb);
});

/**
 * Gulp commands.
 */

gulp.task('clean', clean);

gulp.task('coverage', coverage);

gulp.task('docs:build', docsBuild);

gulp.task('docs:deploy', docsDeploy);

gulp.task('docs:watch', docsWatch);

gulp.task('extras', extras);

gulp.task('format', format);

gulp.task('lint', lint);

gulp.task('scripts', scripts);

gulp.task('styles', styles);

gulp.task('test', test);

gulp.task('updateglyphs', updateglyphs);

gulp.task('watch', watch);

/**
 * Gulp compound commands.
 */

gulp.task('build', gulp.parallel('extras', 'scripts', 'styles'));

gulp.task('updatestatic', gulp.series('lint', 'clean', 'build', 'collectstatic'));

gulp.task('default', gulp.series('build', gulp.parallel('watch', 'runserver')));
