/**
 * Update traffic sign icon
 *
 * @param icon The icon <img> element on which the source image will be updated
 * @param iconUrl The new icon url
 */
function updateTrafficSignIcon(icon, iconUrl) {
  icon.src = iconUrl;
  icon.style.display = iconUrl ? "block" : "none";
}
