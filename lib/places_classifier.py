# PlacesCNN to predict the scene category, attribute, and class activation map in a single pass
# by Bolei Zhou, sep 2, 2017
# updated, making it compatible to pytorch 1.x in a hacky way
# updated, cleaned it up, class'ified it, self contained

import torch
from torch.autograd import Variable as V
import torchvision.models as models
from torchvision import transforms as trn
from torch.nn import functional as F
from typing import List
import os
import re
import numpy as np
import cv2
from PIL import Image

class PlacesClassifier():
    def __init__(self, models_directory):
        self.features_blobs = []
        self.classes = None
        self.labels_IO = None
        self.labels_attribute = None
        self.W_attribute = None
        self.models_directory = models_directory
        self.classes, self.labels_IO, self.labels_attribute, self.W_attribute = self.load_labels()
        self.model = self.load_model()
        self.tf = self.returnTF()

    def recursion_change_bn(self, module):
        if isinstance(module, torch.nn.BatchNorm2d):
            module.track_running_stats = 1
        else:
            for i, (name, module1) in enumerate(module._modules.items()):
                module1 = self.recursion_change_bn(module1)
        return module

    def load_labels(self):
        # prepare all the labels
        # scene category relevant
        file_name_category = self.models_directory + '/categories_places365.txt'
        if not os.access(file_name_category, os.W_OK):
            synset_url = 'https://raw.githubusercontent.com/csailvision/places365/master/categories_places365.txt'
            os.system('wget -P {} '.format(self.models_directory) + synset_url)
        classes = list()
        with open(file_name_category) as class_file:
            for line in class_file:
                classes.append(line.strip().split(' ')[0][3:])
        classes = tuple(classes)

        # indoor and outdoor relevant
        file_name_IO = self.models_directory + '/IO_places365.txt'
        if not os.access(file_name_IO, os.W_OK):
            synset_url = 'https://raw.githubusercontent.com/csailvision/places365/master/IO_places365.txt'
            os.system('wget -P {} '.format(self.models_directory) + synset_url)
        with open(file_name_IO) as f:
            lines = f.readlines()
            labels_IO = []
            for line in lines:
                items = line.rstrip().split()
                labels_IO.append(int(items[-1]) - 1)  # 0 is indoor, 1 is outdoor
        labels_IO = np.array(labels_IO)

        # scene attribute relevant
        file_name_attribute = self.models_directory + '/labels_sunattribute.txt'
        if not os.access(file_name_attribute, os.W_OK):
            synset_url = 'https://raw.githubusercontent.com/csailvision/places365/master/labels_sunattribute.txt'
            os.system('wget -P {} '.format(self.models_directory) + synset_url)
        with open(file_name_attribute) as f:
            lines = f.readlines()
            labels_attribute = [item.rstrip() for item in lines]
        file_name_W = self.models_directory + '/W_sceneattribute_wideresnet18.npy'
        if not os.access(file_name_W, os.W_OK):
            synset_url = 'http://places2.csail.mit.edu/models_places365/W_sceneattribute_wideresnet18.npy'
            os.system('wget -P {} '.format(self.models_directory) + synset_url)
        W_attribute = np.load(file_name_W)

        return classes, labels_IO, labels_attribute, W_attribute

    def hook_feature(self, module, input, output):
        self.features_blobs.append(np.squeeze(output.data.cpu().numpy()))

    def returnCAM(self, feature_conv, weight_softmax, class_idx):
        # generate the class activation maps upsample to 256x256
        size_upsample = (256, 256)
        nc, h, w = feature_conv.shape
        output_cam = []
        for idx in class_idx:
            cam = weight_softmax[class_idx].dot(feature_conv.reshape((nc, h * w)))
            cam = cam.reshape(h, w)
            cam = cam - np.min(cam)
            cam_img = cam / np.max(cam)
            cam_img = np.uint8(255 * cam_img)
            output_cam.append(cv2.resize(cam_img, size_upsample))
        return output_cam

    def returnTF(self):
        tf = trn.Compose([
            trn.Resize((224, 224)),
            trn.ToTensor(),
            trn.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        return tf

    def load_model(self):
        if not os.path.isdir(self.models_directory):
            os.mkdir(self.models_directory)

        model_file = 'wideresnet18_places365.pth.tar'
        if not os.access(self.models_directory + '/' + model_file, os.W_OK):
            os.system('wget -P {} http://places2.csail.mit.edu/models_places365/'
                      .format(self.models_directory) + model_file)
            os.system('wget -P {} https://raw.githubusercontent.com/csailvision/places365/master/wideresnet.py'
                      .format(self.models_directory))

        import models.wideresnet
        model = models.wideresnet.resnet18(num_classes=365)
        checkpoint = torch.load(self.models_directory + '/' + model_file,
                                map_location=lambda storage, loc: storage)
        state_dict = {str.replace(k, 'module.', ''): v for k, v in checkpoint['state_dict'].items()}
        model.load_state_dict(state_dict)

        # hacky way to deal with the upgraded batchnorm2D and avgpool layers...
        for i, (name, module) in enumerate(model._modules.items()):
            module = self.recursion_change_bn(model)
        model.avgpool = torch.nn.AvgPool2d(kernel_size=14, stride=1, padding=0)

        model.eval()

        model.eval()
        # hook the feature extractor
        features_names = ['layer4', 'avgpool']  # this is the last conv layer of the resnet
        for name in features_names:
            model._modules.get(name).register_forward_hook(self.hook_feature)
        return model

    def forward(self, img: Image) -> List[str]:
        attributes = ['clouds',
                      'biking',
                      'swimming',
                      'driving',
                      'sunny',
                      'leaves',
                      'snow',
                      'trees',
                      'climbing',
                      'hiking',
                      'rugged',
                      'ocean',
                      'scene']
        # load the model
        tokens = []

        # get the softmax weight
        params = list(self.model.parameters())
        weight_softmax = params[-2].data.numpy()
        weight_softmax[weight_softmax < 0] = 0

        input_img = V(self.tf(img).unsqueeze(0))

        # forward pass
        logit = self.model.forward(input_img)
        h_x = F.softmax(logit, 1).data.squeeze()
        probs, idx = h_x.sort(0, True)
        probs = probs.numpy()
        idx = idx.numpy()

        # output the IO prediction
        io_image = np.mean(self.labels_IO[idx[:10]])  # vote for the indoor or outdoor
        if io_image < 0.5:
            tokens.append('indoor')
        else:
            tokens.append('outdoor')

        # output the prediction of scene category
        for i in range(0, 5):
            if probs[i] > 0.25:
                tokens.append(self.classes[idx[i]])

        # output the scene attributes
        responses_attribute = self.W_attribute.dot(self.features_blobs[1])
        self.features_blobs = []
        idx_a = np.argsort(responses_attribute)
        for i in range(-1, -10, -1):
            t = self.labels_attribute[idx_a[i]]
            if t in attributes:
                tokens.append(self.labels_attribute[idx_a[i]])

        result = []
        for token in tokens:
            for t in re.split('[, /_-]+', token):
                result.append(t)
        return list(set(result))
