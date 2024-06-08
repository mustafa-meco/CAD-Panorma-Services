# CADUtils.py
import ezdxf
import json
import os
import math

def likeText(text, like):
    return text.lower().replace(" ", "").replace("-", "").replace("_", "") == like.lower().replace(" ", "").replace("-", "").replace("_", "")

# print(likeText("MODULE_ALU_FRAME", "Module Alu frame")) # True

def extract_lwpolylines_from_layer(modelspace, layer_name):
    lwpolylines = []
    for entity in modelspace:
        if entity.dxftype() == 'LWPOLYLINE' and likeText(entity.dxf.layer , layer_name):
            # Extract points from LWPolyline
            points = [(vertex[0], vertex[1]) for vertex in entity.get_points('xy')]
            # Sort points by Y then X values
            sorted_points = sorted(points, key=lambda p: (p[1], p[0]))
            lwpolylines.append(sorted_points)

    return lwpolylines

def read_dxf_file(dxf_file):
    doc = ezdxf.readfile(dxf_file)
    modelspace = doc.modelspace()
    return modelspace

def get_entities(modelspace, layer_name):
    entities = []
    for entity in modelspace:
        if entity.dxf.layer == layer_name:
            entities.append(entity.dxf.__dict__)
    return entities


def get_dxf_files():
    return [f for f in os.listdir('src/dxf') if f.endswith('.dxf')]
def get_json_files():
    return [f for f in os.listdir('src/jsons') if f.endswith('.json')]

# Function to save LWPOLYLINE points to JSON file
def save_lwpolylines_to_json(lwpolylines, output_file):
    lwpolylines_objects = []
    centers = set()
    previous_center = (0, 0)
    for polyline in lwpolylines:
        # Calculate the center point of the bounding box
        min_x = min(int(point[0]) for point in polyline)
        max_x = max(int(point[0]) for point in polyline)
        min_y = min(int(point[1]) for point in polyline)
        max_y = max(int(point[1]) for point in polyline)
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        width = max_x - min_x
        height = max_y - min_y
        

        # Check if center point already exists
        if (center_x, center_y) in centers:
            continue

        row_diff = center_x - previous_center[0]
        column_diff = center_y - previous_center[1]
        # Calculate the row number based on center_x
        row = round(center_x/width)
        column = round(center_y/height)
        
        # Update the previous center point
        previous_center = (center_x, center_y)
        

        polyline_object = {
            "points": polyline,
            "center": (center_x, center_y),
            "row": row,  # Add the row attribute
            "column": column  # Add the column attribute
        }

        lwpolylines_objects.append(polyline_object)
        centers.add((center_x, center_y))
    
    # lwpolylines_objects = sorted(lwpolylines_objects, key=lambda polyline: (polyline['center'][0], polyline['center'][1]))
    for i, polyline in enumerate(lwpolylines_objects):
        polyline['id'] = i

    
    with open(output_file, 'w') as f:
        json.dump(lwpolylines_objects, f, indent=4)


def read_rows_json_file(json_file):
    with open(json_file, 'r') as f:
        lwpolylines_objects = json.load(f)
    
    rows = set()
    for polyline in lwpolylines_objects:
        rows.add(polyline['row'])
    
    return list(rows)

print(read_rows_json_file('src/data.json'))

def read_columns_json_file(json_file):
    with open(json_file, 'r') as f:
        lwpolylines_objects = json.load(f)
    
    columns = set()
    for polyline in lwpolylines_objects:
        columns.add(polyline['column'])
    
    return list(columns)

print(len(read_rows_json_file('src/data.json')))
print(len(read_columns_json_file('src/data.json')))

def get_module_ids_by_row(json_file, row):
    with open(json_file, 'r') as f:
        lwpolylines_objects = json.load(f)
    
    module_ids = []
    for polyline in lwpolylines_objects:
        if polyline['row'] == row:
            module_ids.append(polyline['id'])
    
    return module_ids

# [print("row:",row,"\nids no.:",len(get_module_ids_by_row('src/data.json', row))) for row in read_rows_json_file('src/data.json')]

def get_module_data_by_id(json_file, module_id):
    with open(json_file, 'r') as f:
        lwpolylines_objects = json.load(f)
    
    for polyline in lwpolylines_objects:
        if polyline['id'] == module_id:
            return polyline

    
    return None

def calculate_module_dimensions(json_file, module_id):
    module_data = get_module_data_by_id(json_file, module_id)
    if module_data:
        polyline_points = module_data['points']
        min_x = min(point[0] for point in polyline_points)
        max_x = max(point[0] for point in polyline_points)
        min_y = min(point[1] for point in polyline_points)
        max_y = max(point[1] for point in polyline_points)
        width = max_x - min_x
        height = max_y - min_y
        return width, height
    else:
        return None
    
print(calculate_module_dimensions('src/data.json', 0))  

def get_module_ids_by_column(json_file, column):
    with open(json_file, 'r') as f:
        lwpolylines_objects = json.load(f)
    
    module_ids = []
    for polyline in lwpolylines_objects:
        if polyline['column'] == column:
            module_ids.append(polyline['id'])
    
    return module_ids

def get_column_y(json_file, column):
    with open(json_file, 'r') as f:
        lwpolylines_objects = json.load(f)
    
    for polyline in lwpolylines_objects:
        if polyline['column'] == column:
            return polyline['center'][1]
    
    return None

def get_row_x(json_file, row):
    with open(json_file, 'r') as f:
        lwpolylines_objects = json.load(f)
    
    for polyline in lwpolylines_objects:
        if polyline['row'] == row:
            return polyline['center'][0]
    
    return None



def map_points_to_origin(json_file):
    with open(json_file, 'r') as f:
        lwpolylines_objects = json.load(f)
    
    min_x = min(point[0] for polyline in lwpolylines_objects for point in polyline['points'])
    min_y = min(point[1] for polyline in lwpolylines_objects for point in polyline['points'])
    
    for polyline in lwpolylines_objects:
        for point in polyline['points']:
            point[0] -= min_x
            point[1] -= min_y
    
    return lwpolylines_objects

def map_points_to_origin(input_file, output_file):
    # Load data from input JSON file
    with open(input_file, 'r') as file:
        data = json.load(file)

    # Find the minimum row and column values to determine the origin
    min_row = min(entry['row'] for entry in data)
    min_column = min(entry['column'] for entry in data)

    for entry in data:
        entry['row'] -= min_row 
        entry['column'] -= min_column
        # if entry['column'] > 60:
        #     entry['row'] -= 1    

    # Save mapped data to output JSON file
    with open(output_file, 'w') as outfile:
        json.dump(data, outfile, indent=4)



import json

def group_modules_by_row_and_consequent_columns(input_file, output_file, flag):
    # Load data from input JSON file
    with open(input_file, 'r') as file:
        data = json.load(file)

    # Sort data by row and column
    sorted_data = sorted(data, key=lambda x: (x['row'], x['column']))

    group_number = 0
    prev_row = None
    prev_column = None
    current_row = []
    # Add group attribute to modules with same row and consecutive columns
    for i, entry in enumerate(sorted_data):
        print(group_number)
        if entry['row'] == prev_row:
            current_row.append(entry)
            if i!= len(sorted_data) -1 and sorted_data[i+1]['row'] == entry['row']:
            
                dist_prev = abs(sorted_data[i-1]['column'] - entry['column'])
                dist_after = abs(entry['column'] - sorted_data[i+1]['column'])

                if entry['column'] > 60 and entry['column'] < 70 and flag:
                    entry['group'] = group_number    
                elif dist_prev <= dist_after:
                    entry['group'] = group_number
                else:
                    
                    group_number += 1
                    entry['group'] = group_number
            else:
                entry['group'] = group_number
        else:
            current_row = [entry]
            group_number += 1
            entry['group'] = group_number
        prev_row = entry['row']
        prev_column = entry['column']

    # Save updated data to output JSON file
    with open(output_file, 'w') as outfile:
        json.dump(sorted_data, outfile, indent=4)



def add_gpsdata(json_file, gps_data_jsonfile, outputfile):
    with open(json_file, 'r') as f:
        lwpolylines_objects = json.load(f)
    
    with open(gps_data_jsonfile, 'r') as f:
        gps_data = json.load(f) 
    
    objects_to_remove = []
    flag=False
    for i, polyline in enumerate(lwpolylines_objects):
        for gps in gps_data:
            if gps['id'] == polyline['group']:
                polyline['gps'] = {"corners_pixel": gps['corners_pixel'], 
                                   "gps_coordinates": gps['gps_coordinates'],
                                   }
                flag=True
                break
        if not flag:
            objects_to_remove.append(i)
        flag=False
    
    if objects_to_remove:
        lwpolylines_objects = lwpolylines_objects[:min(objects_to_remove)]
    
    with open(outputfile, 'w') as f:
        json.dump(lwpolylines_objects, f, indent=4)

# add_gpsdata('src/data.json', 'src/gps_data.json', 'src/data.json')     

# group_modules_by_row_and_consequent_columns('src/data.json', 'src/grouped_data.json')

# def group_by_rows(input_file, output_file):
#     # Load data from input JSON file
#     rows = read_rows_json_file(input_file)
#     group_number = 0
#     modules_data = []
#     for row in rows:
#         print("row:", row)
#         module_ids = get_module_ids_by_row(input_file, row)
#         modules_data.extend([get_module_data_by_id(input_file, module_id) for module_id in module_ids])
    
#     # sort modules by column
#     modules_data = sorted(modules_data, key=lambda x: x['column'])
    
#     for i, module_data in enumerate(modules_data):
#         # check if the module is the first in the row
#         if i == 0:
#             group_number += 1
#             module_data['group'] = group_number
#         # check if the module is the last in the row
#         elif i == len(modules_data) - 1:
#             module_data['group'] = group_number
#         else:
#             dist_prev = abs(get_column_y(input_file, modules_data[i-1]['column']) - get_column_y(input_file, module_data['column']))
#             dist_after = abs(get_column_y(input_file, module_data['column']) - get_column_y(input_file, modules_data[i+1]['column']))
#             print("dist_prev:", dist_prev)
#             print("dist_after:", dist_after)
#             if dist_prev < dist_after:
#                 module_data['group'] = group_number
#             else:
#                 group_number += 1
#                 module_data['group'] = group_number

#     # Save updated data to output JSON file
#     with open(output_file, 'w') as outfile:
#         json.dump(modules_data, outfile, indent=4)


# group_by_rows('src/data.json', 'src/grouped_data.json')

