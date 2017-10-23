var gulp = require('gulp');

var pump = require('pump');

var extrasConfig = require('../config.js').extrasConfig;


gulp.task('extras', ['extras:fonts', 'extras:root']);

gulp.task('extras:fonts', function(cb) {
    pump([
        gulp.src(extrasConfig.fonts.files),
        gulp.dest(extrasConfig.fonts.dest)
    ], cb);
});

gulp.task('extras:root', function(cb) {
    pump([
        gulp.src(extrasConfig.root.files),
        gulp.dest(extrasConfig.root.dest)
    ], cb);
});
