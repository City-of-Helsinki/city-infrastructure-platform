from django.utils.translation import gettext_lazy as _
from enumfields import Enum


class CityFurnitureDeviceTypeTargetModel(Enum):
    FURNITURE_SIGNPOST = "furniture_signpost"

    class Labels:
        FURNITURE_SIGNPOST = _("Furniture signpost")


class CityFurnitureClassType(Enum):
    """refs. OGC 12-019 section C.4 CityFurniture module"""

    TRAFFIC = 1000
    COMMUNICATION = 1010
    SECURITY = 1020
    OTHERS = 1030

    class Labels:
        TRAFFIC = _("Traffic")
        COMMUNICATION = _("Communication")
        SECURITY = _("Security")
        OTHERS = _("Others")


class CityFurnitureFunctionType(Enum):
    """refs. OGC 12-019 section C.4 CityFurniture module"""

    COMMUNICATION_FIXTURE = 1000
    TELEPHONE_BOX = 1010
    POSTBOX = 1020
    EMERGENCY_CALL_FIXTURE = 1030
    FIRE_DETECTOR = 1040
    POLICE_CALL_POST = 1050
    SWITCHING_UNIT = 1060
    ROAD_SIGN = 1070
    TRAFFIC_LIGHT = 1080
    FREE_STANDING_SIGN = 1090
    FREE_STANDING_WARNING_SIGN = 1100
    BUS_STOP = 1110
    MILESTONE = 1120
    RAIL_LEVEL_CROSSING = 1130
    GATE = 1140
    STREETLAMP_LATERN_OR_CANDELABRA = 1150
    COLUMN = 1160
    LAMP_POST = 1170
    FLAGPOLE = 1180
    STREET_SINK_BOX = 1190
    RUBBISH_BIN = 1200
    CLOCK = 1210
    DIRECTIONAL_SPOT_LIGHT = 1220
    FLOODLIGHT_MAST = 1230
    WINDMILL = 1240
    SOLAR_CELL = 1250
    WATER_WHEEL = 1260
    POLE = 1270
    RADIO_MAST = 1280
    AERIAL = 1290
    RADIO_TELESCOPE = 1300
    CHIMNEY = 1310
    MARKER = 1320
    HYDRANT = 1330
    UPPER_CORRIDOR_FIRE_HYDRANT = 1340
    LOWER_FLOOR_PANEL_FIRE_HYDRANT = 1350
    SLIDEGATE_VALVE_CAP = 1360
    ENTRANCE_SHAFT = 1370
    CONVERTER = 1380
    STAIR = 1390
    OUTSIDE_STAIRCASE = 1400
    ESCALATOR = 1410
    RAMP = 1420
    PATIO = 1430
    FENCE = 1440
    MEMORIAL_MONUMENT = 1450
    WAYSIDE_SHRINE = 1470
    CROSSROADS = 1480
    CROSS_ON_THE_SUMMIT_OF_A_MOUNTAIN = 1490
    FOUNTAIN = 1500
    BLOCK_MARK = 1510
    BOUNDARY_POST = 1520
    BENCH = 1530
    OTHERS = 1540

    class Labels:
        COMMUNICATION_ADJUSTMENT = _("Communication fixture")
        TELEPHONE_HOUSE = _("Telephone box")
        POSTBOX = _("Postbox")
        EMERGENCY_CALL_ADJUSTMENT = _("Emergency call fixture")
        FIRE_DETECTOR = _("Fire detector")
        SILENT_ALARM_COLUMN = _("Police call post")
        SWITCHING_UNIT = _("Switching unit")
        ROAD_SIGN = _("Road sign")
        TRAFFIC_LIGHT = _("Traffic light")
        FREE_STANDING_SIGN = _("Free-standing sign")
        FREE_STANDING_WARNING_SIGN = _("Free-standing warning sign")
        BUS_STOP = _("Bus stop")
        MILESTONE = _("Milestone")
        RAILROAD_CROSSING = _("Rail level crossing")
        GATE = _("Gate")
        LATERN = _("Streetlamp, latern or candelabra")
        COLUMN = _("Column")
        STACKING_LAMP = _("Lamp post")
        FLAGPOLE = _("Flagpole")
        ROAD_SINKING_BOX = _("Street sink box")
        RUBBISH_BOX = _("Rubbish bin")
        CLOCK = _("Clock")
        LEVELING_HEAD_LIGHT = _("Directional spot light")
        FLOODLIGHT_MAST = _("Floodlight mast")
        WINDMILL = _("Windmill")
        SOLAR_CELL = _("Solar cell")
        WATER_WHEEL = _("Water wheel")
        POLE = _("Pole")
        RADIO_MAST = _("Radio mast")
        AERIAL = _("Aerial")
        RADIO_TELESCOPE = _("Radio telescope")
        CHIMNEY = _("Chimney")
        MARKER = _("Marker")
        HYDRANT = _("Hydrant")
        UPPER_CORRIDOR_FIRE_HYDRANT = _("Upper corridor fire-hydrant")
        LOWER_FLOOR_PANEL_FIRE_HYDRANT = _("Lower floor panel fire-hydrant")
        SLIDEGATE_VALVE_CAP = _("Slidegate valve cap")
        ENTERING_PIT = _("Entrance shaft")
        CONVERTER = _("Converter")
        STAIR = _("Stair")
        OUTSIDE_STAIRCASE = _("Outside staircase")
        ESCALATOR = _("Escalator")
        RAMP = _("Ramp")
        PATIO = _("Patio")
        FENCE = _("Fence")
        MEMORIAL_MONUMENT = _("Memorial/monument")
        WAY_CROSS = _("Wayside shrine")
        ALLEY_CROSS = _("Crossroads")
        CAP_CROSS = _("Cross on the summit of a mountain")
        FOUNTAIN = _("Fountain")
        BLOCK_MARK = _("Block mark")
        DELIMITATION_STAKE = _("Boundary post")
        BENCH = _("Bench")
        UNKNOWN = _("Others")


class OrganizationLevel(Enum):
    """Responsible Entity Organization levels"""

    DIVISION = 10
    SERVICE = 20
    UNIT = 30
    PERSON = 40
    PROJECT = 50

    class Labels:
        DIVISION = _("division")
        SERVICE = _("service")
        UNIT = _("unit")
        PERSON = _("person")
        PROJECT = _("project")
