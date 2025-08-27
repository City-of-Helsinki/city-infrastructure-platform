/**
 * Update traffic sign icon
 *
 * @param icon The icon <img> element on which the source image will be updated
 * @param iconUrl The new icon url
 */
function updateTrafficSignIcon(icon, iconUrl) {
  if (typeof iconUrl !== "string") { // Happens when a new item is introduced to the dropdown after load
    icon.src = null;
    icon.alt = null;
    icon.style.display = "none";
  } else {
    icon.src = iconUrl;
    icon.alt = iconUrl.split("/").pop();
    icon.style.display = iconUrl ? "block" : "none";
  }
}
