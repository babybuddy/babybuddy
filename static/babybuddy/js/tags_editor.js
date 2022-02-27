(function() {
    class TagsEditor {
        constructor(tagEditorRoot) {
            this.tagEditorRoot = tagEditorRoot;
        }
    };

    window.addEventListener('load', () => {
        const widget = document.getElementById('{{ widget.attrs.id }}');
        const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
        
        const prototype = widget.querySelector('.prototype-tag');
        const currentTags = widget.querySelector('.current_tags');
        const newTags = widget.querySelector('.new-tags');

        const inputElement = widget.querySelector('input[type="hidden"]');

        const apiTagsUrl = widget.getAttribute('data-tags-url');
        const createTagInputs = widget.querySelector('.create-tag-inputs');
        const addTagInput = createTagInputs.querySelector('input[type="text"]');
        const addTagButton = createTagInputs.querySelector('.btn-add-new-tag');

        function doReq(method, uri, data, success, fail) {
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
            req.setRequestHeader("X-CSRFTOKEN", csrfToken);
            req.send(data);
        }

        function createTagClicked() {
            const tagName = addTagInput.value.trim();
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

                const tag = createNewTag(name, color, "-");                    
                insertTag(currentTags, tag);
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
        addTagButton.addEventListener('click', createTagClicked);
        addTagInput.addEventListener('keydown', (e) => {
            const key = e.key.toLowerCase();
            if (key === "enter") {
                e.preventDefault();
                createTagClicked();
            }
        });

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

        function updateTag(tag, name, color, actionSymbol) {
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

        function createNewTag(name, color, actionSymbol) {
            const tag = prototype.cloneNode(true);
            tag.classList.remove("prototype-tag");
            tag.classList.add("tag");
            updateTag(tag, name, color, actionSymbol);
            return tag;
        }

        function insertTag(list, tag) {
            list.appendChild(tag);
            updateInputList();
        }

        function registerNewCallback(tag, newParent, newSymbol, onClicked) {
            function callback(event) {
                tag.parentNode.removeChild(tag);
                updateTag(
                    tag,
                    null,
                    tag.getAttribute("data-color"),
                    newSymbol
                );

                insertTag(newParent, tag);

                tag.removeEventListener('click', callback);
                onClicked(tag);
            }
            tag.addEventListener('click', callback);
        }

        function updateInputList() {
            const names = [];
            for (const tag of currentTags.querySelectorAll(".tag")) {
                const name = tag.getAttribute("data-value");
                names.push(`"${name}"`);
            }
            inputElement.value = names.join(",");
        }

        function addTagCallback(tag) {
            registerNewCallback(tag, currentTags, "-", removeTagCallback);
            updateInputList();
        }

        function removeTagCallback(tag) {
            registerNewCallback(tag, newTags, "+", addTagCallback);
            updateInputList();
        }

        for (const tag of newTags.querySelectorAll(".tag")) {
            updateTag(tag);
            addTagCallback(tag);
        }
        for (const tag of currentTags.querySelectorAll(".tag")) {
            updateTag(tag);
            removeTagCallback(tag);
        }
    });
})();