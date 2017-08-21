var gulp = require('gulp');


gulp.task('watch', ['watch:scripts', 'watch:styles']);

gulp.task('watch:scripts', function() {
    return gulp.watch([
        '**/static/js/**/*.js',
        '!babyblotter/static/js/'
    ], ['scripts:app']);
});

gulp.task('watch:styles', function() {
    return gulp.watch('**/static/scss/**/*.scss', ['styles:app']);
});
