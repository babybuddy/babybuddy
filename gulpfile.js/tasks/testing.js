var gulp = require('gulp');

var spawn = require('child_process').spawn;


gulp.task('test', function(cb) {
    var command = ['run', 'python', 'manage.py', 'test'];
    command = command.concat(process.argv.splice(3));
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', cb);
});

gulp.task('coverage', function(cb) {
    spawn(
        'pipenv',
        [
            'run',
            'coverage',
            'run',
            '--source=api,core,dashboard,reports',
            'manage.py',
            'test'
        ],
        {
            stdio: 'inherit'
        }
    ).on('exit', cb);
});
