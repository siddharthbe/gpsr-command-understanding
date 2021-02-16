# GPSR Command Understanding ![Build Status](https://github.com/nickswalker/gpsr-command-understanding/workflows/CI/badge.svg)

A semantic parser for commands from the [RoboCup@Home](http://www.robocupathome.org/) _General Purpose Service Robot_ task. 

* [X] Utterance to λ-calculus representation parser
* [X] Lexer/parser for loading the released command generation CFG
* [X] Tools for generating commands along with a λ-calculus representation
* [X] Crowd-sourcing interface for collecting paraphrases

If you use this code or data, consider citing our paper [Neural Semantic Parsing for Command Understanding in General-Purpose Service Robots](https://arxiv.org/abs/1907.01115). The data collected for this paper is [available separately](https://github.com/nickswalker/gpsr-commands-dataset).

## Usage

Set up a virtual environment using at least Python 3.6:

    python3.7 -m virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt

### Generation

The latest grammar and knowledgebase files (pulled from [the generator](https://github.com/kyordhel/GPSRCmdGen)) are provided in the resources directory. The grammar [format specification](https://github.com/kyordhel/GPSRCmdGen/wiki/Grammar-Format-Specification) will clarify how to interpret the files.

To produce the dataset, see `data/make_dataset.py`.

### Training

We base our training on [previous work](https://github.com/jbkjr/allennlp_sempar) using [AllenNLP](https://allennlp.org) for seq2seq semantic parser training. All of our experiments are
declaratively specified  in the `experiments` directory.

You can run them with

    allennlp train \
    experiments/seq2seq.json \
    -s results/seq2seq \
    --include-package gpsr_command_understanding

You can monitor training with Tensorboard, just point it at the log directory.
    
The `train_all_models` script will train every config back to back.

    ./scripts/train_all_models gen_demo experiments -t data/gen/train.txt -v data/gen/val.txt

### Testing

To see a model's output on a data file, use the `predict command`

    allennlp predict --archive-path results/ --include-package gpsr_command_understanding

You can poke at a trained model through the browser using AllenNLP as well

    python -m gpsr_command_understanding.demo.logging_server \
        --archive-path results/seq2seq/model.tar.gz \
        --predictor  command_parser\
        --include-package gpsr_command_understanding