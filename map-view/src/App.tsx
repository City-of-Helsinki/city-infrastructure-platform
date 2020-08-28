import React from 'react';
import './App.css';
import Map from './common/Map';
import MapConfigAPI from './api/MapConfigAPI';

import 'ol/ol.css';

class App extends React.Component {
  mapId = "map";

  componentDidMount() {
    MapConfigAPI.getMapConfig().then(mapConfig => Map.initialize(this.mapId, mapConfig));
  }

  render() {
    return (
      <div id={this.mapId}></div>
    );
  }
}

export default App;
