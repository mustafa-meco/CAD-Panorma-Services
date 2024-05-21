import cv2
import numpy as np


def calculate_homography(in_pts, out_pts):
    """
    in_pts = H*out_pts
    :param in_pts: correspond to src
    :param out_pts:
    :return:
    """

    if isinstance(in_pts, list):
        in_pts = np.array(in_pts)

    if isinstance(out_pts, list):
        out_pts = np.array(out_pts)

    mat_A, mat_b = build_sys_equations(in_pts, out_pts)

    H = np.matmul(np.linalg.pinv(mat_A), mat_b)

    # print(mat_b)
    #
    # print(np.matmul(mat_A, H))

    H = np.reshape(np.hstack((H,1)), (3,3))

    return H

def convert_to_homogenous_crd(inp, axis=1):

    if isinstance(inp, list):
        inp = np.array(inp)

    r, c = inp.shape

    if axis == 1:
        out = np.concatenate((inp, np.ones((r, 1))), axis=axis)
    else:
        out = np.concatenate((inp, np.ones((1, c))), axis=axis)

    return out

def get_pixel_coord(mask):
    """
    Function to get x, y coordinates of white pixels in mask as homogenous coordinates
    :param mask:
    :return:
    """
    y, x = np.where(mask)
    pts = np.concatenate((x[:,np.newaxis], y[:, np.newaxis], np.ones((x.size, 1))), axis=1) # rows of [x1, y1, 1]
    print(pts)

    return pts


def fit_image_in_target_space(img_src, img_dst, mask, H, offset=np.array([0, 0, 0])):
    """

    :param img_src: source image
    :param img_dst: destination image
    :param mask: mask corresponding to dest image
    :param H: pts_in_src_img = H * pts_in_dst_img
    :param offset: np array [x_offset, y_offset, 0]. Offset 0,0 in mask to this value
    :return:
    """

    pts = get_pixel_coord(mask)  # rows of [x1, y1, 1]

    pts = pts + offset

    out_src = np.matmul(H, pts.T)  # out_src has cols of [x1, y1, z1]

    out_src = out_src/out_src[-1,:]
    # print(out_src[-1,:])
    # print(out_src[:,0])

    # Return only x, y non-homogenous coordinates
    out_src = out_src[0:2, :]  # corresponds to pixels in img_src
    out_src = out_src.T  # rows of [x1, y1]

    # Convert pts to out_src convention
    pts = pts[:, 0:2].astype(np.int64)  # Corresponds to pixel locs in img_dst, rows of [x1,y1]

    h, w, _ = img_src.shape

    get_pixel_val(img_dst, img_src, pts, out_src, offset)

    # # x -> c  y -> r
    #  for i in range(out_src.shape[0]):
    #      if (0 <= out_src[i,0] < w-1) and (0 <= out_src[i,1] < h-1):
    #          img_dst[pts[i,1], pts[i,0], :] = get_pixel_val(out_src[i], img_src)


    return img_dst

def get_pixel_val(img_dst, img_src, pts, out_src, offset):
    """

    :param img_dst:
    :param pts: pts for img_dst rows of [x1, y1]
    :param out_src: rows of [x1, y1], corresponding pts in src img after homography on dst points
    :return:
    """
    h, w, _ = img_src.shape
    tl = np.floor(out_src[:, ::-1]).astype(np.int64) # reverse cols to get row, col notation
    br = np.ceil(out_src[:, ::-1]).astype(np.int64)

    pts = pts - offset[:2]

    r_lzero = np.where(~np.logical_or(np.any(tl < 0, axis=1), np.any(br < 0, axis=1)))
    pts = pts[r_lzero[0], :]
    out_src = out_src[r_lzero[0], :]
    tl = tl[r_lzero[0], :]
    br = br[r_lzero[0], :]

    r_fl = np.where(~np.logical_or(tl[:, 0] >= h-1, tl[:, 1] >= w-1))
    pts = pts[r_fl[0], :]
    out_src = out_src[r_fl[0], :]
    tl = tl[r_fl[0], :]
    br = br[r_fl[0], :]

    r_ce = np.where(~np.logical_or(br[:, 0] >= h-1, br[:, 1] >= w-1))
    pts = pts[r_ce[0], :]
    out_src = out_src[r_ce[0], :]
    tl = tl[r_ce[0], :]
    br = br[r_ce[0], :]

    print(pts.shape)
    print(out_src.shape)
    print(tl.shape)
    print(br.shape)

    tr = np.concatenate((tl[:, 0:1], br[:, 1:2]), axis=1)

    bl = np.concatenate((br[:, 0:1], tl[:, 1:2]), axis=1)

    weight = np.zeros((out_src.shape[0], 4))

    weight[:, 0] = np.linalg.norm(tl-out_src[:, ::-1], axis=1)
    weight[:, 1] = np.linalg.norm(tr-out_src[:, ::-1], axis=1)
    weight[:, 2] = np.linalg.norm(bl-out_src[:, ::-1], axis=1)
    weight[:, 3] = np.linalg.norm(br - out_src[:, ::-1], axis=1)

    weight[np.all(weight == 0, axis=1)] = 1  # For entries where they exactly overlap
    weight = 1/weight

    # pts = pts - offset[:2]

    img_dst[pts[:,1], pts[:,0], :] = (img_src[tl[:,0], tl[:,1], :] * weight[:, 0:1] + \
                                     img_src[tr[:,0], tr[:,1], :] * weight[:, 1:2] + \
                                     img_src[bl[:,0], bl[:,1], :] * weight[:, 2:3] + \
                                     img_src[br[:,0], br[:,1], :] * weight[:, 3:4])/ np.sum(weight, axis=1, keepdims=True)


    return img_dst



def build_sys_equations(in_pts, out_pts):
    """
    :param in_pts: nparray [[x1, y1], [x2, y2], ...]
    :param out_pts: nparray [[x1, y1], [x2, y2], ...]
    :param include_perp_bisector:
    :return:
    """

    mat_A = np.zeros((np.size(in_pts), 8))
    mat_b = in_pts.ravel()

    i = 0
    for x, y in out_pts:
        # x row
        mat_A[i][0:3] = [x, y, 1]
        mat_A[i][-2:] = [-x*mat_b[i], -y*mat_b[i]]

        # y row
        mat_A[i+1][-5:] = [x, y, 1, -x*mat_b[i+1], -y*mat_b[i+1]]

        # row counter
        i = i+2

    return mat_A, mat_b


def get_perp_bisectors(in_pts, out_pts):

    perp_in = np.array([in_pts[-1] + in_pts[0],
                        in_pts[0] + in_pts[1],
                        in_pts[1] + in_pts[2],
                        in_pts[2] + in_pts[3]])

    perp_out = np.array([out_pts[-1] + out_pts[0],
                         out_pts[0] + out_pts[1],
                         out_pts[1] + out_pts[2],
                         out_pts[2] + out_pts[3]])

    in_pts = np.concatenate((in_pts, perp_in / 2), axis=0)
    out_pts = np.concatenate((out_pts, perp_out / 2), axis=0)

    in_pts = in_pts.astype(np.int64)
    out_pts = out_pts.astype(np.int64)

    return in_pts, out_pts

import pickle
def remove_distortion(image: np.ndarray, image_type: str='rgb'):
    mapx_path = 'src\static\calibration files\RGB\mapx.pkl'
    mapy_path = 'src\static\calibration files\RGB\mapy.pkl'
    
    if image_type == 'ir':
        mapx_path = '/kaggle/input/photovoltaic-system-o-and-m-inspection/calibration files/IR/mapx.pkl'
        mapy_path = '/kaggle/input/photovoltaic-system-o-and-m-inspection/calibration files/IR/mapy.pkl'
    
    with open(mapx_path, 'rb') as mapx_file, open(mapy_path, 'rb') as mapy_file:
        mapx = pickle.load(mapx_file)
        mapy = pickle.load(mapy_file)

    return cv2.remap(image, mapx, mapy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)