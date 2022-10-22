const gulp = require('gulp');

const all = require('gulp-all');
const concat = require('gulp-concat');
const del = require('del');
const es = require('child_process').execSync;
const flatten = require('gulp-flatten');
const fontello = require('gulp-fontello');
const minify = require('gulp-minify');
const removeSourcemaps = require('gulp-remove-sourcemaps');
const sass = require('gulp-sass')(require('sass'));
const sassGlob = require('gulp-sass-glob');
const styleLint = require('@ronilaukkarinen/gulp-stylelint');
const spawn = require('child_process').spawn;

const config = require('./gulpfile.config.js');

/**
 * Spawns a command for pipenv.
 *
 * @param command
 *   Command and arguments.
 *
 * @returns {Promise<unknown>}
 *
 * @private
 */
function _runInPipenv(command) {
    command.unshift('run');
    command = command.concat(process.argv.splice(3));
    return new Promise((resolve, reject) => {
        spawn('pipenv', command, { stdio: 'inherit' })
            .on('exit', function (code) {
                if (code) {
                    reject();
                }
                resolve();
            });
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
                        'pipenv run coverage run manage.py test --settings=babybuddy.settings.test ' + test_name,
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
 */
function docsBuild() {
    return _runInPipenv(['mkdocs', 'build']);
}

/**
 * Deploys the documentation site to GitHub Pages.
 */
function docsDeploy() {
    return _runInPipenv(['mkdocs', 'gh-deploy']);
}

/**
 * Serves the documentation site, watching for changes.
 */
function docsWatch() {
    return _runInPipenv(['mkdocs', 'serve']);
}

/**
 * Builds and copies "extra" static files to configured paths.
 */
function extras() {
    return all(
        gulp.src(config.extrasConfig.fonts.files)
            .pipe(gulp.dest(config.extrasConfig.fonts.dest)),
        gulp.src(config.extrasConfig.images.files)
            .pipe(flatten({ subPath: 3 }))
            .pipe(gulp.dest(config.extrasConfig.images.dest)),
        gulp.src(config.extrasConfig.logo.files)
            .pipe(flatten({ subPath: 3 }))
            .pipe(gulp.dest(config.extrasConfig.logo.dest)),
        gulp.src(config.extrasConfig.root.files)
            .pipe(gulp.dest(config.extrasConfig.root.dest))
    );
}

/**
 * Runs Black formatting on Python code.
 */
function format() {
    return _runInPipenv(['black', '.']);
}

/**
 * Runs linting on Python and SASS code.
 */
function lint() {
    return all(
        _runInPipenv(['black', '.', '--check', '--diff', '--color']),
        gulp.src(config.watchConfig.stylesGlob)
            .pipe(styleLint({
                reporters: [{ formatter: 'string', console: true }]
            }))
    );
}

/**
 * Builds and copies JavaScript static files to configured paths.
 */
function scripts() {
    const streams = [];
    const types = ['vendor', 'graph', 'app', 'tags_editor'];
    types.forEach((type) => {
        streams.push(
            gulp.src(config.scriptsConfig[type])
                .pipe(removeSourcemaps())
                .pipe(concat(`${type}.js`))
                .pipe(minify({
                    ext: { min:'.js' },
                    noSource: true,
                }))
                .pipe(gulp.dest(config.scriptsConfig.dest))
        );
    })
    return all(streams);
}

/**
 * Builds and copies CSS static files to configured paths.
 */
function styles() {
    return gulp.src(config.stylesConfig.app)
        .pipe(sassGlob({ignorePaths: config.stylesConfig.ignore}))
        .pipe(sass().on('error', sass.logError))
        .pipe(concat('app.css'))
        .pipe(gulp.dest(config.stylesConfig.dest));
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
                    es('pipenv run python manage.py test --settings=babybuddy.settings.test ' + test_name, {stdio: 'inherit'});
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
function updateGlyphs() {
    return gulp.src(config.glyphFontConfig.configFile)
        .pipe(fontello({ assetsOnly: false }))
        .pipe(gulp.dest(config.glyphFontConfig.dest));
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

gulp.task('compilemessages', () => {
    return _runInPipenv(['python', 'manage.py', 'compilemessages']);
});

gulp.task('createcachetable', () => {
    return _runInPipenv(['python', 'manage.py', 'createcachetable']);
});

gulp.task('fake', () => {
    return _runInPipenv(['python', 'manage.py', 'fake']);
});

gulp.task('migrate', () => {
    return _runInPipenv(['python', 'manage.py', 'migrate']);
});

gulp.task('makemessages', () => {
    return _runInPipenv(['python', 'manage.py', 'makemessages']);
});

gulp.task('makemigrations', () => {
    return _runInPipenv(['python', 'manage.py', 'makemigrations']);
});

gulp.task('reset', () => {
    return _runInPipenv(['python', 'manage.py', 'reset', '--no-input']);
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

gulp.task('generateschema', () => {
    return _runInPipenv([
        'python',
        'manage.py',
        'generateschema',
        '--title',
        'Baby Buddy API',
        '--file',
        'openapi-schema.yml'
    ]);
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

gulp.task('updateglyphs', updateGlyphs);

gulp.task('watch', watch);

/**
 * Gulp compound commands.
 */

gulp.task('build', gulp.parallel('extras', 'scripts', 'styles'));

gulp.task('updatestatic', gulp.series('lint', 'clean', 'build', 'collectstatic'));

gulp.task('default', gulp.series('build', gulp.parallel('watch', 'runserver')));
