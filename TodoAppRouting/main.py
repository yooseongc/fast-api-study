
from fastapi import FastAPI, Depends, status
from TodoAppRouting.routers import auth, todos
from TodoAppRouting.company import companyapis, dependencies

app = FastAPI()

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(companyapis.router,
                   prefix="/companyapis",
                   tags=["companyapis"],
                   dependencies=[Depends(dependencies.get_token_header)],
                   responses={status.HTTP_418_IM_A_TEAPOT: {"description": "Internal Use Only"}})


