from collections import UserDict

from django.conf import settings
from django.contrib.gis.gdal import SpatialReference


class MockAttribute:
    def __init__(self, value):
        self.value = value


class MockFeature(UserDict):
    def __init__(self, data, ogr_geom):
        super().__init__(data)
        self.geom = ogr_geom


def create_mock_data_source(features):
    """
    Create a mock data source class

    The mock data source will create a single layer
    in the data source, and the layer will include
    features provided in function arguments

    :param features: Features to be included in the data source layer
    :return:
    """

    class MockLayer:
        def __init__(self):
            self.srs = SpatialReference(settings.SRID)
            self.mock_features = features

        def __iter__(self):
            yield from self.mock_features

        def __len__(self):
            return len(self.mock_features)

    class MockDataSource:
        def __init__(self, ds_input):
            pass

        def __getitem__(self, index):
            return MockLayer()

    return MockDataSource
