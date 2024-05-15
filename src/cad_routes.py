from flask import render_template, request, jsonify
from src.lib.CADUtils import *
import datetime
from src import app, config
from flask import Blueprint

@app.route('/uploadCAD', methods=['POST'])
def uploadCAD():
    dxf_file = request.files['file']
    dxf_file.save(f'src/dxf/{dxf_file.filename}')
    return render_template('choose_dxf.html')

@app.route('/processCAD', methods=['POST'])
def processCAD():
    dxf_filename = request.form['filename']
    # print(dxf_filename)
    layer_name = request.form['layer_name']
    modelspace = read_dxf_file(f"src/dxf/{dxf_filename}")
    lwpolylines = extract_lwpolylines_from_layer(modelspace, layer_name)
    current_time = datetime.datetime.now()
    day_and_time = current_time.strftime("%A_%H_%M")
    save_lwpolylines_to_json(lwpolylines, f"src/jsons/lwpolylines-{day_and_time}.json")
    save_lwpolylines_to_json(lwpolylines, f"src/data.json")
    map_points_to_origin('src/data.json', 'src/data.json')
    group_modules_by_row_and_consequent_columns('src/data.json', 'src/data.json', dxf_filename == "Packing - PV - 02 - REV 4_dwg.dxf")
    add_gpsdata('src/data.json', 'src/gps_data.json', 'src/data.json')
    return jsonify(extract_lwpolylines_from_layer(modelspace, layer_name))

@app.route('/processCADweb', methods=['POST'])
def processCADweb():
    dxf_filename = request.form['filename']
    # print(dxf_filename)
    layer_name = request.form['layer_name']
    modelspace = read_dxf_file(f"src/dxf/{dxf_filename}")
    lwpolylines = extract_lwpolylines_from_layer(modelspace, layer_name)
    current_time = datetime.datetime.now()
    day_and_time = current_time.strftime("%A_%H_%M")
    save_lwpolylines_to_json(lwpolylines, f"src/jsons/lwpolylines-{day_and_time}.json")
    save_lwpolylines_to_json(lwpolylines, f"src/data.json")
    map_points_to_origin('src/data.json', 'src/data.json')
    group_modules_by_row_and_consequent_columns('src/data.json', 'src/data.json', dxf_filename == "Packing - PV - 02 - REV 4_dwg.dxf")
    add_gpsdata('src/data.json', 'src/gps_data.json', 'src/data.json')
    return render_template('view.html')

@app.route('/getDxfFiles', methods=['GET'])
def getDxfFiles():
    return jsonify([{"filename": dxf_file} for dxf_file in get_dxf_files()])

@app.route('/getJsonFiles', methods=['GET'])
def getJSONFiles():
    print(get_json_files())
    return jsonify([{"filename": json_file} for json_file in get_json_files()])

@app.route('/choose_dxf', methods=['GET'])
def choose_dxf():
    return render_template('choose_dxf.html')

@app.route('/choose_json', methods=['GET'])
def choose_json():
    return render_template('choose_json.html')



from flask import send_from_directory 
@app.route('/images/<path:filename>')
def get_image(filename):
    return send_from_directory('src/static/images', filename)

@app.route('/plotlyfile', methods=['POST'])
def plotlyfile():
    json_file = request.form['json_file']
    f = open(f"src/jsons/{json_file}", 'r')
    data = json.load(f)
    f.close()
    with open('data.json', 'w') as f2:
        json.dump(data, f2)
    
    return render_template('plotly_page.html')

@app.route('/viewBoxes', methods=['GET'])
def viewBoxes():
    return render_template('view.html')

# route to return json file based on its name
@app.route('/getJsonFile', methods=['GET'])
def getJsonFile():
    json_file = "src/data.json"
    with open(json_file, 'r') as f:
        data = json.load(f)
    return jsonify(data)

# get json file by name endpoint
@app.route('/getJsonFileByName', methods=['POST'])
def getJsonFileByName():
    json_file = request.get_json()['filename']
    print(json_file)
    print(json_file)
    with open(f"src/jsons/{json_file}", 'r') as f:
        data = json.load(f)
    return jsonify(data)

from flask import Blueprint
import os

# main blueprint to be registered with application
api = Blueprint('api', __name__)

@api.route('/uploadCAD', methods=['POST'])
def uploadCAD():
    dxf_file = request.files['file']
    folder = 'src/dxf'
    if not os.path.exists(folder):
        os.makedirs(folder)
    dxf_file.save(f'src/dxf/{dxf_file.filename}')
    return jsonify({'message': 'DXF file uploaded successfully'})

@api.route('/processCAD', methods=['POST'])
def processCAD():
    print("request is:  ", request.form)
    dxf_filename = request.get_json()['filename']
    layer_name = request.get_json()['layer_name']
    modelspace = read_dxf_file(f"src/dxf/{dxf_filename}")
    lwpolylines = extract_lwpolylines_from_layer(modelspace, layer_name)
    current_time = datetime.datetime.now()
    day_and_time = current_time.strftime("%A_%H_%M")
    save_lwpolylines_to_json(lwpolylines, f"src/jsons/lwpolylines-{day_and_time}.json")
    save_lwpolylines_to_json(lwpolylines, f"src/data.json")
    map_points_to_origin('src/data.json', 'src/data.json')
    group_modules_by_row_and_consequent_columns('src/data.json', 'src/data.json', dxf_filename == "Packing - PV - 02 - REV 4_dwg.dxf")
    add_gpsdata('src/data.json', 'src/gps_data.json', 'src/data.json')
    # read data from json file and return it
    with open("src/data.json", 'r') as f:
        lwpolylines = json.load(f)
        
    return jsonify(lwpolylines)

@api.route('/processUploadCAD', methods=['POST'])
def processUploadCAD():
    dxf_file = request.files['file']
    dxf_file.save(f'src/dxf/{dxf_file.filename}')
    dxf_filename = dxf_file.filename
    layer_name = "MODULE_ALU_FRAME"
    modelspace = read_dxf_file(f"src/dxf/{dxf_filename}")
    lwpolylines = extract_lwpolylines_from_layer(modelspace, layer_name)
    current_time = datetime.datetime.now()
    day_and_time = current_time.strftime("%A_%H_%M")
    save_lwpolylines_to_json(lwpolylines, f"src/jsons/lwpolylines-{day_and_time}.json")
    save_lwpolylines_to_json(lwpolylines, f"src/data.json")
    map_points_to_origin('src/data.json', 'src/data.json')
    group_modules_by_row_and_consequent_columns('src/data.json', 'src/data.json', dxf_filename == "Packing - PV - 02 - REV 4_dwg.dxf")
    add_gpsdata('src/data.json', 'src/gps_data.json', 'src/data.json')
    return jsonify(lwpolylines)

@api.route('/getDxfFiles', methods=['GET'])
def getDxfFiles():
    return jsonify([{"filename": dxf_file} for dxf_file in get_dxf_files()])

@api.route('/getJsonFiles', methods=['GET'])
def getJSONFiles():
    return jsonify([{"filename": json_file} for json_file in get_json_files()])

@api.route('/plotlyfile', methods=['POST'])
def plotlyfile():
    json_file = request.form['json_file']
    with open(f"src/jsons/{json_file}", 'r') as f:
        data = json.load(f)
    return jsonify(data)

@api.route('/getJsonFile', methods=['GET'])
def getJsonFile():
    json_file = "data.json"
    with open(json_file, 'r') as f:
        data = json.load(f)
    return jsonify(data)

@api.route('/getJsonFileByName', methods=['POST'])
def getJsonFileByName():
    json_file = request.get_json()['filename']
    with open(f"src/jsons/{json_file}", 'r') as f:
        data = json.load(f)
    return jsonify(data)