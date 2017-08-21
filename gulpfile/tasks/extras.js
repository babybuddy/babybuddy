var gulp = require('gulp');


gulp.task('extras', ['extras:fonts']);

gulp.task('extras:fonts', function(cb) {
    pump([
        gulp.src('node_modules/font-awesome/fonts/*'),
        gulp.dest('babyblotter/static/babyblotter/fonts/')
    ], cb);
});