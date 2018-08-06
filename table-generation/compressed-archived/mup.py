#! /usr/bin/python

from __future__ import print_function
import MarkupPy.markup as mp
import webbrowser as web
import os
import time
from wand.image import Image
from PIL import Image as Img
import numpy as np
import pdfkit
# from weasyprint import HTML
import weasyprint
import tinycss
import uuid
import glob
import sys
import mxnet as mx
import cv2
import csv
import random
from random import sample
import itertools
import nltk
import numpy as np
from nltk import word_tokenize, pos_tag, ne_chunk
from nltk.chunk import conlltags2tree, tree2conlltags
from nltk.tag import StanfordNERTagger
import tarfile
import io

parameters = {}

def extract_tar(tarfilename):
    # if not os.path.exists('./html'):
    #    os.makedirs('./html')
    # tar = tarfile.open(os.path.join('./html', tarfilename), "r:gz")
    # tar.extractall('./html')
    # tar.close()
    for filename in os.listdir("./html/html/"):
        print(filename)
        table_to_pdf(filename[:-5])
        # pdf_to_png(filename[:-5])
        # pdf_to_jpg('./pdf/' + filename[:-5] + '.pdf', filename[:-5])


def table_to_pdf(name):
    """
    Converts an HTML table to a PDF file
    :param name file name
    """
    pdfkit.from_file('./html/html/' + name + '.html', './pdf/' + name + ".pdf")
    # weasyprint.HTML('./html/html/' + name + '.html').write_pdf('./pdf/' + name + ".pdf")


def pdf_to_png(name):
    """
    Converts the PDF of a table to a PNG image
    :param name file name
    """
    size = 7016, 4961
    with Image(filename='./pdf/' + name + '.pdf') as img:
        with img.convert('png') as converted:
            converted.save(filename='./png/' + name+ '.png')


def pdf_to_jpg(filepdf, name):
    """
    Converts the PDF of a table to a JPG image
    :param filepdf the PDF file
    :param name file name
    :return the bounding box of the table in the JPG
    """
    uuids = str(uuid.uuid4().fields[-1])[:5]
    with Image(filename=filepdf, resolution=500) as img:
        img.compression_quality = 80
        img.save(filename='TMP/temp_' + name + '_%s.jpg' % uuids)
        list_im = glob.glob('TMP/temp_' + name + '_%s.jpg' % uuids)
        list_im.sort()
        imgs = [Img.open(i) for i in list_im]
        min_shape = sorted([(np.sum(i.size), i.size) for i in imgs])[0][1] #combine images
        imgs_c = np.vstack((np.asarray(i.resize(min_shape)) for i in imgs)) #vertical
        imgs_c = Img.fromarray(imgs_c)
        path = './jpg/' + name + '_%s.jpg' % uuids
        imgs_c.save(path)
        bounding_box(path)
        for i in list_im:
            os.remove(i)
    return bounding_box(path)


def bounding_box(image_file):
    """
    Detects the bounding box of a table in an image using Open CV
    and reports its coordinates
    :param image_file the image to be analysed
    """
    im = cv2.imread(image_file)
    im[im == 255] = 1
    im[im == 0] = 255
    im[im == 1] = 0
    im2 = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    ret,thresh = cv2.threshold(im2,127,255,0)
    im2, contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    cnt = contours[0]
    x,y,w,h = cv2.boundingRect(cnt) #The function calculates and returns the minimal up-right bounding rectangle for the specified point set.
    x1 = x + (w-1)
    y1 = y + (h-1)

    out = [x, y, x1, y1]
    print(out)

    rect = cv2.minAreaRect(cnt)
    box = cv2.boxPoints(rect)

    return out


def write_to_csv(data_arr):
    """
    Writes the bounding box data to a CSV file
    :param data_arr the data to be written to a CSV
    """
    f = open('bounding_boxes.csv','w')
    for i in range(len(data_arr)):
        temp = data_arr[i]
        for j in range(3):
            f.write(str(temp[j]) + ', ')
        f.write(str(temp[3]) + '\n')
    f.close()


def read_words(words_file):
    """
    Reads a text file and puts its words into a list
    :param words_file text file to be read
    :return list of words read from a file
    """
    return [word for line in open(words_file, 'r') for word in line.split()]


def grouped(list_of_words, n):
    """
    Groups elements of a list
    :param list_of_words the list to be grouped
    :param n size of the group
    :return groups
    """
    return zip((*[iter(list_of_words)]*n))


def load_char_distr(): 
    """
    Loads the csv files and builds a nested dictionary to represent the character distribution
    """
    map_of_probs = {}
    counter = 1
    with open('./hyperparams.csv') as f:
        for line_keys, line_values in itertools.zip_longest(*[f]*2):
            if counter < 15:
                counter = counter + 1
                continue
            k_row = line_keys.split(',')
            v_row = line_values.split(',')
            main_key = k_row[0]
            parameters[main_key] = {}
            k_row.remove(k_row[0])
            v_row.remove(v_row[0])
            for key, value in zip(k_row, v_row):
                if (len(key) <= 0 or key == '\n'):
                    continue
                parameters[main_key][key] = value
            counter = counter + 1


def load_header_images(image_folder): # "./logo-images"
    """
    Loads header images
    :param image_folder the location of logos
    :return list of images
    """
    list_of_images = []
    for filename in os.listdir(image_folder):
        list_of_images.append('../../' + str(image_folder) + str(filename))
    return list_of_images


def char_distr(text):
    """
    Builds a list of words, numbers and symbols according to the distribution requested
    :param text the text to be modified
    :return list of words
    """
    nums = []
    symbols = "! @ # $ % ^ & * ( ) _ - + = { } [ ]"
    symb = symbols.split()
    sent = text.split()
    total_num = len(sent)
    for key in parameters['character distribution']:   # {'character distributions': {'words': '0.5', 'numbers': '0.4', 'symbols': '0.1'}}
        nums.append(float(parameters['character distribution'][key]) * total_num)
    final_text = []
    wc = 0
    nc = 0
    sc = 0
    for el in sent:
        if el.isnumeric() and nc < nums[1]:#1:#nums[1]:
            final_text.append(el)
            nc += 1
        if any(s in el for s in symb) and sc < nums[2]:#2:#nums[2]:
            final_text.append(el)
            sc += 1
        elif wc < nums[0]:#2:#nums[0]:
            final_text.append(el)
            wc += 1
    return random.sample(final_text, len(final_text))


def generate_html():
    """
    Generates the HTML and calls further methods
    """
    tar = tarfile.open('./css/css.tar.gz', "r:gz")
    tar.extractall()
    tar.close()
    
    bounding_boxes_ = []
    load_char_distr()
    all_words = read_words('../../pdf-parser/text_for_tables.txt')
    list_of_images = load_header_images('../logo-images/')
    counter = 0

    html_folder = './html'
    if not os.path.exists(html_folder):
       os.makedirs(html_folder)

    html_tar = tarfile.open(os.path.join(html_folder, "html.tar.gz"), "w:gz")
    for x in sorted(os.listdir("/Users/mensikov/Desktop/Chevron/GITHUB_REPO/T-ENTacle/table-generation/compressed-archived/css/css")):
        page = mp.page()
        page.init(title="HTML Generator",
                  css=('/Users/mensikov/Desktop/Chevron/GITHUB_REPO/T-ENTacle/table-generation/compressed-archived/css/css/' + str(x)))

        page.img(width=100, height=70, src=random.choice(list_of_images))

        extra_text_before = " ".join(random.sample(all_words, random.randint(300, 1000)))
        extra_text_after = " ".join(random.sample(all_words, random.randint(500, 3000)))

        page.p(extra_text_before)

        page.table()

        r = random.randint(5, 30)
        c = random.randint(3, 10)

        for i in range(r): #rows
            for j in range(c): #columns
                num = random.randint(5, 300)
                temp = ''
                for r in range(num):
                    temp += random.choice(all_words) + ' '
        list_of_words = char_distr(temp)

        for i in range(r): #rows
            page.tr()
            for j in range(c): #columns
                num = random.randint(3, 21)
                temp_text = ''
                temp_list = []
                for r in range(num):
                    word = random.choice(list_of_words)
                    temp_text += word + ' '
                    temp_list.append(word)
                chosen = random.sample(temp_list, random.randint(3, len(temp_list)))
                no_p_text = ''
                p_text = '<p>'
                for w in temp_list:
                    if w in chosen:
                        no_p_text += w + ' '
                    else:
                        p_text += w + ' '
                p_text += '</p>'
                page.td(p_text + ' ' + no_p_text)
                page.td.close()
            page.tr.close()
        page.table.close()

        page.p(extra_text_after)

        html_content = str(page)

        filename = os.path.splitext(x)[0]
        html_bytes = io.BytesIO(html_content.encode('utf8'))
        html_info = tarfile.TarInfo(name= "html/" + filename + ".html")
        html_info.size=len(html_content)
        html_tar.addfile(tarinfo = html_info, fileobj = html_bytes)


        #bounding_boxes_.append(pdf_to_jpg('./PDF/' + file_ + '.pdf', file_))

    #write_to_csv(bounding_boxes_)
    html_tar.close()
    extract_tar(html_tar)


# generate_html()
extract_tar("html.tar.gz")