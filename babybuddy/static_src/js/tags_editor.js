(function() {
    /**
     * Parse a string as hexadecimal number
     */
    function hexParse(x) {
        return parseInt(x, 16);
    }

    function computeComplementaryColor(colorStr) {
        let avgColor = 0.0;
        avgColor += hexParse(colorStr.substring(1, 3)) * -0.5;
        avgColor += hexParse(colorStr.substring(3, 5)) * 1.5;
        avgColor += hexParse(colorStr.substring(5, 7)) * 1.0;

        if (avgColor > 200) {
            return "#101010";
        } else {
            return "#E0E0E0";
        }
    }

    const CSRF_TOKEN = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

    function doReq(method, uri, data, success, fail) {
        // TODO: prefer jQuery based requests for now

        const req = new XMLHttpRequest();
        req.addEventListener('load', () => {
            if ((req.status >= 200) && (req.status < 300)) {
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

    class TaggingBase {
        constructor(widget) {
            this.prototype = widget.querySelector('.prototype-tag');
            this.listeners = [];

            this.modalElement = widget.querySelector('.tag-editor-error-modal');
            this.modalBodyNode = this.modalElement.querySelector('.modal-body');

            // Clean whitespace text nodes between spans
            for (const n of this.modalBodyNode.childNodes) {
                if (n.nodeType === Node.TEXT_NODE) {
                    this.modalBodyNode.removeChild(n);
                }
            }
        }

        showModal(msg) {
            const selectedMessage = this.modalBodyNode.querySelector(`span[data-message='${msg}']`);
            if (!selectedMessage) {
                selectedMessage = this.modalBodyNode.childNodes[0];
            }

            for (const n of this.modalBodyNode.childNodes) {
                n.classList.add('d-none');
            }
            selectedMessage.classList.remove('d-none');

            jQuery(this.modalElement).modal('show');
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
            const actionTextNode = tag.querySelector('.add-remove-icon').childNodes[0];

            name = name || tag.getAttribute("data-value");
            color = color || tag.getAttribute("data-color");
            actionSymbol = actionSymbol || actionTextNode.textContent;

            tag.childNodes[0].textContent = name;
            tag.setAttribute("data-value", name);
            tag.setAttribute("data-color", color);

            const textColor = computeComplementaryColor(color);
            tag.setAttribute('style', `background-color: ${color}; color: ${textColor};`);
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
    };

    /**
     * Handler for the edit field allowing to dynamically create new tags.
     */
    class AddNewTagControl {
        constructor(widget, taggingBase, onInsertNewTag) {
            this.widget = widget;
            this.taggingBase = taggingBase;

            this.apiTagsUrl = widget.getAttribute('data-tags-url');
            this.createTagInputs = widget.querySelector('.create-tag-inputs');
            this.addTagInput = this.createTagInputs.querySelector('input[type="text"]');
            this.addTagButton = this.createTagInputs.querySelector('.btn-add-new-tag');

            this.addTagInput.value = "";
            
            this.onInsertNewTag = onInsertNewTag;

            this.addTagButton.addEventListener('click', () => this.onCreateTagClicked());
            this.addTagInput.addEventListener('keydown', (e) => {
                const key = e.key.toLowerCase();
                if (key === "enter") {
                    e.preventDefault();
                    this.onCreateTagClicked();
                }
            });
        }

        /**
         * Callback called when the the "Add" button of the add-tag input is
         * clicked or enter is pressed in the editor.
         */
         onCreateTagClicked() {
            // TODO: Make promise based

            const tagName = this.addTagInput.value.trim();
            const uriTagName = encodeURIComponent(tagName);

            const fail = (msg) => {
                this.addTagInput.select();
                this.taggingBase.showModal(msg || "error-creating-tag");
            };

            if (!tagName) {
                fail('invalid-tag-name');
                return;
            }

            const addTag = (name, color) => {
                const tag = this.taggingBase.createNewTag(name, color, "-");                    
                this.addTagInput.value = "";
                this.onInsertNewTag(tag);
            };

            const data = JSON.stringify({
                'name': this.addTagInput.value
            });

            doReq("GET", `${this.apiTagsUrl}?name=${uriTagName}`, null,
                (text) => {
                    const json = JSON.parse(text);
                    if (json.count) {
                        const tagJson = json.results[0];
                        addTag(tagJson.name, tagJson.color);
                    } else {
                        doReq("POST", this.apiTagsUrl, data, 
                            (text) => {
                                const tagJson = JSON.parse(text);
                                addTag(tagJson.name, tagJson.color);
                            }, () => fail("tag-creation-failed")
                        );
                    }
                }, () => fail("tag-checking-failed")
            );
        }
    };

    class TagsEditor {
        constructor(tagEditorRoot) {
            this.widget = tagEditorRoot;
            this.taggingBase = new TaggingBase(this.widget);
            this.addTagControl = new AddNewTagControl(
                this.widget, this.taggingBase, (t) => this.insertNewTag(t)
            );
        
            this.currentTags = this.widget.querySelector('.current_tags');
            this.newTags = this.widget.querySelector('.new-tags');
            this.inputElement = this.widget.querySelector('input[type="hidden"]');
    
            for (const tag of this.newTags.querySelectorAll(".tag")) {
                this.configureAddTag(tag);
            }
            for (const tag of this.currentTags.querySelectorAll(".tag")) {
                this.configureRemoveTag(tag);
            }

            this.updateInputList();
            this.taggingBase.addTagListUpdatedListener(
                () => this.updateInputList()
            );
        }

        insertNewTag(tag) {
            const name = tag.getAttribute("data-value");

            const oldTag = this.widget.querySelector(`span[data-value="${name}"]`);
            if (oldTag) {
                oldTag.parentNode.removeChild(oldTag);
            }

            this.taggingBase.insertTag(this.currentTags, tag);
            this.configureRemoveTag(tag);
        }

        registerNewCallback(tag, newParent, onClicked) {
            function callback(event) {
                tag.parentNode.removeChild(tag);
                this.taggingBase.insertTag(newParent, tag);

                tag.removeEventListener('click', callback);
                onClicked(tag);
            }
            tag.addEventListener('click', callback.bind(this));
        }

        updateInputList() {
            const names = [];
            for (const tag of this.currentTags.querySelectorAll(".tag")) {
                const name = tag.getAttribute("data-value");
                names.push(`"${name}"`);
            }
            this.inputElement.value = names.join(",");
        }

        configureAddTag(tag) {
            this.taggingBase.updateTag(tag, null, null, "+");
            this.registerNewCallback(tag, this.currentTags, () => this.configureRemoveTag(tag));
            this.updateInputList();
        }

        configureRemoveTag(tag) {
            this.taggingBase.updateTag(tag, null, null, "-");
            this.registerNewCallback(tag, this.newTags, () => this.configureAddTag(tag));
            this.updateInputList();
        }
    };

    window.addEventListener('load', () => {
        for (const el of document.querySelectorAll('.babybuddy-tags-editor')) {
            new TagsEditor(el);
        }
    });
})();