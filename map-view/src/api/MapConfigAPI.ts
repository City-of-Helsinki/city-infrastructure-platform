import { MapConfig } from "../models";
import { APIBaseUrl } from "../consts";

class MapConfigAPI {
  private mapConfig: MapConfig;

  getMapConfig(): Promise<MapConfig> {
    if (this.mapConfig) {
      return Promise.resolve(this.mapConfig);
    } else {
      const url = `${APIBaseUrl}/map-config`;
      return fetch(url)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.text();
        })
        .then((responseText) => {
          try {
            this.mapConfig = JSON.parse(responseText);
            return this.mapConfig;
          } catch (error) {
            console.error("Failed to parse MapConfig JSON. Response was:", responseText.substring(0, 500));
            throw new Error(`Invalid JSON response from server: ${error}`);
          }
        })
        .catch((error) => {
          console.error("Error fetching MapConfig:", error);
          throw error;
        });
    }
  }
}

export default new MapConfigAPI();
