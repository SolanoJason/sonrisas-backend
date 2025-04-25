import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models import Base, OtherInfo
from app.config import get_settings

# Configuración de la conexión a la base de datos para tests
@pytest.fixture
async def async_session():
    """Crea una sesión de base de datos asíncrona para testing."""
    settings = get_settings()
    
    # Crea un motor de base de datos para test
    engine = create_async_engine(
        settings.DATABASE_URL_TEST,
        echo=False,
    )
    
    # Crea las tablas en la base de datos de test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Crea una sesión para los tests
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
    
    # Limpia después de los tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_other_info_tiktok_row_exists(async_session):
    """
    Test para verificar que siempre existe una fila en OtherInfo con name='tiktok'.
    """
    # Buscar si existe una fila con name='tiktok'
    result = await async_session.execute(
        select(OtherInfo).where(OtherInfo.name == "tiktok")
    )
    tiktok_row = result.scalars().first()
    
    # Si no existe, verificar que se crea automáticamente al iniciar la aplicación
    if not tiktok_row:
        # Este test fallará para indicar que debe crearse esta fila
        # en el proceso de inicialización de la aplicación
        assert False, "No existe una fila con name='tiktok' en la tabla OtherInfo"
    
    # Verificar que la fila existe
    assert tiktok_row is not None
    assert tiktok_row.name == "tiktok"


# Test adicional para verificar que podemos crear y actualizar el valor de tiktok
@pytest.mark.asyncio
async def test_other_info_tiktok_crud(async_session):
    """
    Test para verificar operaciones CRUD en la fila tiktok de OtherInfo.
    """
    # Crear una fila con name='tiktok'
    tiktok_info = OtherInfo(name="tiktok", value="https://tiktok.com/@ejemplo")
    async_session.add(tiktok_info)
    await async_session.commit()
    
    # Buscar la fila creada
    result = await async_session.execute(
        select(OtherInfo).where(OtherInfo.name == "tiktok")
    )
    tiktok_row = result.scalars().first()
    
    # Verificar que la fila existe y tiene el valor correcto
    assert tiktok_row is not None
    assert tiktok_row.name == "tiktok"
    assert tiktok_row.value == "https://tiktok.com/@ejemplo"
    
    # Actualizar el valor
    tiktok_row.value = "https://tiktok.com/@nuevo_ejemplo"
    await async_session.commit()
    
    # Verificar que el valor se actualizó
    result = await async_session.execute(
        select(OtherInfo).where(OtherInfo.name == "tiktok")
    )
    updated_tiktok_row = result.scalars().first()
    
    assert updated_tiktok_row is not None
    assert updated_tiktok_row.value == "https://tiktok.com/@nuevo_ejemplo" 