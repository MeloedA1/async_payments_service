from fastapi import FastAPI
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.entrypoints.rest.payments import payments_router
from src.exceptions import NotFoundException, ObjAlreadyExists, ValidateError

app = FastAPI(title='Async Payments Service')
app.include_router(payments_router)


@app.exception_handler(NotFoundException)
def obj_does_not_exists_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={'detail': str(exc) or 'Object does not exists.'},
    )


@app.exception_handler(ObjAlreadyExists)
def obj_already_exist_handler(request: Request, exc: ObjAlreadyExists):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={'detail': str(exc) or 'Object already exists.'},
    )


@app.exception_handler(ValidateError)
def validate_error_handler(request: Request, exc: ValidateError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={'detail': str(exc) or 'Validation error.'},
    )


@app.get('/health')
def health_check():
    return {'status': 'ok'}
