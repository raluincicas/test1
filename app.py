import os
import sys
import json

from flask import Flask, request, redirect, render_template, flash
from werkzeug.utils import secure_filename



def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
                            SECRET_KEY='dev',
                            DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
                            )
        
    if test_config is None:
                                # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
                                # load the test config if passed in
        app.config.from_mapping(test_config)
                                    
                                    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
                                                    
    app.config["IMAGE_UPLOADS"] = "/Users/ralucaincicas/Documents/Developer/server/static/img/upload"
    app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "GIF"]
    app.config["MAX_IMAGE_FILESIZE"] = 0.5 * 1024 * 1024

    def allowed_image(filename):
    
        if not "." in filename:
            return False

        ext = filename.rsplit(".", 1)[1]

        if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
            return True
        else:
            return False


    def allowed_image_filesize(filesize):
    
        if int(filesize) <= app.config["MAX_IMAGE_FILESIZE"]:
            return True
        else:
                return False

    @app.errorhandler(InvalidUsage)
    def handle_invalid_usage(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response


    @app.route("/upload-image", methods=["GET", "POST"])
    def upload_image():
    
        if request.method == "POST":
            
            
            
            if request.files:
            
                if "filesize" in request.cookies:
                
                    if not allowed_image_filesize(request.cookies["filesize"]):
                        print("Filesize exceeded maximum limit")
                        raise InvalidUsage('Filesize exceeded maximum limit', status_code=410)
                    
                
                    image = request.files["image"]
                
                    if image.filename == "":
                        print("No filename")
                         raise InvalidUsage('No filename', status_code=410)
            
    
                    if allowed_image(image.filename):
                        filename = secure_filename(image.filename)
            
                        image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
                        row = [1,2]
                        json= json.dumps(row)
                        print(json)
                        sys.stdout.flush()
                        return json
                        
                    else:
                        print("That file extension is not allowed")
                         raise InvalidUsage('That file extension is not allowed', status_code=410)
                        return redirect(request.url)

        return render_template("public/upload_image.html")
            
    return app

app = create_app()

if __name__ == '__main__':
    app.run()
