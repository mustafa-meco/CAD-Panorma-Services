import pickle
import cv2
import numpy as np

def remove_distortion(image: np.ndarray, image_type: str='rgb'):
    mapx_path = 'calibration files\RGB\mapx.pkl'
    mapy_path = 'calibration files\RGB\mapy.pkl'
    
    
    with open(mapx_path, 'rb') as mapx_file, open(mapy_path, 'rb') as mapy_file:
        mapx = pickle.load(mapx_file)
        mapy = pickle.load(mapy_file)

    return cv2.remap(image, mapx, mapy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

def main():
    image = cv2.imread('frame_000033.jpg')
    undistorted_image = remove_distortion(image)
    cv2.imwrite('undistorted_image.jpg', undistorted_image)

if __name__ == '__main__':
    main()

