from src.services.uow import Uow


def get_uow() -> Uow:
    return Uow()
