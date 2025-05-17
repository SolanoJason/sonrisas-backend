import hashlib
from fastapi import FastAPI, Query, Cookie, Header, Response, status, Form, File, UploadFile, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import time
from typing import Annotated
from app.models import Service, LocationServiceAssociation, Location, TeamMember, OtherInfo, Promotions, Offers, Hero, ImageFile
from app.config import settings
from enum import Enum, StrEnum
from pydantic import BaseModel, EmailStr, StringConstraints, HttpUrl, ConfigDict, field_validator, AfterValidator
from datetime import date
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_session
from sqlalchemy_file.storage import StorageManager
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from PIL import Image

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    print("Time took to process the request and return response is {} ms".format((time.time() - start_time) * 1000))
    return response


class HeroBase(BaseModel):
    heading: str
    description: str

    model_config = ConfigDict(str_strip_whitespace=True, str_min_length=1)


def validate_image(value: UploadFile):
    allowed_types = Image.MIME.values()
    if value.content_type not in allowed_types:
        raise ValueError(f'{value.content_type} is not a valid image type')
    return value

UploadImageFile = Annotated[UploadFile, AfterValidator(validate_image)]

class HeroIn(HeroBase):
    image: UploadImageFile


class HeroUpdate(HeroBase):
    heading: str | None = None
    description: str | None = None
    image: UploadImageFile | None = None


class HeroOut(HeroBase):
    id: int
    image_url: HttpUrl
    created_at: datetime
    updated_at: datetime


@app.post("/heros/", status_code=status.HTTP_201_CREATED)
async def create_hero(hero_in: Annotated[HeroIn, File()], session: Session = Depends(get_session)) -> HeroOut:
    hero = Hero(**hero_in.model_dump())
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return HeroOut.model_validate({**hero.__dict__, "image_url": hero.image.public_url})


@app.get("/heros/")
async def get_heros(session: Session = Depends(get_session)) -> list[HeroOut]:
    stmt = select(Hero).order_by(Hero.created_at.desc())
    heros = session.scalars(stmt).all()
    return [HeroOut.model_validate({**hero.__dict__, "image_url": hero.image.public_url}) for hero in heros]


@app.put("/heros/{hero_id}")
async def update_hero(hero_id: int, hero_in: Annotated[HeroUpdate, File()], session: Session = Depends(get_session)) -> HeroOut:
    hero = session.get(Hero, hero_id)
    if hero is None:
        raise HTTPException(status_code=404, detail="Hero not found")
    hero_in_dict = hero_in.model_dump(exclude_none=True)
    for key, val in hero_in_dict.items():
        setattr(hero, key, val)
    session.commit()
    session.refresh(hero)
    return HeroOut.model_validate({**hero.__dict__, "image_url": hero.image.public_url})


@app.delete("/heros/{hero_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hero(hero_id: int, session: Session = Depends(get_session)):
    hero = session.get(Hero, hero_id)
    if hero is None:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()


class TeamMemberBase(BaseModel):
    heading: str
    role: str
    description: str

    model_config = ConfigDict(str_strip_whitespace=True, str_min_length=1)


class TeamMemberIn(TeamMemberBase):
    image: UploadImageFile


class TeamMemberUpdate(TeamMemberBase):
    heading: str | None = None
    role: str | None = None
    description: str | None = None
    image: UploadImageFile | None = None


class TeamMemberOut(TeamMemberBase):
    id: int
    image_url: HttpUrl
    created_at: datetime
    updated_at: datetime


@app.post("/team_members/", status_code=status.HTTP_201_CREATED)
async def create_team_member(member_in: Annotated[TeamMemberIn, File()], session: Session = Depends(get_session)) -> TeamMemberOut:
    member = TeamMember(**member_in.model_dump())
    session.add(member)
    try:
        session.commit()
        session.refresh(member)
    except IntegrityError:
        raise HTTPException(status_code=409, detail=f"Team member with heading '{member_in.heading}' already exists.")
    return TeamMemberOut.model_validate({**member.__dict__, "image_url": member.image.public_url})


@app.get("/team_members/")
async def get_team_members(session: Session = Depends(get_session)) -> list[TeamMemberOut]:
    stmt = select(TeamMember).order_by(TeamMember.created_at.desc())
    members = session.scalars(stmt).all()
    return [TeamMemberOut.model_validate({**member.__dict__, "image_url": member.image.public_url}) for member in members]


@app.put("/team_members/{member_id}")
async def update_team_member(member_id: int, member_in: Annotated[TeamMemberUpdate, File()], session: Session = Depends(get_session)) -> TeamMemberOut:
    member = session.get(TeamMember, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Team member not found")

    member_in_dict = member_in.model_dump(exclude_none=True)
    for attr, value in member_in_dict.items():
        if hasattr(member, attr):
            setattr(member, attr, value)

    try:
        session.commit()
        session.refresh(member)
    except IntegrityError:
        raise HTTPException(status_code=409, detail=f"Team member with heading '{member_in.heading}' already exists.")

    return TeamMemberOut.model_validate({**member.__dict__, "image_url": member.image.public_url})


@app.delete("/team_members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team_member(member_id: int, session: Session = Depends(get_session)):
    member = session.get(TeamMember, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Team member not found")
    session.delete(member)
    session.commit()


class OtherInfoBase(BaseModel):
    name: str
    value: str | None = None

    model_config = ConfigDict(str_strip_whitespace=True, str_min_length=1)


class OtherInfoIn(OtherInfoBase):
    pass  # No extra fields needed for creation


class OtherInfoUpdate(BaseModel):  # value can be explicitly set to None
    name: str | None = None
    value: str | None = None

    model_config = ConfigDict(str_strip_whitespace=True, str_min_length=1)


class OtherInfoOut(OtherInfoBase):
    id: int
    created_at: datetime
    updated_at: datetime


@app.post("/other_info/", status_code=status.HTTP_201_CREATED)
async def create_other_info(info_in: OtherInfoIn, session: Session = Depends(get_session)) -> OtherInfoOut:
    info = OtherInfo(**info_in.model_dump())
    session.add(info)
    try:
        session.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail=f"Information with name '{info_in.name}' already exists.")

    return OtherInfoOut.model_validate(info, from_attributes=True)


@app.get("/other_info/")
async def get_all_other_info(session: Session = Depends(get_session)) -> list[OtherInfoOut]:
    stmt = select(OtherInfo).order_by(OtherInfo.created_at.desc())
    infos = session.scalars(stmt).all()
    return [OtherInfoOut.model_validate(info, from_attributes=True) for info in infos]


@app.get("/other_info/{info_name}")
async def get_other_info(info_name: str, session: Session = Depends(get_session)) -> OtherInfoOut:
    stmt = select(OtherInfo).where(OtherInfo.name == info_name)
    info = session.scalar(stmt)
    if info is None:
        raise HTTPException(status_code=404, detail="Information not found")
    return OtherInfoOut.model_validate(info, from_attributes=True)


@app.put("/other_info/{info_name}")
async def update_other_info(info_name: str, info_in: OtherInfoUpdate, session: Session = Depends(get_session)) -> OtherInfoOut:
    stmt = select(OtherInfo).where(OtherInfo.name == info_name)
    info = session.scalar(stmt)
    if info is None:
        raise HTTPException(status_code=404, detail="Information not found")

    update_data = info_in.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(info, key, value)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        if 'name' in update_data:
            raise HTTPException(status_code=409, detail=f"Information with name '{info_in.name}' already exists.")
        else:
            raise HTTPException(status_code=409, detail="Data conflict during update.")

    return OtherInfoOut.model_validate(info, from_attributes=True)


@app.delete("/other_info/{info_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_other_info(info_name: str, session: Session = Depends(get_session)):
    stmt = select(OtherInfo).where(OtherInfo.name == info_name)
    info = session.scalar(stmt)
    if info is None:
        raise HTTPException(status_code=404, detail="Information not found")
    session.delete(info)
    session.commit()


class LocationBase(BaseModel):
    heading: str
    address: str
    phones_description: str
    operating_hours: str
    google_maps_embed_url: str | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class LocationIn(LocationBase):
    image: UploadImageFile

    model_config = ConfigDict(str_min_length=1)


class LocationOut(LocationBase):
    id: int
    image_url: HttpUrl
    created_at: datetime
    updated_at: datetime


class LocationUpdate(LocationBase):
    heading: str | None = None
    address: str | None = None
    phones_description: str | None = None
    operating_hours: str | None = None
    google_maps_embed_url: str | None = None
    image: UploadImageFile | None = None

    model_config = ConfigDict(str_min_length=1)


@app.get("/locations/")
async def get_locations(session: Session = Depends(get_session)) -> list[LocationOut]:
    stmt = select(Location).order_by(Location.created_at.desc())
    locations = session.scalars(stmt).all()
    return [LocationOut.model_validate({**location.__dict__, "image_url": location.image.public_url}) for location in locations]


@app.post("/locations/", status_code=status.HTTP_201_CREATED)
async def create_location(location_in: Annotated[LocationIn, File()], session: Session = Depends(get_session)) -> LocationOut:
    location = Location(**location_in.model_dump())
    session.add(location)
    session.commit()
    session.refresh(location)
    return LocationOut.model_validate({**location.__dict__, "image_url": location.image.public_url})


@app.put("/locations/{location_id}")
async def update_location(location_id: int, location_in: Annotated[LocationUpdate, File()], session: Session = Depends(get_session)) -> LocationOut:
    location = session.get(Location, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    location_in_dict = location_in.model_dump(exclude_none=True)
    for key, val in location_in_dict.items():
        setattr(location, key, val)
    session.commit()
    session.refresh(location)
    return LocationOut.model_validate({**location.__dict__, "image_url": location.image.public_url})


@app.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(location_id: int, session: Session = Depends(get_session)):
    location = session.get(Location, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    session.delete(location)
    session.commit()


class ServiceBase(BaseModel):
    heading: str
    description: str


class ServiceIn(ServiceBase):
    image: UploadImageFile
    featured: bool = False


class ServiceOut(ServiceBase):
    id: int
    image_url: HttpUrl
    featured: bool


class ServiceUpdate(ServiceBase):
    heading: str | None = None
    description: str | None = None
    image: UploadImageFile | None = None
    featured: bool | None = None


@app.get("/services/")
async def get_services(session: Session = Depends(get_session)) -> list[ServiceOut]:
    stmt = select(Service).order_by(Service.created_at.desc())
    services = session.scalars(stmt).all()
    return [ServiceOut.model_validate({**service.__dict__, "image_url": service.image.public_url}) for service in services]


@app.post("/services/", status_code=status.HTTP_201_CREATED)
async def create_service(service_in: Annotated[ServiceIn, File()], session: Session = Depends(get_session)) -> ServiceOut:
    service = Service(**service_in.model_dump())
    session.add(service)
    session.commit()
    session.refresh(service)
    return ServiceOut.model_validate({**service.__dict__, "image_url": service.image.public_url})


@app.put("/services/{service_id}")
async def update_service(service_id: int, service_in: Annotated[ServiceUpdate, File()], session: Session = Depends(get_session)) -> ServiceOut:
    service = session.get(Service, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    service_in_dict = service_in.model_dump(exclude_none=True)
    for key, val in service_in_dict.items():
        setattr(service, key, val)
    session.commit()
    session.refresh(service)
    return ServiceOut.model_validate({**service.__dict__, "image_url": service.image.public_url})


@app.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(service_id: int, session: Session = Depends(get_session)):
    service = session.get(Service, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    session.delete(service)
    session.commit()


@app.get("/locations/{location_id}/services")
async def get_services_of_location(location_id: int, session: Session = Depends(get_session)) -> list[ServiceOut]:
    location = session.get(Location, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    services = location.services
    return [ServiceOut.model_validate({**service.__dict__, "image_url": service.image.public_url}) for service in services]


@app.patch("/locations/{location_id}/services")
async def update_services_of_location(
    location_id: int,
    service_ids: list[int],
    session: Session = Depends(get_session)
) -> list[ServiceOut]:
    location = session.get(Location, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    
    stmt = select(Service).where(Service.id.in_(service_ids))
    services = set(session.scalars(stmt).all())
    location.services.update(services)
    session.commit()
    session.refresh(location)
    return [
        ServiceOut.model_validate({**service.__dict__, "image_url": service.image.public_url})
        for service in location.services
    ]

@app.delete("/locations/{location_id}/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_of_location(location_id: int, service_id: int, session: Session = Depends(get_session)):
    location = session.get(Location, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    service = session.get(Service, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    if service not in location.services:
        raise HTTPException(status_code=404, detail="Service not found in location")
    location.services.remove(service)
    session.commit()

class PromotionsOut(BaseModel):
    id: int
    heading: str
    image_url: HttpUrl
    description: str
    expire: date | None
    created_at: datetime
    updated_at: datetime

class PromotionsIn(BaseModel):
    heading: str
    description: str
    expire: date | None = None
    image: UploadImageFile

class PromotionsUpdate(BaseModel):
    heading: str | None = None
    description: str | None = None
    expire: date | None = None
    image: UploadImageFile | None = None

@app.get("/promotions/")
async def get_promotions(session: Session = Depends(get_session)) -> list[PromotionsOut]:
    stmt = select(Promotions).order_by(Promotions.created_at.desc())
    promotions = session.scalars(stmt).all()
    return [PromotionsOut.model_validate({**promotion.__dict__, "image_url": promotion.image.public_url}) for promotion in promotions]

@app.post("/promotions/", status_code=status.HTTP_201_CREATED)
async def create_promotion(promotion_in: Annotated[PromotionsIn, File()], session: Session = Depends(get_session)) -> PromotionsOut:
    promotion = Promotions(**promotion_in.model_dump())
    session.add(promotion)
    session.commit()
    session.refresh(promotion)
    return PromotionsOut.model_validate({**promotion.__dict__, "image_url": promotion.image.public_url})

@app.put("/promotions/{promotion_id}")
async def update_promotion(promotion_id: int, promotion_in: Annotated[PromotionsUpdate, File()], session: Session = Depends(get_session)) -> PromotionsOut:
    print(f"{promotion_in=}")
    promotion = session.get(Promotions, promotion_id)
    if promotion is None:
        raise HTTPException(status_code=404, detail="Promotion not found")
    if promotion_in.expire is None:
        promotion_in.expire = None
    promotion_in_dict = promotion_in.model_dump(exclude_unset=True)
    print(f"{promotion_in_dict=}")
    for key, val in promotion_in_dict.items():
        setattr(promotion, key, val)
    session.commit()
    session.refresh(promotion)
    return PromotionsOut.model_validate({**promotion.__dict__, "image_url": promotion.image.public_url})

@app.delete("/promotions/{promotion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_promotion(promotion_id: int, session: Session = Depends(get_session)):
    promotion = session.get(Promotions, promotion_id)
    if promotion is None:
        raise HTTPException(status_code=404, detail="Promotion not found")
    session.delete(promotion)
    session.commit()

class OffersOut(BaseModel):
    id: int
    heading: str
    image_url: HttpUrl
    description: str
    created_at: datetime
    updated_at: datetime

class OffersIn(BaseModel):
    heading: str
    description: str
    image: UploadImageFile

class OffersUpdate(BaseModel):
    heading: str | None = None
    description: str | None = None
    image: UploadImageFile | None = None

@app.get("/offers/")
async def get_offers(session: Session = Depends(get_session)) -> list[OffersOut]:
    stmt = select(Offers).order_by(Offers.created_at.desc())
    offers = session.scalars(stmt).all()
    return [OffersOut.model_validate({**offer.__dict__, "image_url": offer.image.public_url}) for offer in offers]

@app.post("/offers/", status_code=status.HTTP_201_CREATED)
async def create_offer(offer_in: Annotated[OffersIn, File()], session: Session = Depends(get_session)) -> OffersOut:
    offer = Offers(**offer_in.model_dump())
    session.add(offer)
    session.commit()
    session.refresh(offer)
    return OffersOut.model_validate({**offer.__dict__, "image_url": offer.image.public_url})    

@app.put("/offers/{offer_id}")
async def update_offer(offer_id: int, offer_in: Annotated[OffersUpdate, File()], session: Session = Depends(get_session)) -> OffersOut:
    offer = session.get(Offers, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    offer_in_dict = offer_in.model_dump(exclude_unset=True)
    for key, val in offer_in_dict.items():
        setattr(offer, key, val)
    session.commit()
    session.refresh(offer)
    return OffersOut.model_validate({**offer.__dict__, "image_url": offer.image.public_url})   

@app.delete("/offers/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_offer(offer_id: int, session: Session = Depends(get_session)):
    offer = session.get(Offers, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    session.delete(offer)
    session.commit()
