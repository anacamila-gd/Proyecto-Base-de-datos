const gulp = require('gulp');
const sass = require('gulp-sass')(require('sass'));

// Compilar SCSS → CSS
function compilarSass() {
  return gulp.src('scss/main.scss')
    .pipe(sass({ outputStyle: 'compressed' }).on('error', sass.logError))
    .pipe(gulp.dest('static/css'));
}

// Vigilar cambios en SCSS
function vigilar() {
  gulp.watch('scss/**/*.scss', compilarSass);
}

// Tareas
exports.build   = compilarSass;
exports.default = gulp.series(compilarSass, vigilar);
