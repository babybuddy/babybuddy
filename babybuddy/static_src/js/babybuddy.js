if (typeof jQuery === 'undefined') {
  throw new Error('Baby Buddy requires jQuery.')
}
if (typeof moment === 'undefined') {
  throw new Error('Baby Buddy requires moment.js.')
}

/**
 * Baby Buddy Namespace
 *
 * Default namespace for the Baby Buddy app.
 */
var BabyBuddy = function () {
    return {};
}();

/**
 * Baby Buddy Datetime Picker
 *
 * Provides modifications and defaults for the base datetime picker widget.
 */
BabyBuddy.DatetimePicker = function ($, moment) {
    return {
        init: function (element, options) {
            var defaultOptions = {
                allowInputToggle: true,
                buttons: { showToday: true, showClose: true },
                defaultDate: 'now',
                format: 'L LT',
                ignoreReadonly: true,
                locale: moment.locale(),
                useCurrent: false
            };
            element.datetimepicker($.extend(defaultOptions, options));
        }
    };
}(jQuery, moment);
