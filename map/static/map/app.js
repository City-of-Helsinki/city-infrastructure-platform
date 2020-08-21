/* global ol */
(function() {
  "use strict";

  function MapView(target, layerConfig) {
    this.layerConfig = layerConfig;
    this.map = this.createMap(target);
  }

  MapView.prototype.createMap = function(target) {
    const projection = this.getProjection();
    const helsinkiCoords = [25499052.02, 6675851.38];
    const resolutions = [256, 128, 64, 32, 16, 8, 4, 2, 1, 0.5, 0.25, 0.125, 0.0625];
    return new ol.Map({
      target: target,
      controls: this.getControls(),
      layers: [this.getBasemapLayerGroup(), this.getOverlayLayerGroup()],
      view: new ol.View({
        projection: projection,
        center: helsinkiCoords,
        zoom: 5,
        resolutions: resolutions,
        extent: projection.getExtent()
      })
    });
  };

  MapView.prototype.getBasemapLayerGroup = function() {
    const basemapConfig = this.layerConfig.basemap;
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
    const overlayConfig = this.layerConfig.overlay;
    const overlayLayers = overlayConfig.layers.map(([layer, title]) => {
      const wmsSource = new ol.source.ImageWMS({
        url: "https://geoserver.hel.fi/geoserver/city-infra/wms",
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
