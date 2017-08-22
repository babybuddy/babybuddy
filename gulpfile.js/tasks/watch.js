var gulp = require('gulp');

var watchConfig = require('../config.js').watchConfig;


gulp.task('watch', ['watch:scripts', 'watch:styles']);

gulp.task('watch:scripts', function() {
    return gulp.watch(watchConfig.scriptsGlob, ['scripts:app']);
});

gulp.task('watch:styles', function() {
    return gulp.watch(watchConfig.stylesGlob, ['styles:app']);
});
