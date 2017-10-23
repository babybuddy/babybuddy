var gulp = require('gulp');

var runSequence = require('run-sequence');


gulp.task('default', function(cb) {
  runSequence(['build', 'watch'], 'runserver', cb);
});
