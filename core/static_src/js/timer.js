/* Baby Buddy Timer
 *
 * Uses a supplied ID to run a timer. The element using the ID must have
 * three children with the following classes:
 *  * timer-seconds
 *  * timer-minutes
 *  * timer-hours
 */
BabyBuddy.Timer = (function ($) {
  var runIntervalId = null;
  var timerId = null;
  var timerElement = null;
  var lastUpdate = new Date();
  var hidden = null;

  var Timer = {
    run: function (timer_id, element_id) {
      timerId = timer_id;
      timerElement = $("#" + element_id);

      if (timerElement.length === 0) {
        console.error("BBTimer: Timer element not found.");
        return false;
      }

      if (
        timerElement.find(".timer-seconds").length === 0 ||
        timerElement.find(".timer-minutes").length === 0 ||
        timerElement.find(".timer-hours").length === 0
      ) {
        console.error("BBTimer: Element does not contain expected children.");
        return false;
      }

      runIntervalId = setInterval(this.tick, 1000);

      // If the page just came in to view, update the timer data with the
      // current actual duration. This will (potentially) help mobile
      // phones that lock with the timer page open.
      if (typeof document.hidden !== "undefined") {
        hidden = "hidden";
      } else if (typeof document.msHidden !== "undefined") {
        hidden = "msHidden";
      } else if (typeof document.webkitHidden !== "undefined") {
        hidden = "webkitHidden";
      }
      window.addEventListener("focus", Timer.handleVisibilityChange, false);
    },

    handleVisibilityChange: function () {
      if (!document[hidden] && new Date() - lastUpdate > 1) {
        Timer.update();
      }
    },

    tick: function () {
      var s = timerElement.find(".timer-seconds");
      var seconds = Number(s.text());
      if (seconds < 59) {
        s.text(seconds + 1);
        return;
      } else {
        s.text(0);
      }

      var m = timerElement.find(".timer-minutes");
      var minutes = Number(m.text());
      if (minutes < 59) {
        m.text(minutes + 1);
        return;
      } else {
        m.text(0);
      }

      var h = timerElement.find(".timer-hours");
      var hours = Number(h.text());
      h.text(hours + 1);
    },

    update: function () {
      $.get("/api/timers/" + timerId + "/", function (data) {
        if (data && "duration" in data) {
          clearInterval(runIntervalId);
          var duration = data.duration.split(/[\s:.]/);
          if (duration.length === 5) {
            duration[0] = parseInt(duration[0]) * 24 + parseInt(duration[1]);
            duration[1] = duration[2];
            duration[2] = duration[3];
          }
          timerElement.find(".timer-hours").text(parseInt(duration[0]));
          timerElement.find(".timer-minutes").text(parseInt(duration[1]));
          timerElement.find(".timer-seconds").text(parseInt(duration[2]));
          lastUpdate = new Date();
          runIntervalId = setInterval(Timer.tick, 1000);
        }
      });
    },
  };

  return Timer;
})(jQuery);

/* Baby Buddy Screen Wake Lock
 *
 * Keeps the device screen on while a timer page is open, via the Screen
 * Wake Lock API. The toggle state persists in sessionStorage so it is
 * restored on every timer page during the same browser session. The lock
 * is re-acquired automatically when the page becomes visible again
 * (browsers release wake locks on tab switch / minimize) and released
 * when the toggle is turned off or the page is left.
 */
BabyBuddy.WakeLock = (function () {
  var sentinel = null;
  var checkbox = null;
  var storageKey = "babybuddy:keep-screen-on";

  function acquire() {
    navigator.wakeLock
      .request("screen")
      .then(function (lock) {
        sentinel = lock;
      })
      .catch(function (error) {
        // Browsers refuse e.g. in battery saver mode. Reflect reality in
        // the UI instead of pretending the screen will stay on.
        console.warn("BBWakeLock: request failed:", error);
        checkbox.checked = false;
        window.sessionStorage.setItem(storageKey, "false");
      });
  }

  function release() {
    if (sentinel !== null) {
      sentinel.release();
      sentinel = null;
    }
  }

  var WakeLock = {
    init: function (checkbox_id, container_id) {
      checkbox = document.getElementById(checkbox_id);
      if (!checkbox) {
        console.error("BBWakeLock: Checkbox element not found.");
        return false;
      }

      if (!("wakeLock" in navigator)) {
        // Unsupported browser (or insecure context): hide the toggle
        // entirely rather than offering a control that cannot work.
        var container = document.getElementById(container_id);
        if (container) {
          container.hidden = true;
        }
        return false;
      }

      checkbox.addEventListener("change", function () {
        window.sessionStorage.setItem(storageKey, String(checkbox.checked));
        if (checkbox.checked) {
          acquire();
        } else {
          release();
        }
      });

      // Wake locks are released by the browser when the page is hidden;
      // re-acquire when it becomes visible again and the toggle is on.
      document.addEventListener("visibilitychange", function () {
        if (document.visibilityState === "visible" && checkbox.checked) {
          acquire();
        }
      });

      if (window.sessionStorage.getItem(storageKey) === "true") {
        checkbox.checked = true;
        acquire();
      }
    },
  };

  return WakeLock;
})();
