from fastapi import status

from fastapi_laser import fastapi_ext


# Add dependencies here to apply them to the entire API
router = fastapi_ext.get_router(dependencies=[])


@router.get("/liveness", status_code=status.HTTP_200_OK)
def read_liveness():
    return


@router.get("/readiness", status_code=status.HTTP_200_OK)
def read_readiness():
    return dict(msg="Ready to go.")
