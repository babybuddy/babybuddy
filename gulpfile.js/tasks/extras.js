var gulp = require('gulp');

var flatten = require('gulp-flatten');
var pump = require('pump');

var extrasConfig = require('../config.js').extrasConfig;


gulp.task('extras', ['extras:fonts', 'extras:images', 'extras:root']);

gulp.task('extras:fonts', function(cb) {
    pump([
        gulp.src(extrasConfig.fonts.files),
        gulp.dest(extrasConfig.fonts.dest)
    ], cb);
});

gulp.task('extras:images', function(cb) {
    pump([
        gulp.src(extrasConfig.images.files),
        flatten({ subPath: 3 }),
        gulp.dest(extrasConfig.images.dest)
    ], cb);
});

gulp.task('extras:root', function(cb) {
    pump([
        gulp.src(extrasConfig.root.files),
        gulp.dest(extrasConfig.root.dest)
    ], cb);
});
