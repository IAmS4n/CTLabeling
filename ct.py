from glob import glob

import numpy as np
import pydicom


def get_pixels_hu(slices):
    image = np.stack([s.pixel_array for s in slices])
    # Convert to int16 (from sometimes int16),
    # should be possible as values should always be low enough (<32k)
    image = image.astype(np.int16)

    # Set outside-of-scan pixels to 0
    # The intercept is usually -1024, so air is approximately 0
    #     image[image == -2000] = 0

    # Convert to Hounsfield units (HU)
    for slice_number in range(len(slices)):

        intercept = slices[slice_number].RescaleIntercept
        slope = slices[slice_number].RescaleSlope

        if slope != 1:
            image[slice_number] = slope * image[slice_number].astype(np.float64)
            image[slice_number] = image[slice_number].astype(np.int16)

        image[slice_number] += np.int16(intercept)

    return np.array(image, dtype=np.int16)


def color_process(ct):
    ct[ct < -1000] = -1000
    ct[ct > 400] = 400
    return (ct.astype(np.float32) + 1000.0) * (255.0 / 1400.0)


def get_ct(path, z_list):
    images = [
        image
        for image in glob(path + "/*")
        if "tmb" not in image.split("/")[-1]
    ]
    images = sorted(images, key=lambda x: x.split("/")[-1])

    selected_images = [images[z] for z in z_list]

    slices = [pydicom.read_file(image_dir) for image_dir in selected_images]
    hu_ct = get_pixels_hu(slices)
    gs_ct = color_process(hu_ct).astype(np.uint8)

    return gs_ct
