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
            updateTag(tag, name, color, actionSymbol);
            return tag;
        }

        insertTag(list, tag) {
            list.appendChild(tag);
        }
    };

    class AddNewTagControl {
        constructor(widget, taggingBase) {
            this.taggingBase = taggingBase;

            this.apiTagsUrl = widget.getAttribute('data-tags-url');
            this.createTagInputs = widget.querySelector('.create-tag-inputs');
            this.addTagInput = this.createTagInputs.querySelector('input[type="text"]');
            this.addTagButton = this.createTagInputs.querySelector('.btn-add-new-tag');

            this.addTagInput.value = "";

            this.addTagButton.addEventListener('click', () => this.createTagClicked);
            this.addTagInput.addEventListener('keydown', (e) => {
                const key = e.key.toLowerCase();
                if (key === "enter") {
                    e.preventDefault();
                    this.createTagClicked();
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

            function success() {
                addTagInput.value = "";
            }

            function fail(msg) {
                msg = msg || "Error creating tag";

                addTagInput.select()
                alert(msg);
            }

            if (!tagName) {
                fail('Not a valid tag name');
                return;
            }

            const data = JSON.stringify({
                'name': addTagInput.value
            });


            function addTag(name, color) {
                const foundTag = widget.querySelector(`span[data-value="${name}"]`);
                if (foundTag) {
                    foundTag.parentNode.removeChild(foundTag);
                }

                const tag = this.taggingBase.createNewTag(name, color, "-");                    
                this.taggingBase.insertTag(currentTags, tag);
                removeTagCallback(tag);
                success();
            }

            doReq("GET", `${apiTagsUrl}?name=${uriTagName}`, null,
                (text) => {
                    const json = JSON.parse(text);
                    if (json.count) {
                        const tagJson = json.results[0];
                        addTag(tagJson.name, tagJson.color);
                    } else {
                        doReq("POST", apiTagsUrl, data, 
                            (text) => {
                                const tagJson = JSON.parse(text);
                                addTag(tagJson.name, tagJson.color);
                            }, fail
                        );
                    }
                }, fail
            );
        }
    };

    class TagsEditor {
        constructor(tagEditorRoot) {
            this.widget = tagEditorRoot;
            this.taggingBase = new TaggingBase(this.widget);
            this.addTagControl = new AddNewTagControl(
                this.widget, this.taggingBase
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