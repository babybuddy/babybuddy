const basePath = "babybuddy/static/babybuddy/";

const config = {
  basePath: basePath,
  extrasConfig: {
    fonts: {
      dest: basePath + "font/",
      files: "babybuddy/static_src/fontello/font/*",
    },
    images: {
      dest: basePath + "img/",
      files: "**/static_src/img/**/*",
    },
    logo: {
      dest: basePath + "logo/",
      files: "babybuddy/static_src/logo/**/*",
    },
    root: {
      dest: basePath + "root/",
      files: "babybuddy/static_src/root/*",
    },
  },
  glyphFontConfig: {
    configFile: "babybuddy/static_src/fontello/config.json",
    dest: "babybuddy/static_src/fontello",
  },
  scriptsConfig: {
    dest: basePath + "js/",
    vendor: [
      "node_modules/pulltorefreshjs/dist/index.umd.js",
      "node_modules/jquery/dist/jquery.js",
      "node_modules/@popperjs/core/dist/umd/popper.js",
      "node_modules/bootstrap/dist/js/bootstrap.js",
      "node_modules/masonry-layout/dist/masonry.pkgd.js",
    ],
    graph: [
      "node_modules/plotly.js/dist/plotly-cartesian.js",
      "node_modules/plotly.js/dist/plotly-locale-ca.js",
      "node_modules/plotly.js/dist/plotly-locale-cs.js",
      "node_modules/plotly.js/dist/plotly-locale-de.js",
      "node_modules/plotly.js/dist/plotly-locale-da.js",
      "node_modules/plotly.js/dist/plotly-locale-es.js",
      "node_modules/plotly.js/dist/plotly-locale-fi.js",
      "node_modules/plotly.js/dist/plotly-locale-fr.js",
      "node_modules/plotly.js/dist/plotly-locale-he.js",
      "node_modules/plotly.js/dist/plotly-locale-hr.js",
      "node_modules/plotly.js/dist/plotly-locale-hu.js",
      "node_modules/plotly.js/dist/plotly-locale-it.js",
      "node_modules/plotly.js/dist/plotly-locale-ja.js",
      "node_modules/plotly.js/dist/plotly-locale-no.js",
      "node_modules/plotly.js/dist/plotly-locale-nl.js",
      "node_modules/plotly.js/dist/plotly-locale-pl.js",
      "node_modules/plotly.js/dist/plotly-locale-pt-br.js",
      "node_modules/plotly.js/dist/plotly-locale-pt-pt.js",
      "node_modules/plotly.js/dist/plotly-locale-ru.js",
      "node_modules/plotly.js/dist/plotly-locale-sr.js",
      "node_modules/plotly.js/dist/plotly-locale-sv.js",
      "node_modules/plotly.js/dist/plotly-locale-tr.js",
      "node_modules/plotly.js/dist/plotly-locale-uk.js",
      "node_modules/plotly.js/dist/plotly-locale-zh-cn.js",
    ],
    app: [
      "babybuddy/static_src/js/babybuddy.js",
      "core/static_src/js/*.js",
      "dashboard/static_src/js/*.js",
    ],
    tags_editor: ["babybuddy/static_src/js/tags_editor.js"],
  },
  stylesConfig: {
    dest: basePath + "css/",
    app: "babybuddy/static_src/scss/babybuddy.scss",
    ignore: ["babybuddy.scss"],
  },
  testsConfig: {
    isolated: ["babybuddy.tests.tests_views.ViewsTestCase.test_password_reset"],
  },
  watchConfig: {
    scriptsGlob: ["*/static_src/js/**/*.js", "!babybuddy/static/js/"],
    stylesGlob: ["*/static_src/scss/**/*.scss"],
  },
};

export default config;
