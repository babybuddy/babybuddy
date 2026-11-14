/* Warn about weights likely entered in grams before the form is submitted. */
(function weightUnitWarning($) {
  var weight = $("#id_weight");
  var warning = $("#weight-unit-warning");

  if (!weight.length || !warning.length) return;

  function updateWarning() {
    warning.toggleClass("d-none", !(Number(weight.val()) > 1000));
  }

  weight.on("input change", updateWarning);
  updateWarning();
})(jQuery);
