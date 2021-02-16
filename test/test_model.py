import os

from allennlp.common.testing import ModelTestCase
# We need to register components with AllenNLP
from gpsr_command_understanding.models import seq2seq

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestModel(ModelTestCase):
    def setup(self):
        super().setup_method()
        self.set_up_model(os.path.join(FIXTURE_DIR, 'seq2seq.json'),
                          os.path.join(FIXTURE_DIR, 'train.txt'))

    def test_model_can_train_save_and_load(self):
        self.ensure_model_can_train_save_and_load(self.param_file)
