import { MapConfig } from "../models";

class MapConfigAPI {
  private mapConfig: MapConfig;

  getMapConfig(): Promise<MapConfig> {
    if (this.mapConfig) {
      return Promise.resolve(this.mapConfig);
    } else {
      const url = "/map-config";
      return fetch(url)
        .then((response) => response.text())
        .then((responseText) => {
          this.mapConfig = JSON.parse(responseText);
          return this.mapConfig;
        });
    }
  }
}

export default new MapConfigAPI();
