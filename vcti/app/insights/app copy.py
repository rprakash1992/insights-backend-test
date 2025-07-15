#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.

from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from dotenv import load_dotenv
import os

from .dependencies import setup, shutdown, static_folder_path

from .api import (
    templates,
    fs,
    variables,
)

ROUTERS = [
    templates,
    fs,
    variables
]

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup()
    yield  # App runs here
    shutdown()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for route in ROUTERS:
    app.include_router(
        route.router,
        prefix="/api/" + route.prefix,
        tags = route.tags
    )

app.mount("/static", StaticFiles(directory=static_folder_path()), name="static")

# Serve ui
@app.get("/ui")
async def serve_ui():
    return FileResponse(os.path.join(static_folder_path(), "ui", "index.html"))
    # return FileResponse(os.path.join(os.path.dirname(__file__), "static", "ui", "index.html"))


# Serve wcaxviewer
@app.get("/wcaxviewer")
async def serve_wcaxviewer():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "wcaxviewer", "WCAXVIEWER.html"))