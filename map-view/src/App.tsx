import React from 'react';
import './App.css';
import map from './services/map';

class App extends React.Component {
  mapId = "map";

  render() {
    return (
      <div id={this.mapId}></div>
    );
  }
}

export default App;
