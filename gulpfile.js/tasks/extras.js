var gulp = require('gulp');

var pump = require('pump');

var extrasConfig = require('../config.js').extrasConfig;


gulp.task('extras', ['extras:fonts']);

gulp.task('extras:fonts', function(cb) {
    pump([
        gulp.src(extrasConfig.fonts.extras),
        gulp.dest(extrasConfig.fonts.dest)
    ], cb);
});
