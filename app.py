import os
import sys
import json
from fastai import *
from fastai.vision import *
from torch import *

import base64

from torchvision.transforms import ToTensor, ToPILImage
from PIL import Image

import matplotlib as mpl

import numpy as np
from skimage.transform import resize

import torch
import torch.nn.functional as F

from flask import Flask, request, redirect, render_template, flash, jsonify
from werkzeug.utils import secure_filename


class InvalidUsage(Exception):
    status_code = 400
    
    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

def normalize(image):
    imagenet_stats = ([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    mean = torch.Tensor(imagenet_stats[0])
    std = torch.Tensor(imagenet_stats[1])

    print(f'Normalize image shape: {image.shape}, mean shape: {mean.shape}, std shape: {std.shape}')
    return (image - mean[..., None, None]) / std[..., None, None]

class SaveFeatures():
    features = None
    
    def __init__(self, m): self.hook = m.register_forward_hook(self.hook_fn)
    
    def hook_fn(self, module, input, output): self.features = output
    
    def remove(self): self.hook.remove()

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
                                                    
    app.config["IMAGE_UPLOADS"] = "~/"
    app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "GIF"]
    app.config["MAX_IMAGE_FILESIZE"] = 0.5 * 1024 * 1024

    def allowed_image(filename):
    
    
        if not "." in filename:
            return False
        print(". is in filename")
        sys.stdout.flush()
        ext = filename.rsplit(".", 1)[1]
        
        if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
            print("extension is allowed")
            sys.stdout.flush()
            return True
        else:
            print("extension is now allowed")
            sys.stdout.flush()
            return False


    def allowed_image_filesize(filesize):
    
        if int(filesize) <= app.config["MAX_IMAGE_FILESIZE"]:
            return True
        else:
                return False

                    
    def predict(image):

        classes = ['Fainare', 'Pyrenophora', 'RuginaBruna', 'RuginaGalbena', 'RuginaNeagra']
        path="assets"
        data2= ImageDataBunch.single_from_classes(path, classes, ds_tfms=get_transforms(),size=224).normalize(imagenet_stats)
        learn = cnn_learner(data2, models.resnet34)
        learn.load('stage-1')
    
        learn.model.eval().float().cpu()
    
        image = image.resize((224,224))

        target = learn.model[0][-1][-1]
        heatmap_features_size = (512, 224 // 32, 224 // 32)

        toTensor = ToTensor()
        img = toTensor(image)
        img = normalize(img)

        sfs = SaveFeatures(target)
        out = learn.model(img.unsqueeze(0))
        predictions = torch.sigmoid(out).cpu().detach().numpy()[0]
        sfs.remove()

        heatmap_features = sfs.features.reshape(heatmap_features_size)
        values, indices = heatmap_features.max(0)

        heatmap = values.cpu().detach().numpy()
        heatmap = resize(heatmap, (224, 224), anti_aliasing=True)

        heat_interp = np.interp(heatmap, (heatmap.min(), heatmap.max()), (0, 1))
        heat_interp = mpl.cm.plasma(heat_interp)[:, :, 0:3]
        heat_interp = np.uint8(heat_interp * 255)
        heatmap_pil = Image.fromarray(heat_interp)

        print(predictions)
        sys.stdout.flush()
        return Image.blend(image.convert('RGB'), heatmap_pil, alpha=0.5)
        
        
        # return json.dumps(predictions.tolist())

    @app.errorhandler(InvalidUsage)
    def handle_invalid_usage(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response


    @app.route("/upload-image", methods=["GET", "POST"])
    def upload_image():
    
        if request.method == "POST":
            
            
            print("Requesting")
            sys.stdout.flush()
            
            if request.files:
            
                image = request.files["image"]
            
                if image.filename == "":
                    print("No filename")
                    sys.stdout.flush()
                    raise InvalidUsage('No filename', status_code=410)
        
                print("CHECKING FILENAME")
                sys.stdout.flush()
                if allowed_image(image.filename):
                    filename = secure_filename(image.filename)
        
        #image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
                    img = Image.open(image.stream)
                    
                    predicted_img = predict(img)
                    
                    predicted_img.save("predicted.jpg")
                    
                    with open("predicted.jpg", "rb") as imageFile:
                        str = base64.b64encode(imageFile.read())
                        print(str)
                        sys.stdout.flush()
                    return json.dumps(str)
                    
                
                else:
                    print("That file extension is not allowed")
                    sys.stdout.flush()
                    raise InvalidUsage('That file extension is not allowed', status_code=410)

            
            else:
                print("No files in request")
                sys.stdout.flush()
                raise InvalidUsage('No files in request', status_code=410)
    
                       

        return render_template("public/upload_image.html")
            
    return app

app = create_app()

if __name__ == '__main__':
    app.run()
