from fastapi import Depends, status

from fastapi_laser import fastapi_ext

from app import app_config, deps


router = fastapi_ext.get_router(dependencies=[Depends(deps.verify_sa_identity([app_config.scheduler_sa_email]))])


@router.get("/liveness", status_code=status.HTTP_200_OK)
def read_liveness():
    return


@router.get("/readiness", status_code=status.HTTP_200_OK)
def read_readiness():
    return dict(msg="Ready to go.")
