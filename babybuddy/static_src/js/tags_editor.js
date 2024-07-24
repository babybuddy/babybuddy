(function () {
  /**
   * Parse a string as hexadecimal number
   */
  function hexParse(x) {
    return parseInt(x, 16);
  }

  /**
   * Get the contrasting color for any hex color
   *
   * Sourced from: https://vanillajstoolkit.com/helpers/getcontrast/
   *  - Modified with slightly softer colors
   * (c) 2021 Chris Ferdinandi, MIT License, https://gomakethings.com
   * Derived from work by Brian Suda, https://24ways.org/2010/calculating-color-contrast/
   * @param  {String} A hexcolor value
   * @return {String} The contrasting color (black or white)
   */
  function computeComplementaryColor(hexcolor) {
    // If a leading # is provided, remove it
    if (hexcolor.slice(0, 1) === "#") {
      hexcolor = hexcolor.slice(1);
    }

    // If a three-character hexcode, make six-character
    if (hexcolor.length === 3) {
      hexcolor = hexcolor
        .split("")
        .map(function (hex) {
          return hex + hex;
        })
        .join("");
    }

    // Convert to RGB value
    let r = parseInt(hexcolor.substr(0, 2), 16);
    let g = parseInt(hexcolor.substr(2, 2), 16);
    let b = parseInt(hexcolor.substr(4, 2), 16);

    // Get YIQ ratio
    let yiq = (r * 299 + g * 587 + b * 114) / 1000;

    // Check contrast
    return yiq >= 128 ? "#101010" : "#EFEFEF";
  }

  // CSRF token should always be present because it is auto-included with
  // every tag-editor widget
  const CSRF_TOKEN = document.querySelector(
    'input[name="csrfmiddlewaretoken"]',
  ).value;

  function doReq(method, uri, data, success, fail) {
    const req = new XMLHttpRequest();
    req.addEventListener("load", () => {
      if (req.status >= 200 && req.status < 300) {
        success(req.responseText, req);
      } else {
        fail(req.responseText, req);
      }
    });
    for (const name of ["error", "timeout", "abort"]) {
      req.addEventListener(name, () => {
        fail(req.responseText, req);
      });
    }
    req.timeout = 20000;

    req.open(method, uri);
    req.setRequestHeader("Content-Type", "application/json");
    req.setRequestHeader("Accept", "application/json");
    req.setRequestHeader("X-CSRFTOKEN", CSRF_TOKEN);
    req.send(data);
  }

  /**
   * Base class allowing generic operations on the tag lists, like:
   *
   * - Adding tags to a tag list
   * - Updating or creating new tags with a set name and color
   * - Controlling the error modal
   */
  class TaggingBase {
    constructor(widget) {
      this.prototype = widget.querySelector(".prototype-tag");
      this.listeners = [];

      this.modalElement = widget.querySelector(".tag-editor-error-modal");
      this.modalBodyNode = this.modalElement.querySelector(".modal-body");

      // Clean whitespace text nodes between spans
      for (const n of this.modalBodyNode.childNodes) {
        if (n.nodeType === Node.TEXT_NODE) {
          this.modalBodyNode.removeChild(n);
        }
      }
    }

    showModal(msg) {
      const selectedMessage = this.modalBodyNode.querySelector(
        `span[data-message='${msg}']`,
      );
      if (!selectedMessage) {
        selectedMessage = this.modalBodyNode.childNodes[0];
      }

      for (const n of this.modalBodyNode.childNodes) {
        n.classList.add("d-none");
      }
      selectedMessage.classList.remove("d-none");

      jQuery(this.modalElement).modal("show");
    }

    addTagListUpdatedListener(c) {
      this.listeners.push(c);
    }

    callTagListUpdatedListeners() {
      for (const l of this.listeners) {
        l();
      }
    }

    updateTag(tag, name, color, actionSymbol) {
      const actionTextNode =
        tag.querySelector(".add-remove-icon").childNodes[0];

      name = name || tag.getAttribute("data-value");
      color = color || tag.getAttribute("data-color");
      actionSymbol = actionSymbol || actionTextNode.textContent;

      tag.childNodes[0].textContent = name;
      tag.setAttribute("data-value", name);
      tag.setAttribute("data-color", color);

      const textColor = computeComplementaryColor(color);
      tag.setAttribute(
        "style",
        `background-color: ${color}; color: ${textColor};`,
      );
      actionTextNode.textContent = actionSymbol;
    }

    createNewTag(name, color, actionSymbol) {
      const tag = this.prototype.cloneNode(true);
      tag.classList.remove("prototype-tag");
      tag.classList.add("tag");
      this.updateTag(tag, name, color, actionSymbol);
      return tag;
    }

    insertTag(list, tag) {
      list.appendChild(tag);
      this.callTagListUpdatedListeners();
    }
  }

  /**
   * Handler for the edit field allowing to dynamically create new tags.
   *
   * Handles user inputs for the editor. Calls the 'onInsertNewTag' callback
   * when the creation of a new tag has been requested. All backend handling
   * like guareteening that the requested tag exists is handled by this class,
   * the only task left is to add the new tag to the tags-list when
   * 'onInsertNewTag' is called.
   */
  class AddNewTagControl {
    /**
     * @param widget
     *     The root DOM element of the widget
     * @param taggingBase
     *     Reference to a common TaggingBase class to be used by this widget
     * @param onInsertNewTag
     *     Callback that is called when a new tag should be added to the
     *     tags widget.
     */
    constructor(widget, taggingBase, onInsertNewTag) {
      this.widget = widget;
      this.taggingBase = taggingBase;

      this.apiTagsUrl = widget.getAttribute("data-tags-url");
      this.createTagInputs = widget.querySelector(".create-tag-inputs");
      this.addTagInput =
        this.createTagInputs.querySelector('input[type="text"]');
      this.addTagButton = this.createTagInputs.querySelector("#add-tag");

      this.addTagInput.value = "";

      this.onInsertNewTag = onInsertNewTag;

      this.addTagButton.addEventListener("click", () =>
        this.onCreateTagClicked(),
      );
      this.addTagInput.addEventListener("keydown", (e) => {
        const key = e.key.toLowerCase();
        if (key === "enter") {
          e.preventDefault();
          this.onCreateTagClicked();
        }
      });
    }

    /**
     * Callback called when the "Add" button of the add-tag input is
     * clicked or enter is pressed in the editor.
     */
    onCreateTagClicked() {
      // TODO: Make promise based

      const tagName = this.addTagInput.value.trim();
      const uriTagName = encodeURIComponent(tagName);

      const fail = (msg) => {
        this.addTagInput.select();
        this.taggingBase.showModal(msg || "generic");
      };

      if (!tagName) {
        fail("invalid-tag-name");
        return;
      }

      const addTag = (name, color) => {
        const tag = this.taggingBase.createNewTag(name, color, "-");
        this.addTagInput.value = "";
        this.onInsertNewTag(tag);
      };

      const data = JSON.stringify({
        name: this.addTagInput.value,
      });

      doReq(
        "GET",
        `${this.apiTagsUrl}?name=${uriTagName}`,
        null,
        (text) => {
          const json = JSON.parse(text);
          if (json.count) {
            const tagJson = json.results[0];
            addTag(tagJson.name, tagJson.color);
          } else {
            doReq(
              "POST",
              this.apiTagsUrl,
              data,
              (text) => {
                const tagJson = JSON.parse(text);
                addTag(tagJson.name, tagJson.color);
              },
              () => fail("tag-creation-failed"),
            );
          }
        },
        () => fail("tag-checking-failed"),
      );
    }
  }

  /**
   * JavaScript implementation for the tags editor.
   *
   * This class uses TaggingBase and AddNewTagControl to provide the custom
   * tag editor controls. This mainly consists of updating the hidden
   * input values with the current list of tags and adding/removing
   * tags from the current-tags- or recently-used-lists.
   */
  class TagsEditor {
    /**
     * @param tagEditorRoot
     *     The root DOM element of the widget.
     */
    constructor(tagEditorRoot) {
      this.widget = tagEditorRoot;
      this.taggingBase = new TaggingBase(this.widget);
      this.addTagControl = new AddNewTagControl(
        this.widget,
        this.taggingBase,
        (t) => this.insertNewTag(t),
      );

      this.currentTags = this.widget.querySelector(".current_tags");
      this.newTags = this.widget.querySelector(".new-tags");
      this.inputElement = this.widget.querySelector('input[type="hidden"]');

      for (const tag of this.newTags.querySelectorAll(".tag")) {
        this.configureAddTag(tag);
      }
      for (const tag of this.currentTags.querySelectorAll(".tag")) {
        this.configureRemoveTag(tag);
      }

      this.updateInputList();
      this.taggingBase.addTagListUpdatedListener(() => this.updateInputList());
    }

    /**
     * Insert a new tag into the "current tag" list.
     *
     * Makes sure that no duplicates are present in the widget before adding
     * the new tag. If a duplicate is found, the old tag is removed before
     * the new one is added.
     */
    insertNewTag(tag) {
      const name = tag.getAttribute("data-value");

      const oldTag = this.widget.querySelector(`span[data-value="${name}"]`);
      if (oldTag) {
        oldTag.parentNode.removeChild(oldTag);
      }

      this.taggingBase.insertTag(this.currentTags, tag);
      this.configureRemoveTag(tag);
    }

    /**
     * Registeres a click-callback for a given node.
     *
     * The callback chain-calls another callback "onClicked" after
     * moving the clicked tag from the old tag-list to a new tag list.
     */
    registerNewCallback(tag, newParent, onClicked) {
      function callback(event) {
        tag.parentNode.removeChild(tag);
        this.taggingBase.insertTag(newParent, tag);

        tag.removeEventListener("click", callback);
        onClicked(tag);
      }
      tag.addEventListener("click", callback.bind(this));
    }

    /**
     * Updates the value of the hidden input element.
     *
     * Sets the value from the list of tags added to the currentTags
     * DOM element.
     */
    updateInputList() {
      const names = [];
      for (const tag of this.currentTags.querySelectorAll(".tag")) {
        const name = tag.getAttribute("data-value");
        names.push(`"${name}"`);
      }
      this.inputElement.value = names.join(",");
    }

    /**
     * Configure a tag-DOM element as a "add tag" button.
     */
    configureAddTag(tag) {
      this.taggingBase.updateTag(tag, null, null, "+");
      this.registerNewCallback(tag, this.currentTags, () =>
        this.configureRemoveTag(tag),
      );
      this.updateInputList();
    }

    /**
     * Configure a tag-DOM element as a "remove tag" button.
     */
    configureRemoveTag(tag) {
      this.taggingBase.updateTag(tag, null, null, "-");
      this.registerNewCallback(tag, this.newTags, () =>
        this.configureAddTag(tag),
      );
      this.updateInputList();
    }
  }

  window.addEventListener("load", () => {
    for (const el of document.querySelectorAll(".babybuddy-tags-editor")) {
      new TagsEditor(el);
    }
  });
})();
