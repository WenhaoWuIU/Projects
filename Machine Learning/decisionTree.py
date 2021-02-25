# This project is the implementation of decison tree for image classification with entropy and gini index 

import json
from multiprocessing import Pool
import numpy as np
import psutil
import time
import util


class DecisionTree():
    def __init__(
        self,
        max_levels=1000,
        min_leaf_size=10,
        impurity_measure="gini",
        output_filename=None,
        multiproc=True,
        verbose=False,
    ):
        self.max_levels = max_levels
        self.min_leaf_size = min_leaf_size if min_leaf_size > 1 else 1

        impurity_measure_dict = {
            "entropy" : self.entropy,
            "gini"    : self.gini,
        }
        self.impurity_fcn = impurity_measure_dict[impurity_measure]

        self.all_labels = (0, 90, 180, 270)
        self.output_filename = output_filename
        self.multiproc = multiproc
        self.verbose = verbose

        if multiproc:
            self.cpu_count = psutil.cpu_count(logical=False)
            print("Training using %d processes." % self.cpu_count)

    def count(self, values, unique_values):
        counts = np.zeros(len(unique_values))
        for i, u in enumerate(unique_values):
            counts[i] = np.count_nonzero(values == u)

        return counts

    def entropy(self, values, unique_values):
        if len(values) == 0:
            return 0

        freq_list = self.count(values=values, unique_values=unique_values) / len(values)
        freq_list[freq_list == 0] = 1  # Avoid NaN in np.log

        return -sum(freq_list * np.log2(freq_list))

    def gini(self, values, unique_values):
        if len(values) == 0:
            return 0

        freq_list = self.count(values=values, unique_values=unique_values) / len(values)

        return 1 - sum(freq_list ** 2)

    def compute_impurity(self, values_1, values_2, unique_values):
        impurity_1 = self.impurity_fcn(values=values_1, unique_values=unique_values)
        impurity_2 = self.impurity_fcn(values=values_2, unique_values=unique_values)
        n1, n2 = len(values_1), len(values_2)

        return (n1 * impurity_1 + n2 * impurity_2) / (n1 + n2)

    def calc_leaf_label(self, data):
        counts = self.count(values=data[:, -1], unique_values=self.all_labels)

        return np.argmax(counts) * 90

    def split_feature(self, feat_id):
        feature_vec = self._data[:, feat_id]

        if self.verbose and feat_id == 0:
            print("feat_id = %d, # of examples = %d" % (feat_id, len(feature_vec)))
        # print("feat_id = %d, # of examples = %d" % (feat_id, len(feature_vec)))

        best_impurity = 100000

        for thr in set(feature_vec):
            left = self._data[feature_vec <= thr, :]
            right = self._data[feature_vec > thr, :]

            impurity = self.compute_impurity(
                values_1=left[:, -1],
                values_2=right[:, -1],
                unique_values=self.all_labels,
            )

            if impurity < best_impurity:
                best_param = feat_id, thr
                best_impurity = impurity

        return best_impurity, best_param

    def split(self, node, data, level):
        def find_best_param(param_list):
            best_impurity = 1000000
            for impurity, param in param_list:
                if impurity < best_impurity:
                    best_impurity = impurity
                    best_param = param

            return best_param

        if level >= self.max_levels:
            node["label"] = self.calc_leaf_label(data)
            return

        if self.verbose:
            print("level = %d" % level)
        self._data = data

        if self.multiproc:
            with Pool(self.cpu_count) as p:
                param_list = p.map(self.split_feature, self.all_feat_ids)
        else:
            num_feat = data.shape[1] - 1
            param_list = [
                self.split_feature(feat_id=feat_id)
                for feat_id in range(num_feat)
            ]

        best_param = find_best_param(param_list=param_list)
        node["split_param"] = best_param

        feat_id, thr = best_param
        feature_vec = data[:, feat_id]
        left = data[feature_vec <= thr]
        right = data[feature_vec > thr]

        if len(left) < self.min_leaf_size or len(right) < self.min_leaf_size:
            node["label"] = self.calc_leaf_label(data)
            return

        node["left"] = {}
        node["right"] = {}

        self.split(
            node=node["left"],
            data=left,
            level=level + 1,
        )
        self.split(
            node=node["right"],
            data=right,
            level=level + 1,
        )

    def load_param(self, root):
        self.root = root

    def train(self, data):
        num_feat = data.shape[1] - 1
        self.all_feat_ids = list(range(num_feat))
        self.root = {}
        self.split(node=self.root, data=data, level=0)

    def predict_single(self, node, example):
        if "label" in node:
            return node["label"]

        feat_id, thr = node["split_param"]
        if example[feat_id] <= thr:
            return self.predict_single(node["left"], example)
        else:
            return self.predict_single(node["right"], example)

    def predict_bulk(self, data):
        predictions = []
        for row in data:
            predictions.append(self.predict_single(self.root, row))

        return predictions

    def predict(self, photo_ids, data):
        predictions = self.predict_bulk(data)
        accuracy = util.compute_test_accuracy(
            labels=data[:, -1], predictions=predictions,
        )

        if self.output_filename is not None:
            util.write_results_to_file(
                photo_ids=photo_ids,
                predictions=predictions,
                filepath=self.output_filename,
            )

        print("Accuracy on test set = %f" % accuracy)

        return predictions


def train_and_test_dt(
    dt, subsample_rate, train_filepath="train-data.txt", test_filepath="test-data.txt"
):
    print("Subsampling rate (train dataset) = %1.2f\n" % subsample_rate)

    start_time = time.time()

    _, data = util.read_dt_data(
        filepath=train_filepath, subsample_rate=subsample_rate,
    )
    print("Now training. It can take a little while :-)")
    dt.train(data=data)

    train_pred_labels = dt.predict_bulk(data=data)
    train_accuracy = util.compute_test_accuracy(
        labels=data[:, -1], predictions=train_pred_labels,
    )
    print()

    test_photo_ids, test_data = util.read_dt_data(filepath=test_filepath)
    pred_labels = dt.predict_bulk(data=test_data)
    test_accuracy = util.compute_test_accuracy(
        labels=test_data[:, -1], predictions=pred_labels,
    )
    # print(pred_labels)
    print("Train accuracy, test_accuracy = %1.4f, %1.4f" % (train_accuracy, test_accuracy))

    util.time_used(prefix="DT completed.", start_time=start_time)


def convert_leaf_to_str(root, str_root):
    if "label" in root:
        str_root["label"] = str(root["label"])
    else:
        feat_id, thr = root["split_param"]
        str_root["feat_id"] = str(feat_id)
        str_root["thr"] = str(thr)

        left = {}
        str_root["left"] = left
        convert_leaf_to_str(root["left"], left)

        right = {}
        str_root["right"] = right
        convert_leaf_to_str(root["right"], right)


def convert_leaf_to_float(root, float_root):
    if "label" in root:
        float_root["label"] = float(root["label"])
    else:
        split_param = int(root["feat_id"]), float(root["thr"])
        float_root["split_param"] = split_param

        left = {}
        float_root["left"] = left
        convert_leaf_to_float(root["left"], left)

        right = {}
        float_root["right"] = right
        convert_leaf_to_float(root["right"], right)


def save_to_json(root, filepath):
    new_root = {}
    convert_leaf_to_str(root, new_root)
    with open(filepath, 'w') as f:
        json.dump(new_root, f)


def read_json(filepath):
    with open(filepath, 'r') as f:
        root = json.load(f)
    new_root = {}
    convert_leaf_to_float(root, new_root)

    return new_root


def initialize_dt():
    return DecisionTree(
        max_levels=100,
        min_leaf_size=2,
        impurity_measure="gini",
        output_filename="output.txt",
        multiproc=True,
    )


def train_dt(train_filename, model_filename):
    start_time = time.time()

    dt = initialize_dt()

    subsample_rate = 0.4
    _, data = util.read_dt_data(
        filepath="train-data.txt",
        subsample_rate=subsample_rate,
    )
    print("subsample_rate = %1.4f" % subsample_rate)
    dt.train(data=data)
    save_to_json(root=dt.root, filepath=model_filename)

    util.time_used(start_time=start_time, prefix="DT training completed.")


def test_dt(test_filename, model_filename):
    root = read_json(filepath=model_filename)
    dt = initialize_dt()
    dt.load_param(root)

    test_photo_ids, test_data = util.read_dt_data(filepath=test_filename)
    pred_labels = dt.predict(data=test_data, photo_ids=test_photo_ids)
    test_accuracy = util.compute_test_accuracy(
        labels=test_data[:, -1], predictions=pred_labels,
    )