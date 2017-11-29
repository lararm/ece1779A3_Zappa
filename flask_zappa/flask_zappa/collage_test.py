import argparse
import os
import random
from PIL import Image
import PIL
import numpy as np
import requests

def make_collage():
    url = "https://s3.amazonaws.com/lambdas3source/beach1.jpg"
    ims3 = Image.open(requests.get(url, stream=True).raw)
    width, height = ims3.size
    print("s3 ")
    print(width)



    images = ['flower1.jpg', 'flower2.jpg','flower3.jpg', 'Image3.jpg', 'Image2.jpg', 'Image4.jpg']
    filename = 'collage5avg.jpg'

    imgs = [PIL.Image.open(i) for i in images]
    # pick the image which is the smallest, and resize the others to match it (can be arbitrary image shape here)
    min_shape = sorted([(np.sum(i.size), i.size) for i in imgs])[0][1]
    print(min_shape)
    for i in imgs:
        i.resize(min_shape)

    #find smallest width and height
    width_list=[]
    height_list=[]
    for im in images:
        with Image.open(im) as img:
            width, height = img.size
            width_list.append(width)
            height_list.append(height)
    width_list.sort()
    height_list.sort()

    min_width = width_list[0]
    min_height = height_list[0]

    avg_width = sum(width_list) // len(width_list)
    avg_height = sum(height_list)// len(height_list)


    print(avg_height, avg_width)
    print(min_width,min_height)

    width = avg_height #min_width #avg_height
    init_height = avg_width #min_width #avg_width

    print("#make_collage")
    """
    Make a collage image with a width equal to `width` from `images` and save to `filename`.
    """
    if not images:
        print('No images for collage found!')
        return False

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
            print(img_path)
            img = Image.open(img_path)
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
                img = Image.open(img_path)
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
    collage_image.save(filename)
    return True


def main():
    print("main")
    # prepare argument parser
    parse = argparse.ArgumentParser(description='Photo collage maker')
    parse.add_argument('-f', '--folder', dest='folder', help='folder with images (*.jpg, *.jpeg, *.png)', default='.')
    parse.add_argument('-o', '--output', dest='output', help='output collage image filename', default='collage.png')
    parse.add_argument('-w', '--width', dest='width', type=int, help='resulting collage image width')
    parse.add_argument('-i', '--init_height', dest='init_height', type=int, help='initial height for resize the images')
    parse.add_argument('-s', '--shuffle', action='store_true', dest='shuffle', help='enable images shuffle')

    args = parse.parse_args()
    if not args.width or not args.init_height:
        parse.print_help()
        exit(1)

    # get images
    files = [os.path.join(args.folder, fn) for fn in os.listdir(args.folder)]
    images = [fn for fn in files if os.path.splitext(fn)[1].lower() in ('.jpg', '.jpeg', '.png')]
    if not images:
        print('No images for making collage! Please select other directory with images!')
        exit(1)

    # shuffle images if needed
    if args.shuffle:
        random.shuffle(images)

    print('Making collage...')
    res = make_collage(images, args.output, args.width, args.init_height)
    if not res:
        print('Failed to create collage!')
        exit(1)
    print('Collage is ready!')

def collage3():
    print("#collage3")
    #hstack to vstack
    list_im = ['flower1.jpg', 'flower2.jpg','flower3.jpg', 'Image3.jpg', 'Image2.jpg', 'Image4.jpg']

    imgs = [PIL.Image.open(i) for i in list_im]
    # pick the image which is the smallest, and resize the others to match it (can be arbitrary image shape here)
    min_shape = sorted([(np.sum(i.size), i.size) for i in imgs])[0][1]
    imgs_comb = np.hstack((np.asarray(i.resize(min_shape)) for i in imgs))

    # cols = 2
    # rows = 2
    # for col in range(cols):
    #     for row in range(rows):
    #         imgs_comb = np.hstack((np.asarray(i.resize(min_shape)) for i in imgs))

    # save that picture
    imgs_comb = PIL.Image.fromarray(imgs_comb)
    imgs_comb.save('Collage3V.jpg')

    # for a vertical stacking it is simple: use vstack
    imgs_comb = np.vstack((np.asarray(i.resize(min_shape)) for i in imgs))
    imgs_comb = PIL.Image.fromarray(imgs_comb)
    imgs_comb.save('Collage3.jpg')

def create_collage4(width, height, listofimages):
    #decide collage
    # columns = len(listofimages)/2
    # print(columns)
    # rowsn = columns
    cols = 2
    rows = 2
    thumbnail_width = width//cols
    thumbnail_height = height//rows
    size = thumbnail_width, thumbnail_height
    new_im = Image.new('RGB', (width, height))
    ims = []
    for p in listofimages:
        im = Image.open(p)
        im.thumbnail(size)
        ims.append(im)
    i = 0
    x = 0
    y = 0
    for col in range(cols):
        for row in range(rows):
            print(i, x, y)
            new_im.paste(ims[i], (x, y))
            i += 1
            y += thumbnail_height
        x += thumbnail_width
        y = 0

    new_im.save("Collage4.jpg")

#Call collage
list_im = ['flower1.jpg', 'flower2.jpg', 'flower3.jpg','flower4.jpg','flower5.jpg']
make_collage()
collage3()
create_collage4(450, 300, list_im)