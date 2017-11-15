var gulp = require('gulp');

var sassLint = require('gulp-sass-lint');
var pump = require('pump');
var spawn = require('child_process').spawn;

var watchConfig = require('../config.js').watchConfig;


gulp.task('lint', ['lint:styles', 'lint:python']);

gulp.task('lint:python', function(cb) {
    var command = ['run', 'flake8', '--exclude=etc,migrations,manage.py,node_modules,settings'];
    command = command.concat(process.argv.splice(3));
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', cb);
});

gulp.task('lint:styles', function(cb) {
    pump([
        gulp.src(watchConfig.stylesGlob),
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
});
