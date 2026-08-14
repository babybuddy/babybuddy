if (typeof jQuery === "undefined") {
  throw new Error("Baby Buddy requires jQuery.");
}

/**
 * Baby Buddy Namespace
 *
 * Default namespace for the Baby Buddy app.
 *
 * @type {{}}
 */
var BabyBuddy = (function () {
  return {};
})();

/**
 * Run a callback on first paint and after every Turbo visit.
 *
 * turbo:load fires on the initial page load and after each Drive visit.
 * Fall back to DOMContentLoaded when Turbo is not present.
 *
 * @param {Function} callback
 */
BabyBuddy.onLoad = function (callback) {
  document.addEventListener("turbo:load", callback);
  if (typeof Turbo === "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback);
    } else {
      callback();
    }
  }
};

/**
 * Run a callback once the document is ready. Safe from inline body scripts
 * that execute during the first parse (before deferred vendor/app JS) and
 * from scripts Turbo evaluates after a Drive visit (document already ready).
 *
 * @param {Function} callback
 */
BabyBuddy.whenReady = function (callback) {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", callback);
  } else {
    callback();
  }
};

/**
 * Disable Turbo Drive on forms that cannot be visited safely (file uploads).
 * Login/logout are opted out in templates.
 */
BabyBuddy.markUnsafeForms = function () {
  document.querySelectorAll("form").forEach(function (form) {
    if (form.querySelector('input[type="file"]')) {
      form.setAttribute("data-turbo", "false");
    }
  });
};

/**
 * Restore advanced fieldsets the user left open.
 */
BabyBuddy.initAdvancedFields = function () {
  if (localStorage.getItem("advancedForm") !== "open") {
    return;
  }
  document.querySelectorAll(".advanced-fields").forEach(function (node) {
    node.open = true;
  });
};

/**
 * Re-init Masonry after Drive visits. The HTML API only runs on
 * DOMContentLoaded, which does not fire again under Turbo.
 */
BabyBuddy.initMasonry = function (attempt) {
  var nodes = document.querySelectorAll("[data-masonry]");
  if (!nodes.length) {
    return;
  }
  if (!(window.jQuery && jQuery.fn.masonry) && typeof Masonry === "undefined") {
    if ((attempt || 0) < 20) {
      setTimeout(function () {
        BabyBuddy.initMasonry((attempt || 0) + 1);
      }, 50);
    }
    return;
  }
  if (window.jQuery && jQuery.fn.masonry) {
    jQuery(nodes).each(function () {
      var $el = jQuery(this);
      var options = {};
      try {
        options = JSON.parse(this.getAttribute("data-masonry") || "{}");
      } catch (e) {
        options = {};
      }
      if ($el.data("masonry")) {
        $el.masonry("destroy");
      }
      $el.masonry(options);
    });
    return;
  }
  if (typeof Masonry === "undefined") {
    return;
  }
  nodes.forEach(function (el) {
    var options = {};
    try {
      options = JSON.parse(el.getAttribute("data-masonry") || "{}");
    } catch (e) {
      options = {};
    }
    new Masonry(el, options);
  });
};

/**
 * Start dashboard watch / timer from data attributes so they survive
 * cached back/forward visits (inline scripts are not re-run from cache).
 */
BabyBuddy.initPageWidgets = function () {
  var dashboard = document.querySelector("[data-dashboard-watch]");
  if (dashboard && BabyBuddy.Dashboard) {
    var rate = dashboard.getAttribute("data-refresh-rate");
    BabyBuddy.Dashboard.watch(dashboard.id, rate ? Number(rate) : false);
  }
  var timer = document.querySelector("[data-timer-id]");
  if (timer && BabyBuddy.Timer) {
    BabyBuddy.Timer.run(timer.getAttribute("data-timer-id"), timer.id);
  }
  if (window.Plotly) {
    document.querySelectorAll(".js-plotly-plot").forEach(function (el) {
      try {
        Plotly.Plots.resize(el);
      } catch (e) {
        /* Plot may not be fully constructed yet. */
      }
    });
  }
};

/**
 * Tear down listeners and injected DOM before Turbo caches the page.
 */
BabyBuddy.teardownPage = function () {
  if (BabyBuddy.PullToRefresh) {
    BabyBuddy.PullToRefresh.destroy();
  }
  if (BabyBuddy.Dashboard) {
    BabyBuddy.Dashboard.stop();
  }
  if (BabyBuddy.Timer) {
    BabyBuddy.Timer.stop();
  }
  if (window.bootstrap) {
    document.querySelectorAll(".modal").forEach(function (el) {
      var modal = bootstrap.Modal.getInstance(el);
      if (modal) {
        modal.hide();
        modal.dispose();
      }
    });
    document
      .querySelectorAll('[data-bs-toggle="dropdown"]')
      .forEach(function (el) {
        var dropdown = bootstrap.Dropdown.getInstance(el);
        if (dropdown) {
          dropdown.hide();
          dropdown.dispose();
        }
      });
  }
  document.querySelectorAll(".modal-backdrop").forEach(function (el) {
    el.remove();
  });
};

/**
 * Pull to refresh.
 *
 * @type {{init: BabyBuddy.PullToRefresh.init, destroy: BabyBuddy.PullToRefresh.destroy, onRefresh: BabyBuddy.PullToRefresh.onRefresh}}
 */
BabyBuddy.PullToRefresh = (function (ptr) {
  var instance = null;
  return {
    init: function () {
      this.destroy();
      instance = ptr.init({
        mainElement: "body",
        onRefresh: this.onRefresh,
      });
    },

    destroy: function () {
      if (instance && typeof instance.destroy === "function") {
        instance.destroy();
        instance = null;
      }
    },

    onRefresh: function () {
      if (window.Turbo) {
        Turbo.visit(window.location.href, { action: "replace" });
      } else {
        window.location.reload();
      }
    },
  };
})(PullToRefresh);

/**
 * Show a loading spinner on the submit button when a form is submitted and
 * prevent double-submission. Delegated so it survives Turbo Drive visits.
 */
(function handleFormSubmit() {
  $(document).on("submit", "form", function (event) {
    var submitter =
      (event.originalEvent && event.originalEvent.submitter) ||
      $(this).find('[type="submit"]')[0];
    if (!submitter || $(submitter).prop("disabled")) return;
    $(submitter)
      .prop("disabled", true)
      .prepend(
        '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>',
      );
  });
})();

BabyBuddy.RememberAdvancedToggle = function (ptr) {
  localStorage.setItem("advancedForm", event.newState);
};

BabyBuddy.onLoad(function () {
  BabyBuddy.markUnsafeForms();
  BabyBuddy.initAdvancedFields();
  BabyBuddy.initMasonry();
  BabyBuddy.initPageWidgets();
  if (
    document.body &&
    document.body.getAttribute("data-authenticated") === "true"
  ) {
    BabyBuddy.PullToRefresh.init();
  }
});

document.addEventListener("turbo:before-cache", function () {
  BabyBuddy.teardownPage();
});
