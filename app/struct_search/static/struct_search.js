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
PROCEDURE: Create code block
*/
function createCodeBlock(structViewRef, struct_serialized) {
    // Reference elements
    let codeBlockRef = structViewRef.children[1];

    // New elements
    let preFormatEl = document.createElement("pre");
    let codeEl = document.createElement("code");
    let codeTextNode = document.createTextNode(struct_serialized);

    // Link elements
    codeBlockRef.innerHTML = "";
    codeBlockRef.appendChild(preFormatEl);
    preFormatEl.appendChild(codeEl);
    codeEl.appendChild(codeTextNode);
}

/*
PROCEDURE: Populate references
*/
function populateReferences(structViewRef, references) {
    // Element references
    let refsRef = structViewRef.children[2];
    refsRef.innerHTML = "";

    references.forEach(reference => {
        // New elements
        let buttonEl = document.createElement("button");
        let refTextNode = document.createTextNode(reference);

        // Onclick action
        buttonEl.setAttribute("onclick", `newView('${reference}')`)

        // Link elements
        refsRef.appendChild(buttonEl);
        buttonEl.appendChild(refTextNode);
    });
}

/*
PROCEDURE: New view
*/
function newView(selection) {
    const url = selection ? `/new-view?selection=${encodeURIComponent(selection)}` : "/new-view";
    fetch(url)
        .then(r => r.json())
        .then(_ => window.location.reload());
}

/*
PROCEDURE: Make selection
*/
function makeSelection(view_idx, selection) {
    let structViewRef = document.getElementById("struct-views-container").children[view_idx];

    fetch(`/make-selection?view_idx=${encodeURIComponent(view_idx)}&selection=${encodeURIComponent(selection)}`)
        .then(r => r.json())
        .then(result => {
            createCodeBlock(structViewRef, result["desc"]["serialized"]);
            populateReferences(structViewRef, result["desc"]["references"]);
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