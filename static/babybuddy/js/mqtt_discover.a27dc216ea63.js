(function () {
  "use strict";

  var HOST_FIELD_ID = "id_mqtt.settings____broker_host";
  var PORT_FIELD_ID = "id_mqtt.settings____broker_port";
  var DISCOVER_URL = "/api/mqtt/discover";

  var hostInput = document.getElementById(HOST_FIELD_ID);
  if (!hostInput) return;

  var portInput = document.getElementById(PORT_FIELD_ID);
  var inputCol = hostInput.parentElement;

  var group = document.createElement("div");
  group.className = "input-group";
  hostInput.parentNode.insertBefore(group, hostInput);
  group.appendChild(hostInput);

  var btn = document.createElement("button");
  btn.type = "button";
  btn.className = "btn btn-outline-secondary";
  btn.innerHTML =
    '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">' +
    '<path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85zm-5.242.656a5 5 0 1 1 0-10 5 5 0 0 1 0 10z"/>' +
    "</svg>";
  btn.title = "Discover MQTT brokers on the network";
  group.appendChild(btn);

  var resultsDiv = document.createElement("div");
  resultsDiv.style.display = "none";
  resultsDiv.style.position = "relative";
  inputCol.appendChild(resultsDiv);

  btn.addEventListener("click", function () {
    btn.disabled = true;
    btn.innerHTML =
      '<span class="spinner-border spinner-border-sm" role="status"></span>';
    resultsDiv.style.display = "none";
    resultsDiv.innerHTML = "";

    var csrfToken = "";
    var csrfMeta = document.querySelector("[name=csrfmiddlewaretoken]");
    if (csrfMeta) csrfToken = csrfMeta.value;

    fetch(DISCOVER_URL, {
      headers: {
        "X-CSRFToken": csrfToken,
        Accept: "application/json",
      },
      credentials: "same-origin",
    })
      .then(function (resp) {
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        return resp.json();
      })
      .then(function (brokers) {
        resetBtn();

        if (!brokers.length) {
          resultsDiv.style.display = "block";
          resultsDiv.innerHTML =
            '<small class="text-muted d-block mt-1">No brokers found.</small>';
          return;
        }

        var list = document.createElement("div");
        list.className = "list-group mt-1";
        list.style.maxWidth = "100%";

        brokers.forEach(function (b) {
          var item = document.createElement("a");
          item.href = "#";
          item.className = "list-group-item list-group-item-action py-1 px-2";
          item.style.fontSize = "0.85em";

          var host = document.createElement("strong");
          host.textContent = b.host + ":" + b.port;
          item.appendChild(host);

          if (b.source) {
            var badge = document.createElement("span");
            badge.className = "badge bg-secondary ms-2";
            badge.style.fontWeight = "normal";
            badge.textContent = b.source;
            item.appendChild(badge);
          }

          if (b.name) {
            var nameSpan = document.createElement("span");
            nameSpan.className = "text-muted ms-2";
            nameSpan.textContent = b.name;
            item.appendChild(nameSpan);
          }

          item.addEventListener("click", function (e) {
            e.preventDefault();
            hostInput.value = b.host;
            if (portInput) portInput.value = b.port;
            resultsDiv.style.display = "none";
          });
          list.appendChild(item);
        });

        resultsDiv.innerHTML = "";
        resultsDiv.appendChild(list);
        resultsDiv.style.display = "block";
      })
      .catch(function (err) {
        resetBtn();
        resultsDiv.style.display = "block";
        resultsDiv.innerHTML =
          '<small class="text-danger d-block mt-1">Discovery failed: ' +
          err.message +
          "</small>";
      });
  });

  function resetBtn() {
    btn.disabled = false;
    btn.innerHTML =
      '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">' +
      '<path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85zm-5.242.656a5 5 0 1 1 0-10 5 5 0 0 1 0 10z"/>' +
      "</svg>";
  }
})();
