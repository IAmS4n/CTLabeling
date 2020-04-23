#!/bin/bash
export FLASK_APP=labeler
#export FLASK_ENV=development
flask run || python -m flask run
