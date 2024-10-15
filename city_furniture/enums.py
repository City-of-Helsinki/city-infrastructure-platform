from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _


class CityFurnitureDeviceTypeTargetModel(models.TextChoices):
    FURNITURE_SIGNPOST = "furniture_signpost", _("Furniture signpost")


class CityFurnitureClassType(models.IntegerChoices):
    """refs. OGC 12-019 section C.4 CityFurniture module"""

    TRAFFIC = 1000, _("Traffic")
    COMMUNICATION = 1010, _("Communication")
    SECURITY = 1020, _("Security")
    OTHERS = 1030, _("Others")


class CityFurnitureFunctionType(models.IntegerChoices):
    """refs. OGC 12-019 section C.4 CityFurniture module"""

    COMMUNICATION_FIXTURE = 1000, _("Communication fixture")
    TELEPHONE_BOX = 1010, _("Telephone box")
    POSTBOX = 1020, _("Postbox")
    EMERGENCY_CALL_FIXTURE = 1030, _("Emergency call fixture")
    FIRE_DETECTOR = 1040, _("Fire detector")
    POLICE_CALL_POST = 1050, _("Police call post")
    SWITCHING_UNIT = 1060, _("Switching unit")
    ROAD_SIGN = 1070, _("Road sign")
    TRAFFIC_LIGHT = 1080, _("Traffic light")
    FREE_STANDING_SIGN = 1090, _("Free-standing sign")
    FREE_STANDING_WARNING_SIGN = 1100, _("Free-standing warning sign")
    BUS_STOP = 1110, _("Bus stop")
    MILESTONE = 1120, _("Milestone")
    RAIL_LEVEL_CROSSING = 1130, _("Rail level crossing")
    GATE = 1140, _("Gate")
    STREETLAMP_LATERN_OR_CANDELABRA = 1150, _("Streetlamp, latern or candelabra")
    COLUMN = 1160, _("Column")
    LAMP_POST = 1170, _("Lamp post")
    FLAGPOLE = 1180, _("Flagpole")
    STREET_SINK_BOX = 1190, _("Street sink box")
    RUBBISH_BIN = 1200, _("Rubbish bin")
    CLOCK = 1210, _("Clock")
    DIRECTIONAL_SPOT_LIGHT = 1220, _("Directional spot light")
    FLOODLIGHT_MAST = 1230, _("Floodlight mast")
    WINDMILL = 1240, _("Windmill")
    SOLAR_CELL = 1250, _("Solar cell")
    WATER_WHEEL = 1260, _("Water wheel")
    POLE = 1270, _("Pole")
    RADIO_MAST = 1280, _("Radio mast")
    AERIAL = 1290, _("Aerial")
    RADIO_TELESCOPE = 1300, _("Radio telescope")
    CHIMNEY = 1310, _("Chimney")
    MARKER = 1320, _("Marker")
    HYDRANT = 1330, _("Hydrant")
    UPPER_CORRIDOR_FIRE_HYDRANT = 1340, _("Upper corridor fire-hydrant")
    LOWER_FLOOR_PANEL_FIRE_HYDRANT = 1350, _("Lower floor panel fire-hydrant")
    SLIDEGATE_VALVE_CAP = 1360, _("Slidegate valve cap")
    ENTRANCE_SHAFT = 1370, _("Entrance shaft")
    CONVERTER = 1380, _("Converter")
    STAIR = 1390, _("Stair")
    OUTSIDE_STAIRCASE = 1400, _("Outside staircase")
    ESCALATOR = 1410, _("Escalator")
    RAMP = 1420, _("Ramp")
    PATIO = 1430, _("Patio")
    FENCE = 1440, _("Fence")
    MEMORIAL_MONUMENT = 1450, _("Memorial/monument")
    WAYSIDE_SHRINE = 1470, _("Wayside shrine")
    CROSSROADS = 1480, _("Crossroads")
    CROSS_ON_THE_SUMMIT_OF_A_MOUNTAIN = 1490, _("Cross on the summit of a mountain")
    FOUNTAIN = 1500, _("Fountain")
    BLOCK_MARK = 1510, _("Block mark")
    BOUNDARY_POST = 1520, _("Boundary post")
    BENCH = 1530, _("Bench")
    OTHERS = 1540, _("Others")
