var gulp = require('gulp');

var spawn = require('child_process').spawn;


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

gulp.task('runserver', function(cb) {
    var command = ['run', 'python', 'manage.py', 'runserver'];
    command = command.concat(process.argv.splice(3));
    spawn('pipenv', command, { stdio: 'inherit' }).on('exit', cb);
});
