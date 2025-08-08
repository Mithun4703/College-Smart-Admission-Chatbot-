# Follow this after cloning this repo & use it

## Virtual Environment

Try either of these methods :

1. `pip install virtualenv`
2. `virtualenv venv`

--- OR ---

in VS Code, run `Ctrl+Shift+P` ,s earch for _Create environment_ & create one. **But don't tick the `requirements.txt`**

## Installations (in terminal)

1. `pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118`
   **Note** : I have used CUDA (GPU) so torch versions have `+cu116` written.
2. `pip install nltk spacy flask flask_sqlalchemy`
3. `python -m spacy download en_core_web_sm`
4. `pip install thinc wheel`

## Running the flask Server

1. In terminal run this command `cd flask_server`
2. In terminal run this command `set FLASK_APP=university.__init__.py`
3. then go to `college-enquiry-chatbot\flask_server\university\routes.py` file & uncomment `db.create_all()` in `hello_world` method
4. in terminal run this command `flask run` & open the browser & see the website working
5. go to `/teachers` url in browser & add some teachers
6. similiarly add some Courses, Students & holiday (more details later...)

## Training the Neural network

1. In terminal run this command `cd ..`
2. In terminal run this command `set FLASK_APP=run.py`
3. In terminal run this command `python train.py`

## Finally you can use the project

1. In terminal run this command `flask --app run run --host=0.0.0.0 --port=5000`
