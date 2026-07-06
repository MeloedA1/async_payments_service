from typing import Any

from src.services.uow import Uow
from tests.adapters import fake_models

MODEL_GENERATOR_MAP = {
    'payments': fake_models.make_payment,
    'outbox': fake_models.make_outbox,
}


def generate_fake_models(models_data):
    primary_models = {
        instance_name: MODEL_GENERATOR_MAP[data.pop('_model')](**data) for instance_name, data in models_data.items()
    }
    models_by_ids = {model.id: model for model in primary_models.values()}
    for model in primary_models.values():
        for column in model.__table__.columns:
            column_value = getattr(model, column.name)
            if isinstance(column_value, int) and column.name.endswith('_id'):
                setattr(model, column.name.replace('_id', ''), models_by_ids[column_value])
    return primary_models


async def generate_and_save_models(uow: Uow, models_data: dict[str, Any], save_in_db: bool = True) -> dict[str, Any]:
    try:
        name_model_map = generate_fake_models(models_data)
    except KeyError as e:
        raise Exception(f'Invalid models for fixtures generation., {e}')

    if not save_in_db:
        return name_model_map

    async with uow:
        _models = tuple(name_model_map.values())
        for model in _models:
            uow.session.add(model)
        await uow.commit()
        for model in _models:
            await uow.session.refresh(model)

    return name_model_map
