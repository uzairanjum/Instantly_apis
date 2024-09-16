# INSTANTLY RESPONDER API V1

# create virtual environment
python -m venv env
 
# activate environment
source ./env/Scripts/activate (window)
source ./env/bin/activate (macos)

# install dependencies
pip install -r requirements.txt

# start application
uvicorn index:app --port=3000 --reload



