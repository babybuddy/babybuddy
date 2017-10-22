/* Baby Buddy Timer
 *
 * Uses a supplied ID to run a timer. The element using the ID must have
 * three children with the following classes:
 *  * timer-seconds
 *  * timer-minutes
 *  * timer-hours
 */
BabyBuddy.Timer = function ($) {
    var runIntervalId = null;
    var timerElement = null;

    var Timer = {
        run: function(id) {
            timerElement = $('#' + id);

            if (timerElement.length == 0) {
                console.error('BBTimer: Timer element not found.');
                return false;
            }

            if (timerElement.find('.timer-seconds').length == 0
                || timerElement.find('.timer-minutes').length == 0
                || timerElement.find('.timer-hours').length == 0) {
                console.error('BBTimer: Element does not contain expected children.');
                return false;
            }

            runIntervalId = setInterval(this.tick, 1000);
            return runIntervalId;
        },

        tick: function() {
            var s = timerElement.find('.timer-seconds');
            var seconds = Number(s.text());
            if (seconds < 59) {
                s.text(seconds + 1);
                return;
            }
            else {
                s.text(0);
            }

            var m = timerElement.find('.timer-minutes');
            var minutes = Number(m.text());
            if (minutes < 59) {
                m.text(minutes + 1);
                return;
            }
            else {
                m.text(0);
            }

            var h = timerElement.find('.timer-hours');
            var hours = Number(h.text());
            h.text(hours + 1);
        }
    };

    return Timer;
}(jQuery);
