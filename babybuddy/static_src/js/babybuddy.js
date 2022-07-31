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
 *
 * @type {{}}
 */
var BabyBuddy = function () {
    return {};
}();

/**
 * Datetime Picker.
 *
 * Provides modifications and defaults for the base datetime picker widget.
 *
 * @type {{init: BabyBuddy.DatetimePicker.init}}
 */
BabyBuddy.DatetimePicker = function (moment) {
    return {
        init: function (element, options) {
            let defaultOptions = {
                display: {
                    buttons: {
                        close: true,
                        today: true,
                    },
                    components: {
                        calendar: true,
                        clock: true,
                        date: true,
                        decades: true,
                        hours: true,
                        minutes: true,
                        month: true,
                        seconds: false,
                        useTwentyfourHour: false,
                        year: true,
                    },
                    icons: {
                        clear: 'icon-delete',
                        close: 'icon-cancel',
                        date: 'icon-calendar',
                        down: 'icon-arrow-down',
                        next: 'icon-angle-circled-right',
                        previous: 'icon-angle-circled-left',
                        time: 'icon-clock',
                        today: 'icon-today',
                        up: 'icon-arrow-up',
                    },
                    viewMode: 'clock',
                },
                localization: {
                    locale: moment.locale(),
                },
            };

            new tempusDominus.TempusDominus(element, Object.assign(defaultOptions, options));
        }
    };
}(moment);

/**
 * Pull to refresh.
 *
 * @type {{init: BabyBuddy.PullToRefresh.init, onRefresh: BabyBuddy.PullToRefresh.onRefresh}}
 */
BabyBuddy.PullToRefresh = function(ptr) {
    return {
        init: function () {
            ptr.init({
                mainElement: 'body',
                onRefresh: this.onRefresh
            });
        },

        onRefresh: function() {
            window.location.reload();
        }
    };
}(PullToRefresh);

/**
 * Fix for duplicate form submission from double pressing submit
 */
function preventDoubleSubmit() {
    return false;
}
$('form').off("submit", preventDoubleSubmit);
$("form").on("submit", function() {
    $(this).on("submit", preventDoubleSubmit);
});
