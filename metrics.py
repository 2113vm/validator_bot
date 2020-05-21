from abc import abstractmethod
from pathlib import Path

import pandas as pd
import numpy as np
from Levenshtein import distance


class Validator:
    def __init__(self):
        pass

    @abstractmethod
    def validate(self, filename):
        pass


class NotRotatedBB:
    def __init__(self, coords):
        x1, y1, x2, y2, x3, y3, x4, y4 = coords
        self.x_max = max(x1, x2, x3, x4)
        self.x_min = min(x1, x2, x3, x4)
        self.y_max = max(y1, y2, y3, y4)
        self.y_min = min(y1, y2, y3, y4)
        self.h = self.y_max - self.y_min
        self.w = self.x_max - self.x_min
        self.area = self.h * self.w

    def __sub__(self, other):
        """
        Intersection of two boxes
        :param other: NotRotatedBB
        :return: int.
        """
        x_inter = (self.w + other.w) - (max(self.x_max, other.x_max) - min(self.x_min, other.x_min))
        y_inter = (self.h + other.h) - (max(self.y_max, other.y_max) - min(self.y_min, other.y_min))

        if x_inter > 0 and y_inter > 0:
            return x_inter * y_inter
        else:
            return 0

    def __add__(self, other):
        """
        Union of two boxes
        :param other:
        :return:
        """
        return (self.area + other.area) - (self - other)


class TextBase:
    def __init__(self, dir_path):
        dir_path = Path(dir_path)
        self.matching = {}

        for path in dir_path.glob('*.txt'):
            with open(str(path), 'r') as file:
                lines = file.readlines()
            boxes = [NotRotatedBB(list(map(int, line.strip().split(',')[:8]))) for line in lines]
            self.matching[path.name] = boxes

    def find(self, current_key):
        base_keys = list(self.matching.keys())
        for base_key in base_keys:
            if current_key in base_key:
                return base_key
        return None

    def __getitem__(self, item):
        return self.matching[item]

    def __iter__(self):
        return iter(list(self.matching.keys()))


class TextDetectionValidator(Validator):
    def __init__(self, gt_dir):
        super().__init__()

        self.gt_base = TextBase(gt_dir)

    def validate(self, dir_path):
        alg_base = TextBase(dir_path)

        res = []
        for gt_key in self.gt_base:
            alg_key = alg_base.find(gt_key)
            if alg_key:
                res.append(self.validate_one_file(self.gt_base[gt_key], alg_base[alg_key]))
            else:
                res.append([0, 0, 0, 0, 0, 0])
        r = pd.DataFrame(res).mean()
        r.index = ['true_positive', 'precision', 'recall', 'f_measure', 'gt_num', 'alg_num']
        return r

    def validate_one_file(self, gt_boxes, alg_boxes):

        ious = np.zeros((len(gt_boxes), len(alg_boxes)))
        alg_num = len(alg_boxes)
        gt_num = len(gt_boxes)

        for gt_num, gt in enumerate(gt_boxes):
            for alg_num, alg in enumerate(alg_boxes):
                ious[gt_num, alg_num] = self._iou(gt, alg)

        true_positive = (ious > 0.5).astype(int).sum()
        precision = true_positive / len(alg_boxes)
        recall = true_positive / len(gt_boxes)
        f_measure = (2 * precision * recall) / (precision + recall)
        return true_positive, precision, recall, f_measure, gt_num, alg_num

    @staticmethod
    def _iou(box1: NotRotatedBB, box2: NotRotatedBB):
        return (box1 - box2) / (box1 + box2)


class OCRValidator(Validator):
    def __init__(self, gt_file):
        super().__init__()

        self.base = self._read_csv(gt_file)

    def validate(self, filename):
        alg_base = self._read_csv(filename)

        res = pd.merge(self.base, alg_base, on=['path'])
        res['is_equil'] = res.label_x == res.label_y
        acc = res.is_equil.mean()
        res['leven'] = res.apply(lambda row: distance(row['label_x'], row['label_y']), axis=1)
        lev = res.leven.mean()
        return {'acc': acc, 'lev': lev}

    @staticmethod
    def _read_csv(filename):

        with open(filename) as f:
            lines = f.readlines()

        base = []
        for line in lines:
            img_path, *labels = line.split(' ')
            labels = ' '.join(labels)
            base.append([img_path, labels.lower().strip()])
        return pd.DataFrame(data=base, columns=['path', 'label'])
