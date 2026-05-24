"""Management command for creating testdata triplets for 3rd party application testing."""
import uuid
from typing import NamedTuple

from auditlog.context import set_actor
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError

from traffic_control.enums import DeviceTypeTargetModel, Lifecycle
from traffic_control.models.additional_sign import AdditionalSignReal
from traffic_control.models.common import Owner, TrafficControlDeviceType
from traffic_control.models.mount import LocationSpecifier as MountLocationSpecifier, MountReal, MountType
from traffic_control.models.traffic_sign import LocationSpecifier as SignLocationSpecifier, TrafficSignReal
from users.utils import get_system_user

# Helsinki city centre in EPSG:3879
HELSINKI_CENTER_X = 25496000
HELSINKI_CENTER_Y = 6673000
LOCATION_OFFSET_STEP = 10

_MOUNT_LOCATION_SPECIFIERS = [
    MountLocationSpecifier.RIGHT,
    MountLocationSpecifier.LEFT,
    MountLocationSpecifier.ABOVE,
    MountLocationSpecifier.MIDDLE,
    MountLocationSpecifier.OUTSIDE,
]
_SIGN_LOCATION_SPECIFIERS = list(SignLocationSpecifier)
_LIFECYCLES = list(Lifecycle)


class TripletAttrs(NamedTuple):
    """Attributes shared across a single mount/sign/additional-sign triplet."""

    location: Point
    lifecycle: Lifecycle
    mount_location_specifier: MountLocationSpecifier
    sign_location_specifier: SignLocationSpecifier
    source_id: str
    source_name: str


class Command(BaseCommand):
    """Create linked testdata triplets (MountReal, TrafficSignReal, AdditionalSignReal) for 3rd party app testing."""

    help = "Creates linked testdata triplets of MountReal, TrafficSignReal and AdditionalSignReal."

    def add_arguments(self, parser) -> None:
        """Add command arguments.

        Args:
            parser: The argument parser instance.
        """
        parser.add_argument(
            "--source-name",
            type=str,
            required=True,
            help="Base source_name used for all created objects (suffixed with triplet index).",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=5,
            help="Number of triplets to create (default: 5).",
        )

    def handle(self, *args, **options) -> None:
        """Execute the command.

        Args:
            *args: Positional arguments.
            **options: Parsed command-line options.

        Raises:
            CommandError: If required DB prerequisites (MountType, TrafficControlDeviceType) are missing.
        """
        source_name = options["source_name"]
        count = options["count"]

        system_user = get_system_user()
        mount_type = MountType.objects.first()
        sign_device_type = TrafficControlDeviceType.objects.filter(
            target_model=DeviceTypeTargetModel.TRAFFIC_SIGN
        ).first()
        additional_sign_device_type = TrafficControlDeviceType.objects.filter(
            target_model=DeviceTypeTargetModel.ADDITIONAL_SIGN
        ).first()

        if mount_type is None:
            raise CommandError("No MountType found in database. Please create at least one MountType first.")
        if sign_device_type is None:
            raise CommandError(
                "No TrafficControlDeviceType with target_model=TRAFFIC_SIGN found. "
                "Please create at least one traffic sign device type first."
            )
        if additional_sign_device_type is None:
            raise CommandError(
                "No TrafficControlDeviceType with target_model=ADDITIONAL_SIGN found. "
                "Please create at least one additional sign device type first."
            )

        self.stdout.write(f"Creating {count} testdata triplet(s) with source_name base '{source_name}'...")
        self.stdout.write(f"  Using MountType: {mount_type}")
        self.stdout.write(f"  Using sign DeviceType: {sign_device_type}")
        self.stdout.write(f"  Using additional sign DeviceType: {additional_sign_device_type}")

        with set_actor(system_user):
            for n in range(count):
                owner = _create_owner(n, source_name)
                attrs = _build_triplet_attrs(n, source_name)
                mount, sign, additional_sign = _create_triplet(
                    attrs, owner, system_user, mount_type, sign_device_type, additional_sign_device_type
                )
                msg = (
                    f"  [{n + 1}/{count}] "
                    f"MountReal={mount.id} | "
                    f"TrafficSignReal={sign.id} | "
                    f"AdditionalSignReal={additional_sign.id} | "
                    f"owner='{owner.name_fi}' | "
                    f"lifecycle={attrs.lifecycle.name} | "
                    f"source_name='{attrs.source_name}' | "
                    f"mount_loc_spec={attrs.mount_location_specifier.name} | "
                    f"sign_loc_spec={attrs.sign_location_specifier.name}"
                )
                self.stdout.write(self.style.SUCCESS(msg))

        self.stdout.write(self.style.SUCCESS(f"\nDone. Created {count} triplet(s)."))


def _build_triplet_attrs(n: int, source_name: str) -> TripletAttrs:
    """Build the varying attribute set for triplet index n.

    Args:
        n (int): Zero-based triplet index.
        source_name (str): Base source name provided via CLI.

    Returns:
        TripletAttrs: Immutable attribute bundle for the triplet.
    """
    location = Point(
        HELSINKI_CENTER_X + n * LOCATION_OFFSET_STEP,
        HELSINKI_CENTER_Y + n * LOCATION_OFFSET_STEP,
        0.0,
        srid=settings.SRID,
    )
    lifecycle = _LIFECYCLES[n % len(_LIFECYCLES)]
    mount_location_specifier = _MOUNT_LOCATION_SPECIFIERS[n % len(_MOUNT_LOCATION_SPECIFIERS)]
    sign_location_specifier = _SIGN_LOCATION_SPECIFIERS[n % len(_SIGN_LOCATION_SPECIFIERS)]
    source_id = uuid.uuid4().hex

    return TripletAttrs(
        location=location,
        lifecycle=lifecycle,
        mount_location_specifier=mount_location_specifier,
        sign_location_specifier=sign_location_specifier,
        source_id=source_id,
        source_name=source_name,
    )


def _create_owner(n: int, source_name: str) -> Owner:
    """Get or create a unique Owner for the triplet at index n.

    Args:
        n (int): Zero-based triplet index.
        source_name (str): Base source name provided via CLI.

    Returns:
        Owner: The owner instance for this triplet.
    """
    owner, _ = Owner.objects.get_or_create(name_fi=f"TestOwner {n}")
    return owner


def _create_triplet(
    attrs: TripletAttrs,
    owner: Owner,
    system_user: object,
    mount_type: MountType,
    sign_device_type: TrafficControlDeviceType,
    additional_sign_device_type: TrafficControlDeviceType,
) -> tuple[MountReal, TrafficSignReal, AdditionalSignReal]:
    """Create one linked MountReal → TrafficSignReal → AdditionalSignReal triplet.

    Args:
        attrs (TripletAttrs): Varying attribute bundle for this triplet.
        owner (Owner): Owner instance for all three objects.
        system_user (object): System user for created_by/updated_by stamps.
        mount_type (MountType): Mount type applied to all three objects.
        sign_device_type (TrafficControlDeviceType): Device type for the TrafficSignReal.
        additional_sign_device_type (TrafficControlDeviceType): Device type for the AdditionalSignReal.

    Returns:
        tuple[MountReal, TrafficSignReal, AdditionalSignReal]: The three created objects.
    """
    mount = MountReal.objects.create(
        source_id=attrs.source_id,
        source_name=attrs.source_name,
        location=attrs.location,
        lifecycle=attrs.lifecycle,
        owner=owner,
        mount_type=mount_type,
        location_specifier=attrs.mount_location_specifier,
        created_by=system_user,
        updated_by=system_user,
    )

    sign = TrafficSignReal.objects.create(
        source_id=attrs.source_id,
        source_name=attrs.source_name,
        location=attrs.location,
        lifecycle=attrs.lifecycle,
        owner=owner,
        device_type=sign_device_type,
        mount_type=mount_type,
        mount_real=mount,
        location_specifier=attrs.sign_location_specifier,
        direction=0,
        created_by=system_user,
        updated_by=system_user,
    )

    additional_sign = AdditionalSignReal.objects.create(
        source_id=attrs.source_id,
        source_name=attrs.source_name,
        location=attrs.location,
        lifecycle=attrs.lifecycle,
        owner=owner,
        device_type=additional_sign_device_type,
        mount_type=mount_type,
        mount_real=mount,
        parent=sign,
        location_specifier=attrs.sign_location_specifier,
        missing_content=True,
        direction=0,
        created_by=system_user,
        updated_by=system_user,
    )

    return mount, sign, additional_sign
