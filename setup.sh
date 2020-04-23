#!/bin/bash
export FLASK_APP=labeler
#export FLASK_ENV=development
python -c 'import os; print(os.urandom(16))' >.secret_key
flask init-db || python -m flask init-db
rm -- "$0" # setup.sh will be removed
echo "Setup file will be removed..."
echo "NOTE : Maybe the sort needs be adapted with slices name format. (./labeler/ct.py:38)"

