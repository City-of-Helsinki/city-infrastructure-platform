/**
 * Toggles the visibility of the import results table and updates ARIA states
 * for screen readers.
 *
 * @param {string} resultType - The type of result (e.g., 'success', 'error')
 */
function toggleImportGeometryResultsTable(resultType) {
    const content = document.getElementById("content_" + resultType);
    const icon = document.getElementById("toggle_" + resultType);
    const button = document.querySelector('button[aria-controls="content_' + resultType + '"]');

    let isHidden = content.style.display === "none" || content.style.display === "";

    if (isHidden) {
        content.style.display = "block";
        if (icon) icon.textContent = "▼";
        if (button) button.setAttribute("aria-expanded", "true");
    } else {
        content.style.display = "none";
        if (icon) icon.textContent = "▶";
        if (button) button.setAttribute("aria-expanded", "false");
    }
}
