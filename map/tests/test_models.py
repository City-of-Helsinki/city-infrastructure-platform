import pytest
from django.db.utils import IntegrityError

from ..models import IconDrawingConfig
from .factories import IconDrawingConfigFactory


@pytest.mark.django_db
@pytest.mark.parametrize(
    "enabled, image_type, expected",
    (
        (
            True,
            IconDrawingConfig.ImageType.PNG,
            'duplicate key value violates unique constraint "map_icondrawingconfig_unique_enabled"',
        ),
        (
            False,
            IconDrawingConfig.ImageType.SVG,
            'duplicate key value violates unique constraint "map_icondrawingconfig_unique_image_type_png_size"',
        ),
    ),
)
def test_create_icon_drawing_configs_constraints(enabled, image_type, expected):
    IconDrawingConfigFactory(enabled=True, image_type=IconDrawingConfig.ImageType.SVG)
    with pytest.raises(IntegrityError) as exc_info:
        IconDrawingConfigFactory(enabled=enabled, image_type=image_type)
    assert expected in str(exc_info.value)
