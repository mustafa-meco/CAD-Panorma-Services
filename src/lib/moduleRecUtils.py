
from pathlib import Path
from scipy import ndimage as ndi
from PIL import Image
import cv2
import numpy as np
# import matplotlib.pyplot as plt

def load_image(image_path: Path):
    image_format = image_path.suffix
    if image_format == '.jpg':
        return cv2.imread(image_path.as_posix())
    # elif image_format == '.tiff':
    #     return Thermogram(image_path)

from skimage.measure import regionprops
import json
def module_recognition(rgb_label_mask, min_module_area, max_non_complete_percentage, rgb_image):
    # Initialize a list to store the bounding boxes of recognized modules
    recognized_modules = []
    cropped_images_rgb = []

    # Iterate over the segmented regions in the RGB image
    for region in regionprops(rgb_label_mask):
        # Calculate the area of the region
        area = region.area

        # Check if the region's area meets the minimum module area requirement
        if area >= min_module_area:
            # Calculate the percentage of non-complete modules
            non_complete_percentage = (area - region.filled_area) / area * 100

            # Check if the non-complete percentage is within the threshold
            if non_complete_percentage <= max_non_complete_percentage:
                # Extract the bounding box coordinates of the region
                min_row, min_col, max_row, max_col = region.bbox

                # Append the bounding box coordinates to the list of recognized modules
                recognized_modules.append((min_row, min_col, max_row, max_col))

                # Crop the image based on the bounding box
                cropped_rgb = rgb_image[min_row-30:max_row+30, min_col-30:max_col+30]
                
                cropped_images_rgb.append(cropped_rgb)

    return recognized_modules, cropped_images_rgb

#Debugging without distortion
def process_single_image(rgb_image_path, min_module_area, max_non_complete_percentage, result_folder):
    undistorted_rgb = load_image(Path(rgb_image_path))
    # crop the image from the right and left sides only by 10% of the image width and keep the top and bottom as is
    undistorted_rgb = undistorted_rgb[:, int(undistorted_rgb.shape[1]*0.1):int(undistorted_rgb.shape[1]*0.9)]
    
    #undistorted_rgb = remove_distortion(rgb_image, 'rgb')

    # Apply segmentation steps here and use `module_recognition` function
    lower_blue = np.array([90, 100, 100])
    upper_blue = np.array([125, 255, 200])
    mask_1 = preprocess_rgb_image_manual(undistorted_rgb, lower_blue, upper_blue)
    mask_2 = preprocess_rgb_image_hsv_otsu(undistorted_rgb)
    blur = cv2.medianBlur(mask_2, 5)
    kernel = np.ones((7, 7), np.uint8)
    blur_open = cv2.morphologyEx(blur, cv2.MORPH_OPEN, kernel)
    kernel = np.ones((9, 9), np.uint8)
    module_mask = ndi.binary_fill_holes(blur_open, kernel)
    _, optical_label_mask = cv2.connectedComponents(module_mask.astype('uint8'))


    recognized_modules, cropped_images_rgb = module_recognition(
        optical_label_mask, min_module_area, max_non_complete_percentage, undistorted_rgb
    )

    # Save the cropped images
    for module_idx, cropped_rgb in enumerate(cropped_images_rgb, start=1):
        cv2.imwrite(result_folder+ f'/cropped_rgb_module_single_{module_idx}.png', cropped_rgb)
        
    # Create a list to store the module information
    module_info = []

    # Iterate over the recognized modules and generate module information
    for module_idx, recognized_module in enumerate(recognized_modules, start=1):
        # Generate the module ID
        module_id = f"module_{module_idx}"
        
        # Generate the image path
        image_path = f"{result_folder}/cropped_rgb_module_single_{module_idx}.png"
        
        # Create a dictionary to store the module information
        module_dict = {
            "id": module_idx,
            "image_path": image_path,
            "corners": {
                "top_left": {
                    "x": recognized_module[1],
                    "y": recognized_module[0]
                },
                "bottom_right": {
                    "x": recognized_module[3],
                    "y": recognized_module[2]
                }
            }
        }
        
        # Append the module information to the list
        module_info.append(module_dict)

    # Define the output JSON file path
    json_file_path = f"{result_folder}/jsons/module_info.json"

    # make the jsons folder if it does not exist
    if not Path(f"{result_folder}/jsons").exists():
        Path(f"{result_folder}/jsons").mkdir(parents=True, exist_ok=True)

    # Write the module information to the JSON file
    with open(json_file_path, "w") as json_file:
        json.dump(module_info, json_file)

    # Print a success message
    print(f"Module information has been stored in {json_file_path}")
    return recognized_modules, cropped_images_rgb

def preprocess_rgb_image_manual(image, lower_values, higher_values):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    return cv2.inRange(image, lower_values, higher_values)

def preprocess_rgb_image_hsv_otsu(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    masks = []
    for channel_index, channel_image in enumerate(cv2.split(image)):
        channel_image = cv2.GaussianBlur(channel_image, (3, 3), 0)
        max_value = 179 if channel_index == 0 else 255
        _, mask = cv2.threshold(
            channel_image, 0,
            max_value, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        masks.append(mask)

    result_mask = np.bitwise_and(masks[0], masks[1])
    return np.bitwise_and(result_mask, masks[2])

def draw_bounding_boxes(image, recognized_modules):
    # Make a copy of the image to draw on
    image_with_boxes = image.copy()
    
    # Iterate over the recognized modules and draw bounding boxes
    for min_row, min_col, max_row, max_col in recognized_modules:
        # Draw the bounding box
        cv2.rectangle(image_with_boxes, (min_col, min_row), (max_col, max_row), (0, 255, 0), 2)
    
    return image_with_boxes

def is_inside_boundary(x, y, module):
    top_left_x = module['corners']['top_left']['x']
    top_left_y = module['corners']['top_left']['y']
    bottom_right_x = module['corners']['bottom_right']['x']
    bottom_right_y = module['corners']['bottom_right']['y']
    
    return top_left_x <= x <= bottom_right_x and top_left_y <= y <= bottom_right_y

def find_module_containing_point(x, y, modules):
    for module in modules:
        if is_inside_boundary(x, y, module):
            return module['id']
    return None
def get_module_by_id(module_id, modules):
    for module in modules:
        if module['id'] == module_id:
            return module
    return None

def read_json_file(json_file_path):
    with open(json_file_path, "r") as json_file:
        return json.load(json_file)