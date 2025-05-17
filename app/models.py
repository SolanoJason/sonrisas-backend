from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, MappedAsDataclass
from sqlalchemy import Column
from typing_extensions import Annotated
from sqlalchemy.ext.associationproxy import association_proxy, AssociationProxy
from datetime import datetime, UTC
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.types import JSON, String, Unicode, TypeDecorator
from sqlalchemy_file import File, FileField, ImageField
from typing import Any
from sqlalchemy_file.storage import StorageManager
from datetime import date
from app.config import settings
from typing import NewType
from collections.abc import Callable
from app.storage import default_container
from sqlalchemy_utils.types import CountryType, EmailType, URLType
from sqlalchemy_utils import Country


class SmartString(TypeDecorator):
    impl = String

    cache_ok = False

    """
    Parameters:
    -----------
    length : int | None
        Maximum length for the string field
    collation : str | None
        The collation for the string field
    validators : list[Callable[[str], None]] | None
        List of validation functions that accept a string and raise ValueError if validation fails.
        Each validator should take a string as input and raise ValueError if the string
        doesn't meet the validation criteria.
    processors : list[Callable[[str], str]] | None
        List of processing functions that transform the input string.
        Each processor should take a string as input and return a modified string.
        Processors are applied before validators.
    """

    def __init__(self, length: int | None = None, collation: str | None = None, validators: list[Callable[[str], None]] | None = None, processors: list[Callable[[str], str]] | None = None):
        super().__init__(length=length, collation=collation)
        if processors is None:
            self.processors = []
        if validators is None:
            self.validators = []
        self.validators = validators
        self.processors = processors

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        for processor in self.processors:
            value = processor(value)
        for validator in self.validators:
            validator(value)
        return value


def validator_non_empty(value: str):
    if value == "":
        raise ValueError("Value cannot be empty")


def processor_strip(value: str) -> str:
    return value.strip()


class ImageFile(File):

    @property
    def public_url(self):
        return f"https://storage.googleapis.com/{settings.GOOGLE_STORAGE_BUCKET}/{self.file_id}"


StorageManager.add_storage("default", default_container)

clean_str = NewType("clean_str", str)

intpk = Annotated[int, mapped_column(primary_key=True, init=False)]


# my_str = Annotated[clean_str, mapped_column(server_default="")]


class TimeStampMixin(MappedAsDataclass, kw_only=True, unsafe_hash=True):
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), insert_default=lambda: datetime.now(UTC), init=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), insert_default=lambda: datetime.now(UTC), onupdate=datetime.now(UTC), init=False)


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True, unsafe_hash=True):
    type_annotation_map = {
        File: FileField(none_as_null=True),
        ImageFile: ImageField(upload_type=ImageFile, none_as_null=True),
        dict: JSON(none_as_null=True),
        # clean_str: SmartString(processors=[processor_strip])
    }


class User(TimeStampMixin, Base):
    __tablename__ = 'users'

    id: Mapped[intpk] = mapped_column(init=False)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]


class Hero(TimeStampMixin, Base):
    __tablename__ = 'heros'

    id: Mapped[intpk] = mapped_column(init=False, hash=True)
    heading: Mapped[str]
    description: Mapped[str]
    image: Mapped[ImageFile] = mapped_column(hash=False)


class Location(TimeStampMixin, Base):
    __tablename__ = 'locations'

    id: Mapped[intpk] = mapped_column(init=False)
    heading: Mapped[str]
    address: Mapped[str]
    phones_description: Mapped[str]
    operating_hours: Mapped[str]
    image: Mapped[ImageFile] = mapped_column(hash=False)
    google_maps_embed_url: Mapped[str | None] = mapped_column(default=None)

    service_associations: Mapped[set[LocationServiceAssociation]] = relationship(back_populates="location", cascade="save-update, merge, delete, delete-orphan", default_factory=set, hash=False)
    services: AssociationProxy[set[Service]] = association_proxy("service_associations", "service", creator=lambda service_obj: LocationServiceAssociation(service=service_obj),
                                                                  default_factory=set, hash=False)


class Service(TimeStampMixin, Base):
    __tablename__ = 'services'

    id: Mapped[intpk] = mapped_column(init=False)
    heading: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str]
    image: Mapped[ImageFile] = mapped_column(hash=False)
    featured: Mapped[bool] = mapped_column(default=False)

    location_associations: Mapped[set[LocationServiceAssociation]] = relationship(back_populates="service", cascade="save-update, merge, delete, delete-orphan", default_factory=set, hash=False)
    locations: AssociationProxy[set[Location]] = association_proxy("location_associations", "location", creator=lambda location_obj: LocationServiceAssociation(location=location_obj),
                                                                    default_factory=set, hash=False)


class LocationServiceAssociation(TimeStampMixin, Base):
    __tablename__ = 'location_service_associations'

    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), primary_key=True, default=None)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), primary_key=True, default=None)

    location: Mapped[Location] = relationship(back_populates="service_associations", default=None)
    service: Mapped[Service] = relationship(back_populates="location_associations", default=None)


class TeamMember(TimeStampMixin, Base):
    __tablename__ = 'team_members'

    id: Mapped[intpk] = mapped_column(init=False)
    heading: Mapped[str] = mapped_column(unique=True)
    image: Mapped[ImageFile] = mapped_column(hash=False)
    role: Mapped[str]
    description: Mapped[str]


class OtherInfo(TimeStampMixin, Base):
    __tablename__ = 'other_info'

    id: Mapped[intpk] = mapped_column(init=False)
    name: Mapped[str] = mapped_column(unique=True)
    value: Mapped[str | None] = mapped_column(default=None)


class Promotions(TimeStampMixin, Base):
    __tablename__ = 'promotions'

    id: Mapped[intpk] = mapped_column(init=False)
    heading: Mapped[str]
    image: Mapped[ImageFile] = mapped_column(hash=False)
    description: Mapped[str]
    expire: Mapped[date | None] = mapped_column(default=None)


class Offers(TimeStampMixin, Base):
    __tablename__ = 'offers'

    id: Mapped[intpk] = mapped_column(init=False)
    heading: Mapped[str]
    image: Mapped[ImageFile] = mapped_column(hash=False)
    description: Mapped[str]


class Test(TimeStampMixin, Base):
    __tablename__ = "tests"

    id: Mapped[intpk] = mapped_column(init=False)
    my_dict: Mapped[dict]
    normal_str: Mapped[str]
    my_str: Mapped[str]
    country: Mapped[str] = mapped_column(CountryType)
    image: Mapped[ImageFile] = mapped_column(hash=False)
    file: Mapped[File] = mapped_column(hash=False)
