/* Baby Buddy Dashboard
 *
 * Provides a "watch" function to update the dashboard at one minute intervals
 * and/or on visibility state changes.
 */
BabyBuddy.Dashboard = function ($) {
    var runIntervalId = null;
    var dashboardElement = null;
    var lastUpdate = moment();

    var Dashboard = {
        watch: function(element_id, refresh_rate) {
            dashboardElement = $('#' + element_id);

            if (dashboardElement.length == 0) {
                console.error('Baby Buddy: Dashboard element not found.');
                return false;
            }

            runIntervalId = setInterval(this.update, refresh_rate);

            Visibility.change(function (e, state) {
                if (state == 'visible' && moment().diff(lastUpdate) > 60000) {
                    Dashboard.update();
                }
            });
        },

        update: function() {
            // TODO: Someday maybe update in place?
            location.reload();
        }
    };

    return Dashboard;
}(jQuery);
