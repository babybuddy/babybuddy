var gulp = require('gulp');

var spawn = require('child_process').spawn;


gulp.task('test', function(cb) {
    spawn(
        'pipenv',
        [
            'run',
            'python',
            'manage.py',
            'test'
        ],
        {
            stdio: 'inherit'
        }
    ).on('exit', cb);
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
