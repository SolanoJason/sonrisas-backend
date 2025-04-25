import hashlib
from fastapi import FastAPI, Query, Cookie, Header, Response, status, Form, File, UploadFile, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated, List
from app.models import Service, LocationServiceAssociation, Location, TeamMember, OtherInfo, Promotions, Offers, Hero, ImageFile
from app.config import settings
from enum import Enum, StrEnum
from pydantic import BaseModel, EmailStr, StringConstraints, HttpUrl, ConfigDict
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_session
from sqlalchemy_file.storage import StorageManager
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HeroBase(BaseModel):
    heading: str
    description: str

    model_config = ConfigDict(str_strip_whitespace=True, str_min_length=1)


class HeroIn(HeroBase):
    image: UploadFile


class HeroUpdate(HeroBase):
    heading: str | None = None
    description: str | None = None
    image: UploadFile | None = None


class HeroOut(HeroBase):
    id: int
    image_url: HttpUrl
    created_at: datetime
    updated_at: datetime


@app.post("/heros/", status_code=status.HTTP_201_CREATED)
async def create_hero(hero_in: Annotated[HeroIn, File()], session: Session = Depends(get_session)) -> HeroOut:
    hero = Hero(heading=hero_in.heading, description=hero_in.description, image=hero_in.image)
    session.add(hero)
    session.commit()
    return HeroOut(
        id=hero.id,
        heading=hero.heading,
        description=hero.description,
        image_url=hero.image.public_url,
        created_at=hero.created_at,
        updated_at=hero.updated_at,
    )


@app.get("/heros/")
async def get_heros(session: Session = Depends(get_session)) -> list[HeroOut]:
    stmt = select(Hero).order_by(Hero.created_at.desc())
    heros = session.scalars(stmt).all()
    return [HeroOut(
        id=hero.id,
        heading=hero.heading,
        description=hero.description,
        image_url=hero.image.public_url,
        created_at=hero.created_at,
        updated_at=hero.updated_at
    ) for hero in heros]


@app.put("/heros/{hero_id}")
async def update_hero(hero_id: int, hero_in: Annotated[HeroUpdate, File()], session: Session = Depends(get_session)) -> HeroOut:
    hero = session.get(Hero, hero_id)
    if hero is None:
        raise HTTPException(status_code=404, detail="Hero not found")
    if hero_in.heading is not None:
        hero.heading = hero_in.heading
    if hero_in.description is not None:
        hero.description = hero_in.description
    if hero_in.image is not None:
        hero.image = hero_in.image
    session.commit()
    return HeroOut(
        id=hero.id,
        heading=hero.heading,
        description=hero.description,
        image_url=hero.image.public_url,
        created_at=hero.created_at,
        updated_at=hero.updated_at
    )


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
    image: UploadFile


class TeamMemberUpdate(TeamMemberBase):
    heading: str | None = None
    role: str | None = None
    description: str | None = None
    image: UploadFile | None = None


class TeamMemberOut(TeamMemberBase):
    id: int
    image_url: HttpUrl
    created_at: datetime
    updated_at: datetime


@app.post("/team_members/", status_code=status.HTTP_201_CREATED)
async def create_team_member(member_in: Annotated[TeamMemberIn, File()], session: Session = Depends(get_session)) -> TeamMemberOut:
    member = TeamMember(
        heading=member_in.heading,
        role=member_in.role,
        description=member_in.description,
        image=member_in.image
    )
    session.add(member)
    try:
        session.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail=f"Team member with heading '{member_in.heading}' already exists.")
    return TeamMemberOut(
        id=member.id,
        heading=member.heading,
        role=member.role,
        description=member.description,
        image_url=member.image.public_url,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


@app.get("/team_members/")
async def get_team_members(session: Session = Depends(get_session)) -> list[TeamMemberOut]:
    stmt = select(TeamMember).order_by(TeamMember.created_at.desc())
    members = session.scalars(stmt).all()
    return [TeamMemberOut(
        id=member.id,
        heading=member.heading,
        role=member.role,
        description=member.description,
        image_url=member.image.public_url,
        created_at=member.created_at,
        updated_at=member.updated_at
    ) for member in members]



@app.put("/team_members/{member_id}")
async def update_team_member(member_id: int, member_in: Annotated[TeamMemberUpdate, File()], session: Session = Depends(get_session)) -> TeamMemberOut:
    member = session.get(TeamMember, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Team member not found")

    update_data = {k: v for k, v in member_in.model_dump(exclude_unset=True).items() if v is not None}
    for attr, value in update_data.items():
        if hasattr(member, attr):
            setattr(member, attr, value)

    try:
        session.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail=f"Team member with heading '{member_in.heading}' already exists.")

    return TeamMemberOut(
        id=member.id,
        heading=member.heading,
        role=member.role,
        description=member.description,
        image_url=member.image.public_url,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


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
    pass # No extra fields needed for creation


class OtherInfoUpdate(BaseModel): # value can be explicitly set to None
    name: str | None = None
    value: str | None = None
    
    model_config = ConfigDict(str_strip_whitespace=True, str_min_length=1)


class OtherInfoOut(OtherInfoBase):
    id: int
    created_at: datetime
    updated_at: datetime


@app.post("/other_info/", status_code=status.HTTP_201_CREATED)
async def create_other_info(info_in: OtherInfoIn, session: Session = Depends(get_session)) -> OtherInfoOut:
    info = OtherInfo(name=info_in.name, value=info_in.value)
    session.add(info)
    try:
        session.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail=f"Information with name '{info_in.name}' already exists.")
        
    return OtherInfoOut(
        id=info.id,
        name=info.name,
        value=info.value,
        created_at=info.created_at,
        updated_at=info.updated_at
    )


@app.get("/other_info/")
async def get_all_other_info(session: Session = Depends(get_session)) -> list[OtherInfoOut]:
    stmt = select(OtherInfo).order_by(OtherInfo.created_at.desc())
    infos = session.scalars(stmt).all()
    return [OtherInfoOut(
        id=info.id,
        name=info.name,
        value=info.value,
        created_at=info.created_at,
        updated_at=info.updated_at
    ) for info in infos]


@app.get("/other_info/{info_name}")
async def get_other_info(info_name: str, session: Session = Depends(get_session)) -> OtherInfoOut:
    print(f"{info_name=}")
    stmt = select(OtherInfo).where(OtherInfo.name == info_name)
    info = session.scalar(stmt)
    if info is None:
        raise HTTPException(status_code=404, detail="Information not found")
    return OtherInfoOut(
        name=info.name,
        value=info.value,
        id=info.id,
        created_at=info.created_at,
        updated_at=info.updated_at
    )



@app.put("/other_info/{info_name}")
async def update_other_info(info_name: str, info_in: OtherInfoUpdate, session: Session = Depends(get_session)) -> OtherInfoOut:
    stmt = select(OtherInfo).where(OtherInfo.name == info_name)
    info = session.scalar(stmt)
    if info is None:
        raise HTTPException(status_code=404, detail="Information not found")

    update_data = info_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(info, key):
            setattr(info, key, value)
            

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        if 'name' in update_data:
             raise HTTPException(status_code=409, detail=f"Information with name '{info_in.name}' already exists.")
        else:
             raise HTTPException(status_code=409, detail="Data conflict during update.")

    return OtherInfoOut(
        name=info.name,
        value=info.value,
        id=info.id,
        created_at=info.created_at,
        updated_at=info.updated_at
    )


@app.delete("/other_info/{info_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_other_info(info_name: str, session: Session = Depends(get_session)):
    stmt = select(OtherInfo).where(OtherInfo.name == info_name)
    info = session.scalar(stmt)
    if info is None:
        raise HTTPException(status_code=404, detail="Information not found")
    session.delete(info)
    session.commit()