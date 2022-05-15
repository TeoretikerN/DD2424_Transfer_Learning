#import logging
import math

import numpy as np
from PIL import Image
from torchvision import datasets
from torchvision import transforms

from .randaugment import RandAugmentMC

#logger = logging.getLogger(__name__)

pets_mean = (0.4779, 0.4434, 0.3940)
pets_std = (0.2677, 0.2630, 0.2697)


def get_oxfordiiitpet(num_labeled, root):
    num_classes = 37

    #have not checked the transforms with the paper
    transform_labeled = transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.RandomCrop(size=32,
                              padding=int(32*0.125),
                              padding_mode='reflect'),
        transforms.ToTensor(),
        transforms.Normalize(mean=pets_mean, std=pets_std)
    ])
    transform_val = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=pets_mean, std=pets_std)
    ])

    #https://pytorch.org/vision/stable/generated/torchvision.datasets.OxfordIIITPet.html#torchvision.datasets.OxfordIIITPet
    base_dataset = datasets.OxfordIIITPet(root, target_types='category', download=True)

    train_labeled_idxs, train_unlabeled_idxs = x_u_split(
        num_labeled, num_classes, base_dataset.targets)

    train_labeled_dataset = OxfordIIITPetSSL(
        root, train_labeled_idxs, split='trainval',
        target_types='category', transform=transform_labeled)

    train_unlabeled_dataset = OxfordIIITPetSSL(
        root, train_unlabeled_idxs, split='trainval',
        target_types='category', transform=TransformFixMatch(mean=pets_mean, std=pets_std))

    test_dataset = datasets.OxfordIIITPet(
        root, split='trainval', target_types='category',
        transform=transform_val, download=False)

    return train_labeled_dataset, train_unlabeled_dataset, test_dataset

def x_u_split(num_labeled, num_classes, labels):
    label_per_class = num_labeled // num_classes #e.g. 10
    labels = np.array(labels)
    labeled_idx = []
    # unlabeled data: all data (https://github.com/kekmodel/FixMatch-pytorch/issues/10)
    unlabeled_idx = np.array(range(len(labels)))
    #randomly selects label_per_class imgs as labeled images
    for i in range(num_classes):
        idx = np.where(labels == i)[0] #1d array of idx where imgs have that label
        idx = np.random.choice(idx, label_per_class, False) #label_per_class rndm samples drawn from idx
        labeled_idx.extend(idx) #adds idx to labeled_idx
    labeled_idx = np.array(labeled_idx)
    assert len(labeled_idx) == num_labeled

    ###intended to expand labels to match eval steps, didnt fully understand
    #if args.expand_labels or args.num_labeled < args.batch_size:
    #    num_expand_x = math.ceil(
    #        args.batch_size * args.eval_step / args.num_labeled)
    #    labeled_idx = np.hstack([labeled_idx for _ in range(num_expand_x)])
    np.random.shuffle(labeled_idx)
    return labeled_idx, unlabeled_idx

class TransformFixMatch(object):
    def __init__(self, mean, std):
        self.weak = transforms.Compose([
            transforms.RandomHorizontalFlip(),
            transforms.RandomCrop(size=32,
                                  padding=int(32*0.125),
                                  padding_mode='reflect')])
        self.strong = transforms.Compose([
            transforms.RandomHorizontalFlip(),
            transforms.RandomCrop(size=32,
                                  padding=int(32*0.125),
                                  padding_mode='reflect'),
            RandAugmentMC(n=2, m=10)])
        self.normalize = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std)])

    def __call__(self, x):
        weak = self.weak(x)
        strong = self.strong(x)
        return self.normalize(weak), self.normalize(strong)

class OxfordIIITPetSSL(datasets.OxfordIIITPet):
    def __init__(self, root, indexs, split='trainval', target_types='category',
                 transform=None, target_transform=None,
                 download=False):
        super().__init__(root, split=split, 
                         target_types=target_types,
                         transform=transform,
                         target_transform=target_transform,
                         download=download)
        if indexs is not None:
            self.data = self.data[indexs]
            self.targets = np.array(self.targets)[indexs]

    def __getitem__(self, index):
        img, target = self.data[index], self.targets[index]
        img = Image.fromarray(img)

        if self.transform is not None:
            img = self.transform(img)

        if self.target_transform is not None:
            target = self.target_transform(target)

        return img, target

DATASET_GETTERS = {'oxfordiiipet': get_oxfordiiitpet}
