from flask import render_template, request, jsonify, flash, redirect, url_for
from src.lib.Mosaic import GenerateMosaic
import datetime
from src import app, config
from flask import Blueprint
import zipfile
from werkzeug.utils import secure_filename
import os
import time
import cv2

app.config['UPLOAD_FOLDER'] = "src/static/rgb"
app.config['ALLOWED_EXTENSIONS'] = {'zip'}

app.secret_key = 'supersecretkey'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/upload')
def uploadHome():
    return render_template('upload_images.html')

@app.route('/uploadRGB', methods=['POST'])
def upload_RGB():
    if 'file' not in request.files or 'foldername' not in request.form:
        flash('No file or folder name part')
        return redirect(request.url)
    file = request.files['file']
    foldername = request.form['foldername']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file: #and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_folder = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(foldername))
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        filepath = os.path.join(save_folder, filename)
        file.save(filepath)
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(save_folder)
        os.remove(filepath)
        flash(f'File successfully uploaded and extracted in {filename}')
        return redirect(url_for('uploadHome'))
    else:
        flash('Allowed file types are zip')
        return redirect(request.url)
    
@app.route('/select_folder')
def select_folder():
    folders = [d for d in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], d))]
    return render_template('select_folder.html', folders=folders)

@app.route('/process_folder', methods=['POST'])
def process_folder():
    foldername = request.form['foldername']
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], foldername)
    if not os.path.exists(folder_path):
        flash('Folder does not exist')
        return redirect(url_for('select_folder'))
    
    # Process the folder (e.g., list images)
    images = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    flash(f'Processing folder {foldername}. Images found: {images}')

    os.makedirs(f'src/static/rgb/results/{foldername}', exist_ok=True)

    obj = GenerateMosaic(parent_folder=folder_path , img_name_list=images[::2], result_folder=f'src/static/rgb/results/{foldername}')
    
    start_time = time.time()
    mosaic_img = obj.mosaic(resize=False)

    end_time = time.time()

    execution_time = end_time - start_time
    flash(f"Execution time: {execution_time} seconds")
    
    cv2.imwrite(f'src/static/rgb/final_results/{foldername}_panorama_final.jpg', mosaic_img[:, :, (2, 1, 0)])
    return redirect("/show_image/"+foldername)  

@app.route('/show_image/<foldername>')
def show_image(foldername):
    image_path = f'src/static/rgb/final_results/{foldername}_panorama_final.jpg'
    # image_path = 'src\static\\rgb\\results\\row_1\\results\panorama_0.jpg'
    if not os.path.exists(image_path):
        flash('Image not found')
        return redirect(url_for('select_folder'))
    # remove src from image_path
    image_path = image_path[4:]
    return render_template('show_image.html', foldername=foldername, image_path=image_path)
