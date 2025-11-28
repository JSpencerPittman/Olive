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
        // Create elements
        let listElement = document.createElement("li");
        let anchorElement = document.createElement("a");
        let fileNameSpanElement = document.createElement("span");
        let filePathSpanElement = document.createElement("span");
        let filePathTextNode = document.createTextNode(`(${content["proj_path"]})`);

        // Set attributes
        fileNameSpanElement.textContent = `${content["name"]} `;
        fileNameSpanElement.setAttribute("class", "sr-filename");
        filePathSpanElement.setAttribute("class", "sr-filepath");

        // Link elements
        filePathSpanElement.appendChild(filePathTextNode);
        anchorElement.appendChild(fileNameSpanElement);
        anchorElement.appendChild(filePathSpanElement);
        anchorElement.setAttribute("href", `/parse-structs?path=${encodeURIComponent(content["full_path"])}`)
        listElement.appendChild(anchorElement);
        searchResultsList.appendChild(listElement);
    }

    searchResultsList.innerHTML = "";
    matches.forEach(match => createFileLink(match));
}

/*
PROCEDURE: Synchronize header
*/
function synchronizeHeader(structViewRef, heading) {
    // Reference elements
    let headingTextRef = structViewRef.children[0].children[0];

    // New elements
    let headingTextNode = document.createTextNode(heading);

    // Link elements
    headingTextRef.innerHTML = "";
    headingTextRef.appendChild(headingTextNode);
}

/*
PROCEDURE: Create code block
*/
function createCodeBlock(structViewRef, struct_serialized) {
    // Reference elements
    let codeBlockRef = structViewRef.children[2];

    // New elements
    let preFormatEl = document.createElement("pre");
    let codeEl = document.createElement("code");

    // Set attributes
    codeEl.textContent = struct_serialized;
    codeEl.setAttribute("class", "language-c");

    // Link elements
    codeBlockRef.innerHTML = "";
    codeBlockRef.appendChild(preFormatEl);
    preFormatEl.appendChild(codeEl);

    Prism.highlightElement(codeEl);
}

/*
PROCEDURE: Populate references
*/
function populateReferences(structViewRef, references) {
    // Element references
    let refsRef = structViewRef.children[3];
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
PROCEDURE: Delete view
*/
function deleteView(view_idx) {
    const url = `/delete-view?view-idx=${encodeURIComponent(view_idx)}`;
    fetch(url)
        .then(r => r.json())
        .then(_ => window.location.reload());
}

/*
PROCEDURE: Reset views
*/
function resetViews() {
    fetch("/reset-views")
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
            synchronizeHeader(structViewRef, result["desc"]["name"]);
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