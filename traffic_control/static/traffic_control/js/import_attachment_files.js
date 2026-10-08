(function () {
    "use strict";

    var UNITS = ["B", "kB", "MB", "GB"];

    function formatSize(bytes) {
        var size = bytes;
        var unitIndex = 0;
        while (size >= 1024 && unitIndex < UNITS.length - 1) {
            size = size / 1024;
            unitIndex += 1;
        }
        var rounded = unitIndex === 0 ? size : Math.round(size * 10) / 10;
        return rounded + " " + UNITS[unitIndex];
    }

    function renderEmpty(container, heading) {
        heading.textContent = container.dataset.emptyText || "";
        var list = container.querySelector("ul");
        if (list) {
            container.removeChild(list);
        }
    }

    function renderFiles(container, heading, files) {
        heading.textContent = (container.dataset.headingText || "") + " (" + files.length + ")";

        var list = container.querySelector("ul");
        if (!list) {
            list = document.createElement("ul");
            container.appendChild(list);
        }
        list.textContent = "";

        Array.prototype.forEach.call(files, function (file) {
            var item = document.createElement("li");

            var name = document.createElement("span");
            name.className = "attachment-file-name";
            name.textContent = file.name;
            item.appendChild(name);

            var size = document.createElement("span");
            size.className = "attachment-file-size";
            size.textContent = " (" + formatSize(file.size) + ")";
            item.appendChild(size);

            list.appendChild(item);
        });
    }

    function update(input, container) {
        var heading = container.querySelector(".attachment-file-list-heading");
        if (!heading) {
            return;
        }

        var files = input.files;
        if (!files || files.length === 0) {
            renderEmpty(container, heading);
            return;
        }
        renderFiles(container, heading, files);
    }

    function initialize() {
        var containers = document.querySelectorAll("[data-attachment-file-list]");
        Array.prototype.forEach.call(containers, function (container) {
            var input = document.getElementById(container.dataset.inputId);
            if (!input) {
                return;
            }
            input.addEventListener("change", function () {
                update(input, container);
            });
            update(input, container);
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initialize);
    } else {
        initialize();
    }
})();
