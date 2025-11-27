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