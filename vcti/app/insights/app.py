#!/usr/bin/env python

# Copyright (C) 2018 Visual Collaboration Technologies Inc.
# All Rights Reserved.
#
# This file is a property of Visual Collaboration Technologies Inc.
# Unauthorized access, reproduction or redistribution of any kind is prohibited.

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import os

from .api import fs, runs, templates, variables
from .app_context import setup, shutdown, static_files_directory

ROUTERS = [templates, fs, variables, runs]

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
    app.include_router(route.router, prefix="/api/" + route.prefix, tags=route.tags)

# app.mount("/static", StaticFiles(directory=static_files_directory()), name="static")

base_path = os.path.dirname(__file__)
static_dir = Path(base_path) / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

print(static_dir, "static_dirrrrrrrrrrr")
print("static_files_directory:", static_files_directory())

# Serve ui
@app.get("/ui")
async def serve_ui():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "ui", "index.html"))


# Serve wcaxviewer
@app.get("/wcaxviewer")
async def serve_wcaxviewer():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "wcaxviewer", "WCAXVIEWER.html"))