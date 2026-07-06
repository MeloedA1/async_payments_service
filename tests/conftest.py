import logging

import pytest

from src.config import settings
from src.domain.models import Base
from src.services.uow import Uow, get_engine, get_session_factory
from tests.adapters.fake_db import generate_and_save_models

logger = logging.Logger('tests')


@pytest.fixture
async def fake_uow():
    engine = get_engine(db_name=f'test_{settings.db_name}')
    test_session_factory = get_session_factory(engine)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return Uow(session_factory=test_session_factory)


@pytest.fixture
async def prepared_models(request, fake_uow: Uow):
    """
    Creates fixture with models and case data.

    Examples in models_data see in generate_and_save_models function docstring.
    Any additional data will be added to case_data param in request.
    """
    models_data = request.param.get('models')
    if models_data is None:
        raise ValueError('Models param is required for this fixture!')
    if models_data:
        models = await generate_and_save_models(fake_uow, models_data)
    else:
        models = {}
    return {'models': models, 'uow': fake_uow}
