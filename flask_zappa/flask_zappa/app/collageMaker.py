import argparse
import os
import random
from PIL import Image
import requests
import boto3
import time
import random
import io
from app import dynamo

def make_collage(images, profile_name):

    if not images:
        print('No images for collage found!')
        return False

    # find smallest width and height
    width_list = []
    height_list = []
    for im in images:
        # with Image.open(im) as img:
        with Image.open(requests.get(im, stream=True).raw) as img:
            width, height = img.size
            width_list.append(width)
            height_list.append(height)
    width_list.sort()
    height_list.sort()

    min_width = width_list[0]
    min_height = height_list[0]

    avg_width = sum(width_list) // len(width_list)
    avg_height = sum(height_list) // len(height_list)

    width = avg_width
    init_height = avg_height

    margin_size = 2
    # run until a suitable arrangement of images is found
    while True:
        # copy images to images_list
        images_list = images[:]
        coefs_lines = []
        images_line = []
        x = 0
        while images_list:
            # get first image and resize to `init_height`
            img_path = images_list.pop(0)
            img = Image.open(requests.get(img_path, stream=True).raw) #Image.open(img_path)
            img.thumbnail((width, init_height))
            # when `x` will go beyond the `width`, start the next line
            if x > width:
                coefs_lines.append((float(x) / width, images_line))
                images_line = []
                x = 0
            x += img.size[0] + margin_size
            images_line.append(img_path)
        # finally add the last line with images
        coefs_lines.append((float(x) / width, images_line))

        # compact the lines, by reducing the `init_height`, if any with one or less images
        if len(coefs_lines) <= 1:
            break
        if any(map(lambda c: len(c[1]) <= 1, coefs_lines)):
            # reduce `init_height`
            init_height -= 10
        else:
            break

    # get output height
    out_height = 0
    for coef, imgs_line in coefs_lines:
        if imgs_line:
            out_height += int(init_height / coef) + margin_size
    if not out_height:
        print('Height of collage could not be 0!')
        return False

    collage_image = Image.new('RGB', (width, int(out_height)), (35, 35, 35))
    # put images to the collage
    y = 0
    for coef, imgs_line in coefs_lines:
        # console.log(coef)
        if imgs_line:
            x = 0
            for img_path in imgs_line:
                img = Image.open(requests.get(img_path, stream=True).raw) #Image.open(img_path)
                # if need to enlarge an image - use `resize`, otherwise use `thumbnail`, it's faster
                k = (init_height / coef) / img.size[1]
                if k > 1:
                    img = img.resize((int(img.size[0] * k), int(img.size[1] * k)), Image.ANTIALIAS)
                else:
                    img.thumbnail((int(width / coef), int(init_height / coef)), Image.ANTIALIAS)
                if collage_image:
                    collage_image.paste(img, (int(x), int(y)))
                x += img.size[0] + margin_size
            y += int(init_height / coef) + margin_size

    # Create an S3 client
    s3 = boto3.client('s3')
    id = "lambdas3source.collages"
    #Creating unique name
    unique_name = profile_name + '_' + 'collage.jpg'

    # Upload image to S3
    image_new_name = unique_name
    imgByteArr = io.BytesIO()
    collage_image.save(imgByteArr, format='PNG')
    imgByteArr = imgByteArr.getvalue()

    s3.delete_object(Bucket=id, Key=image_new_name)
    s3.put_object(Body=imgByteArr, Bucket=id, Key=image_new_name)
    image_url = (s3.generate_presigned_url('get_object', Params={'Bucket': id, 'Key': image_new_name},
                                           ExpiresIn=100)).split('?')[0]

    #Add to db
    dynamo.update_collages_table(profile_name, image_url)

    return True
