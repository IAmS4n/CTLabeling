export FLASK_APP=labeler
export FLASK_ENV=development
python -c 'import os; print(os.urandom(16))' > .secret_key
python -m flask init-db
