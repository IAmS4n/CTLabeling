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


def get_ct(path, wl, ww, z_list=None):
    images = [image for image in glob(path + "/*") if "tmb" not in image.split("/")[-1]]
    images = sorted(images, key=lambda x: x.split("/")[-1])

    if z_list is None:
        selected_images = images
    else:
        selected_images = [images[z] for z in z_list]

    slices = [pydicom.read_file(image_dir) for image_dir in selected_images]
    hu_ct = get_pixels_hu(slices)

    min_hu = float(wl - ww / 2.0)
    max_hu = float(wl + ww / 2.0)

    hu_ct = hu_ct.astype(np.float32)
    hu_ct[hu_ct < min_hu] = min_hu
    hu_ct[hu_ct > max_hu] = max_hu
    hu_ct -= min_hu
    hu_ct *= 255.0 / float(ww)

    hu_ct = hu_ct.astype(np.int16)
    hu_ct[hu_ct < 0] = 0
    hu_ct[hu_ct > 255] = 255

    return hu_ct.astype(np.uint8)
