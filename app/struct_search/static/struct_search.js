/*
Globals
*/
let searchTimeout;
const searchInput = document.getElementById("search");
const searchResultsList = document.getElementById("search-results");
const DEBOUNCE_INTERVAL_MS = 300;


/*
PROCEDURE: Update search results
*/
function updateSearchResultsList(matches) {
    function createFileLink(content) {
        let listElement = document.createElement("li");
        let anchorElement = document.createElement("a");
        anchorElement.appendChild(document.createTextNode(`${content["name"]} (${content["proj_path"]})`));
        anchorElement.setAttribute("href", `/parse-structs?path=${encodeURIComponent(content["full_path"])}`)
        listElement.appendChild(anchorElement);
        searchResultsList.appendChild(listElement);
    }

    searchResultsList.innerHTML = "";
    matches.forEach(match => createFileLink(match));
}

/*
PROCEDURE: Make selection
*/
function makeSelection(side, selection) {
    function createCodeBlock(serialized_structure) {
        // Element References
        let structDispEl = document.getElementById("left-struct-disp");

        // New Elements
        let preFormatEl = document.createElement("pre");
        let codeEl = document.createElement("code");
        let codeTextNode = document.createTextNode(serialized_structure);

        // Link elements
        structDispEl.innerHTML = "";
        structDispEl.appendChild(preFormatEl);
        preFormatEl.appendChild(codeEl);
        codeEl.appendChild(codeTextNode);
    }

    function populateReferences(references) {
        // Element references
        let structRefEl = document.getElementById("left-struct-ref");

        references.forEach(reference => {
            // New elements
            let buttonEl = document.createElement("button");
            let refTextNode = document.createTextNode(reference);

            // Onclick action
            buttonEl.setAttribute("onclick", `makeSelection('left', '${reference}')`)

            // Link elements
            structRefEl.appendChild(buttonEl);
            buttonEl.appendChild(refTextNode);
        });
    }

    fetch(`/make-selection?side=${encodeURIComponent(side)}&selection=${encodeURIComponent(selection)}`)
        .then(r => r.json())
        .then(result => {
            createCodeBlock(result["serialized"]);
            populateReferences(result["references"]);
        });
}

/*
Event Handler: Search input changes
*/
searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);

    // Debouncing
    searchTimeout = setTimeout(() => {
        const query = e.target.value;

        fetch(`/search?q=${encodeURIComponent(query)}`)
            .then(r => r.json())
            .then(results => updateSearchResultsList(results["matches"]));
    }, DEBOUNCE_INTERVAL_MS);
});