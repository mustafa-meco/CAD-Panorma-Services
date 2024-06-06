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
from src.lib.moduleRecUtils import *

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
    distortion = request.form.get('distortion')
    resize = request.form.get('resize')
    rotate90 = request.form.get('rotate90')
    print(distortion, resize, rotate90)
    if distortion == 'on':
        distortion = True
    else:
        distortion = False
    if resize == 'on':
        resize = True
    else:
        resize = False
    if rotate90 == 'on':
        rotate90 = True
    else:
        rotate90 = False

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
    mosaic_img = obj.mosaic(resize=resize, distortion=distortion, rotate90=rotate90)

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

@app.route('/panels_rgb/<foldername>', methods=['POST'])
def panels_rgb(foldername):
    rgb_image_path = f'src/{request.form["image_path"]}'
    min_module_area = int(request.form["mod_area"])
    max_non_complete_percentage = int(request.form["max_non_com"])
    # rgb_folder = request.form["rgb_folder"]
    # Get the x and y coordinates of the click
    print(request.form.keys())
    
    recognized_modules, cropped_images_rgb = process_single_image(rgb_image_path, min_module_area, max_non_complete_percentage, result_folder=f'src/static/rgb/results/{foldername}/results')

    # Load the original image for drawing bounding boxes
    original_image = cv2.imread(rgb_image_path)
    # crop the image 10% from all sides
    original_image = original_image[:, int(original_image.shape[1]*0.1):int(original_image.shape[1]*0.9)]

    # Draw bounding boxes on the image
    image_with_boxes = draw_bounding_boxes(original_image, recognized_modules)

    cv2.imwrite(f'src/static/rgb/results/{foldername}/results/panels_rgb_{foldername}_boxes.jpg', image_with_boxes)
    processed_image_path = f'src/static/rgb/results/{foldername}/results/panels_rgb_{foldername}_boxes.jpg'
    # Process the coordinates as needed
    # print(f'Image clicked at coordinates: ({x}, {y})')
    # print(rgb_image_path)

    return render_template('show_modules.html', foldername=foldername, image_path=rgb_image_path[4:], processed_image_path=processed_image_path[4:])

@app.route('/process_click/<foldername>', methods=['POST'])
def process_click(foldername):
    x = int(request.form.get('image.x'))
    y = int(request.form.get('image.y'))
    modules = read_json_file(f'src\static\\rgb\\results\\{foldername}\\results\jsons\module_info.json')
    
    module_id = find_module_containing_point(x, y, modules)
    module = get_module_by_id(module_id, modules)
    image_path = module['image_path']

    print(f'Image clicked at coordinates: ({x}, {y})')
    return render_template('show_image_module.html', image_path=image_path[4:], module=module)