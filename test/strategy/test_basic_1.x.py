"""Tests for quantization."""
import os
import shutil
import unittest

import numpy as np
import yaml


def build_fake_yaml():
    fake_yaml = """
        model:
          name: fake_yaml
          framework: tensorflow
          inputs: x
          outputs: op2_to_store
        device: cpu
        evaluation:
          accuracy:
            metric:
              topk: 1
        tuning:
            strategy:
              name: basic
            accuracy_criterion:
              relative: 0.01
            workspace:
              path: saved
        """
    y = yaml.load(fake_yaml, Loader=yaml.SafeLoader)
    with open("fake_yaml.yaml", "w", encoding="utf-8") as f:
        yaml.dump(y, f)
    f.close()


def build_fake_yaml_recipe():
    fake_yaml = """
        model:
          name: fake_yaml
          framework: tensorflow
          inputs: x
          outputs: op2_to_store
        device: cpu
        evaluation:
          accuracy:
            metric:
              topk: 1
        quantization:
            approach:
                post_training_auto_quant
        tuning:
          strategy:
            name: basic
          exit_policy:
            max_trials: 10
          accuracy_criterion:
            absolute: -1
          workspace:
            path: saved
        """
    y = yaml.load(fake_yaml, Loader=yaml.SafeLoader)
    with open("fake_yaml_recipe.yaml", "w", encoding="utf-8") as f:
        yaml.dump(y, f)
    f.close()


def build_fake_yaml2():
    fake_yaml = """
        model:
          name: fake_yaml
          framework: tensorflow
          inputs: x
          outputs: op2_to_store
        device: cpu
        evaluation:
          accuracy:
            metric:
              topk: 1
        tuning:
          strategy:
            name: basic
          exit_policy:
            max_trials: 3
          accuracy_criterion:
            relative: -0.01
          workspace:
            path: saved
        """
    y = yaml.load(fake_yaml, Loader=yaml.SafeLoader)
    with open("fake_yaml2.yaml", "w", encoding="utf-8") as f:
        yaml.dump(y, f)
    f.close()


def build_fake_yaml3():
    fake_yaml = """
        model:
          name: fake_yaml
          framework: tensorflow
          inputs: x
          outputs: op2_to_store
        device: cpu
        evaluation:
          accuracy:
            multi_metrics:
              topk: 1
              MSE:
                compare_label: False
        tuning:
          strategy:
            name: basic
          exit_policy:
            max_trials: 3
            timeout: 50
          accuracy_criterion:
            relative: -0.01
          workspace:
            path: saved
        """
    y = yaml.load(fake_yaml, Loader=yaml.SafeLoader)
    with open("fake_yaml3.yaml", "w", encoding="utf-8") as f:
        yaml.dump(y, f)
    f.close()


def build_fake_yaml4():
    fake_yaml = """
        model:
          name: fake_yaml
          framework: tensorflow
          inputs: x
          outputs: op2_to_store
        device: cpu
        evaluation:
          accuracy:
            multi_metrics:
              topk: 1
              MSE:
                compare_label: False
              weight: [1, 0]
        tuning:
          strategy:
            name: basic
          exit_policy:
            max_trials: 3
            timeout: 50
          accuracy_criterion:
            relative: -0.01
          workspace:
            path: saved
        """
    y = yaml.load(fake_yaml, Loader=yaml.SafeLoader)
    with open("fake_yaml4.yaml", "w", encoding="utf-8") as f:
        yaml.dump(y, f)
    f.close()


def build_fake_model():
    import tensorflow as tf

    try:
        graph = tf.Graph()
        graph_def = tf.compat.v1.GraphDef()
        with tf.compat.v1.Session() as sess:
            x = tf.compat.v1.placeholder(tf.float32, shape=(1, 3, 3, 1), name="x")
            y = tf.constant(np.random.random((2, 2, 1, 1)).astype(np.float32), name="y")
            z = tf.constant(np.random.random((1, 1, 1, 1)).astype(np.float32), name="z")
            op = tf.nn.conv2d(input=x, filters=y, strides=[1, 1, 1, 1], padding="VALID", name="op_to_store")
            op2 = tf.nn.conv2d(
                input=op,
                filters=z,
                strides=[1, 1, 1, 1],
                padding="VALID",
            )
            last_identity = tf.identity(op2, name="op2_to_store")
            sess.run(tf.compat.v1.global_variables_initializer())
            constant_graph = tf.compat.v1.graph_util.convert_variables_to_constants(
                sess, sess.graph_def, ["op2_to_store"]
            )

        graph_def.ParseFromString(constant_graph.SerializeToString())
        with graph.as_default():
            tf.import_graph_def(graph_def, name="")
    except:
        graph = tf.Graph()
        graph_def = tf.compat.v1.GraphDef()
        with tf.compat.v1.Session() as sess:
            x = tf.compat.v1.placeholder(tf.float32, shape=(1, 3, 3, 1), name="x")
            y = tf.constant(np.random.random((2, 2, 1, 1)).astype(np.float32), name="y")
            z = tf.constant(np.random.random((1, 1, 1, 1)).astype(np.float32), name="z")
            op = tf.nn.conv2d(input=x, filters=y, strides=[1, 1, 1, 1], padding="VALID", name="op_to_store")
            op2 = tf.nn.conv2d(input=op, filters=z, strides=[1, 1, 1, 1], padding="VALID")
            last_identity = tf.identity(op2, name="op2_to_store")

            sess.run(tf.compat.v1.global_variables_initializer())
            constant_graph = tf.compat.v1.graph_util.convert_variables_to_constants(
                sess, sess.graph_def, ["op2_to_store"]
            )

        graph_def.ParseFromString(constant_graph.SerializeToString())
        with graph.as_default():
            tf.import_graph_def(graph_def, name="")
    return graph


class TestBasicTuningStrategy(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.constant_graph = build_fake_model()
        build_fake_yaml()
        build_fake_yaml2()
        build_fake_yaml3()
        build_fake_yaml4()
        build_fake_yaml_recipe()

    @classmethod
    def tearDownClass(self):
        os.remove("fake_yaml.yaml")
        os.remove("fake_yaml2.yaml")
        os.remove("fake_yaml3.yaml")
        os.remove("fake_yaml4.yaml")
        os.remove("fake_yaml_recipe.yaml")
        shutil.rmtree("saved", ignore_errors=True)

    def test_run_basic_one_trial(self):
        from neural_compressor.experimental import Quantization, common

        quantizer = Quantization("fake_yaml.yaml")
        dataset = quantizer.dataset("dummy", (100, 3, 3, 1), label=True)
        quantizer.calib_dataloader = common.DataLoader(dataset)
        quantizer.eval_dataloader = common.DataLoader(dataset)
        quantizer.model = self.constant_graph
        quantizer.fit()

        # resume tuning history
        quantizer.conf.usr_cfg.tuning.workspace.resume = "saved/history.snapshot"
        quantizer.fit()

    def test_run_basic_max_trials(self):
        from neural_compressor.experimental import Quantization, common

        quantizer = Quantization("fake_yaml2.yaml")
        dataset = quantizer.dataset("dummy", (100, 3, 3, 1), label=True)
        quantizer.calib_dataloader = common.DataLoader(dataset)
        quantizer.eval_dataloader = common.DataLoader(dataset)
        quantizer.model = self.constant_graph
        quantizer.fit()

    def test_run_basic_recipe(self):
        from neural_compressor.experimental import Quantization, common

        quantizer = Quantization("fake_yaml_recipe.yaml")
        dataset = quantizer.dataset("dummy", (100, 3, 3, 1), label=True)
        quantizer.calib_dataloader = common.DataLoader(dataset)
        quantizer.eval_dataloader = common.DataLoader(dataset)
        quantizer.model = self.constant_graph
        quantizer.fit()

    def test_run_basic_max_trials_multimetric(self):
        from neural_compressor.experimental import Quantization, common

        quantizer = Quantization("fake_yaml3.yaml")
        dataset = quantizer.dataset("dummy", (100, 3, 3, 1), label=True)
        quantizer.calib_dataloader = common.DataLoader(dataset)
        quantizer.eval_dataloader = common.DataLoader(dataset)
        quantizer.model = self.constant_graph
        quantizer.fit()

    def test_run_basic_max_trials_multimetric_weight(self):
        from neural_compressor.experimental import Quantization, common

        quantizer = Quantization("fake_yaml4.yaml")
        dataset = quantizer.dataset("dummy", (100, 3, 3, 1), label=True)
        quantizer.calib_dataloader = common.DataLoader(dataset)
        quantizer.eval_dataloader = common.DataLoader(dataset)
        quantizer.model = self.constant_graph
        quantizer.fit()


if __name__ == "__main__":
    unittest.main()
