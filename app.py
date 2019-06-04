from flask import Flask,request, redirect, render_template

from werkzeug.utils import secure_filename

import os

app = Flask(__name__)

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


@app.route('/', methods=["GET", "POST"])
def hello_world():
    if request.method == "POST":
        
        if request.files:
            
            if "filesize" in request.cookies:
                
                if not allowed_image_filesize(request.cookies["filesize"]):
                    print("Filesize exceeded maximum limit")
                    return redirect(request.url)
                    
                    image = request.files["image"]
                    
                    if image.filename == "":
                        print("No filename")
                        return redirect(request.url)
                
                    if allowed_image(image.filename):
                        filename = secure_filename(image.filename)
                        
                        image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
                        
                        return redirect(request.url)
                    
                    else:
                        print("That file extension is not allowed")
                        return redirect(request.url)
    
    return render_template("public/upload_image.html")



if __name__ == '__main__':
    app.run()
