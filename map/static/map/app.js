/* global ol */
(function() {
  "use strict";

  function MapView(target, mapConfig) {
    this.mapConfig = mapConfig;
    this.map = this.createMap(target);
    this.featureInfoPopup = this.createFeatureInfoPopup();
    this.map.addOverlay(this.featureInfoPopup);
  }

  MapView.prototype.createMap = function(target) {
    const projection = this.getProjection();
    const helsinkiCoords = [25499052.02, 6675851.38];
    const resolutions = [256, 128, 64, 32, 16, 8, 4, 2, 1, 0.5, 0.25, 0.125, 0.0625];
    const basemapLayerGroup = this.getBasemapLayerGroup()
    const overlayLayerGroup = this.getOverlayLayerGroup()
    const view = new ol.View({
      projection: projection,
      center: helsinkiCoords,
      zoom: 5,
      resolutions: resolutions,
      extent: projection.getExtent()
    });
    const map = new ol.Map({
      target: target,
      controls: this.getControls(),
      layers: [basemapLayerGroup, overlayLayerGroup],
      view: view
    });

    map.on("singleclick", (event) => {
      const viewResolution = view.getResolution();
      const visibleLayers = overlayLayerGroup.getLayers().getArray().filter(layer => layer.getVisible())
      if (visibleLayers.length > 0) {
        const layerNames = visibleLayers.map(layer => layer.getSource().getParams().LAYERS);
        const url = visibleLayers[0].getSource().getFeatureInfoUrl(
          event.coordinate,
          viewResolution,
          projection,
          {
            INFO_FORMAT: "application/json",
            LAYERS: layerNames.join(","),
            FEATURE_COUNT: 10
          }
        );

        if (url) {
          fetch(url).then(response => response.text()).then(responseText => {
            const data = JSON.parse(responseText);
            const features = data["features"];
            if (features.length > 0) {
              this.showFeatureInfo(event.coordinate, features);
            }
          });
        }
      }
    });

    return map;
  };

  MapView.prototype.createFeatureInfoPopup = function() {
    return new ol.Overlay({
      element: document.getElementById("feature-info-popup"),
      autoPan: true,
      autoPanAnimation: {
        duration: 250,
      }
    });
  };

  MapView.prototype.closeFeatureInfo = function() {
    this.featureInfoPopup.setPosition(undefined);
  };

  MapView.prototype.showFeatureInfo = function(coordinate, features) {
    const featureList = features.map(feature => {
      const [featureType, featureId] = feature["id"].split(".");
      const url = `/admin/traffic_control/${featureType.replace(/_/g, "")}/${featureId}/change`;
      return `<div>${featureType}: <a target="_blank" href="${url}">${featureId}</a></div>`;
    });
    const featureListElem = document.getElementById("feature-list");
    featureListElem.innerHTML = featureList.join("\n");
    this.featureInfoPopup.setPosition(coordinate);
  };

  MapView.prototype.getBasemapLayerGroup = function() {
    const basemapConfig = this.mapConfig.layerConfig.basemap;
    const basemapLayers = basemapConfig.layers.map(([layer, title], index) => {
      const wmsSource = new ol.source.ImageWMS({
        url: "https://kartta.hel.fi/ws/geoserver/avoindata/wms",
        params: {LAYERS: layer}
      });
      return new ol.layer.Image({
        type: "base",
        title: title,
        source: wmsSource,
        visible: index === 0
      });
    });

    return new ol.layer.Group({
      title: basemapConfig.title,
      layers: basemapLayers
    });
  };

  MapView.prototype.getOverlayLayerGroup = function() {
    const overlayConfig = this.mapConfig.layerConfig.overlay;
    const overlayLayers = overlayConfig.layers.map(([layer, title]) => {
      const wmsSource = new ol.source.ImageWMS({
        url: this.mapConfig.overlaySourceUrl,
        params: {LAYERS: layer}
      });
      return new ol.layer.Image({
        title: title,
        source: wmsSource,
        visible: false
      });
    });
    return new ol.layer.Group({
      title: overlayConfig.title,
      layers: overlayLayers
    });
  };

  MapView.prototype.getProjection = function() {
    return new ol.proj.Projection({
      code: "EPSG:3879",
      extent: [25440000, 6630000, 25571072, 6761072],
      units: "m",
      axisOrientation: "neu"
    });
  };

  MapView.prototype.getControls = function() {
    const mousePosition = new ol.control.MousePosition({
      coordinateFormat: ol.coordinate.createStringXY(0),
      projection: "EPSG:3879",
      className: "mouse-position"
    });

    const scaleLine = new ol.control.ScaleLine();

    const layerSwitcher = new ol.control.LayerSwitcher({
      reverse: false,
      tipLabel: "Layers"
    });

    return ol.control.defaults().extend([mousePosition, scaleLine, layerSwitcher]);
  };

  window.MapView = MapView;
})();
