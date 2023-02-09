## Traffic control devices

Provides REST API for traffic control devices, such as traffic signs, traffic lights, barriers, signposts, mounts and road markings.

These devices have planned and realized entities in the platform, and therefore also equivalent REST-endpoints.

Entity location output format can be controlled via "geo_format" GET-parameter. Supported formats are `ewkt` and `geojson`. EWKT is the default format.

All coordinate values are presented in [ETRS89 / ETRS-GK25FIN (EPSG:3879)](https://epsg.org/crs_3879/ETRS89-GK25FIN.html) coordinate reference system.
