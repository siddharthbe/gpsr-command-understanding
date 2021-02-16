# coding: utf-8
import os
import unittest

import lark
from lark import Lark

from gpsr_command_understanding.generator.generator import GENERATOR_GRAMMARS
from gpsr_command_understanding.generator.grammar import expand_shorthand, TypeConverter
from gpsr_command_understanding.util import ParseForward

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class TestGenerator(unittest.TestCase):

    def setUp(self):
        self.__grammar_parser = Lark(GENERATOR_GRAMMARS[2018],
                                     start=['rule_start', 'expression_start'], parser="lalr",
                                     transformer=TypeConverter())
        self.rule_parser = ParseForward(self.__grammar_parser, "rule_start")
        self.sequence_parser = ParseForward(self.__grammar_parser, "expression_start")

    def test_ignore_comment(self):
        comments = ["", "# this is a comment", "; this is a comment", "// this is a comment",
                    '; grammar name Category I', "# test"]
        for comment in comments:
            test = self.rule_parser.parse(comment)
            self.assertEqual([], test.children)
        test = self.rule_parser.parse("// Ignore this\n $test = But not this")
        self.assertNotEqual([], test.children)

    def test_parse_rule(self):
        test = self.rule_parser.parse("$test = {pron} went to the mall and {location} $go $home")
        # TODO: Actually check this
        print(test.pretty())

    def test_parse_wildcard_shorthand(self):
        # Check the shorthand wildcards look the same as the full form
        self.assertEqual(self.sequence_parser.parse("{location room}"),
                         self.sequence_parser.parse("{room}"))
        self.assertEqual(self.sequence_parser.parse("{location beacon}"),
                         self.sequence_parser.parse("{beacon}"))
        self.assertEqual(self.sequence_parser.parse("{kobject}"),
                         self.sequence_parser.parse("{object known}"))
        self.assertEqual(self.sequence_parser.parse("{sobject}"),
                         self.sequence_parser.parse("{object special}"))

        # Make sure obfuscation and metadata operators work

    def test_parse_wildcard_ids(self):
        self.assertEqual(self.sequence_parser.parse("{object 1}").children[0].id, 1)
        self.assertEqual(self.sequence_parser.parse("{aobject 1}").children[0].id, 1)
        self.assertEqual(self.sequence_parser.parse("{location 2}").children[0].id, 2)
        self.assertEqual(self.sequence_parser.parse("{name 3}").children[0].id, 3)
        self.assertEqual(self.sequence_parser.parse("{category? 3}").children[0].id, 3)
        self.assertEqual(self.sequence_parser.parse("{category?}").children[0].id, None)

    def test_parse_wildcard_obfuscation(self):
        # Shouldn't be able to obfuscate some types of wildcard
        self.assertRaises(lark.exceptions.UnexpectedToken, self.sequence_parser.parse, "{name?}")
        self.assertRaises(lark.exceptions.UnexpectedToken, self.sequence_parser.parse, "{question?}")

        def is_obf(wildcard, type=None, id=None):
            return wildcard.obfuscated and wildcard.type is type and wildcard.id is id

        object_obf = self.sequence_parser.parse("{object?}").children[0]
        self.assertEqual(is_obf(object_obf), True)
        aobject_obf = self.sequence_parser.parse("{aobject?}").children[0]
        self.assertEqual(is_obf(aobject_obf, "alike"), True)
        self.assertEqual(self.sequence_parser.parse("{aobject? 1 meta: test}").children[0].obfuscated, True)
        location_obf = self.sequence_parser.parse("{location?}").children[0]
        self.assertEqual(is_obf(location_obf), True)
        self.assertEqual(self.sequence_parser.parse("{category?}").children[0].obfuscated, True)
        self.assertEqual(self.sequence_parser.parse("{category}").children[0].obfuscated, False)

    def test_parse_wildcard_meta(self):
        parsed_name = self.sequence_parser.parse("{name 1 meta: test}").children[0]
        self.assertEqual(parsed_name.metadata, ["test"])

        # Check meta choice
        meta_choice = '{name meta: {pron sub} is (sitting | standing | lying | waving ) at the {beacon}}'
        parsed = self.sequence_parser.parse(meta_choice).children[0]
        self.assertFalse(parsed.obfuscated)
        self.assertEqual(parsed.name, "name")
        self.assertEqual(len(parsed.metadata), 6)

    def test_parse_willdcard_integration(self):
        test = self.sequence_parser.parse(
            "Go to the {location placement 1} and get the {kobject}. "
            "Then give it to {name 1} who is next to {name 2} at the {location beacon 1} in the {location room}")
        print(test.pretty())

    def test_parse_wildcard_condition(self):
        test = self.sequence_parser.parse("{object where Category=\"test\"}").children[0]
        self.assertEqual(1, len(test.conditions))
        self.assertEqual("test", test.conditions["category"])
        test = self.sequence_parser.parse("{object where category=\"test\" and canPour=\"true\"}").children[0]
        self.assertEqual(len(test.conditions), 2)
        self.assertEqual("test", test.conditions["category"])
        self.assertEqual("true", test.conditions["canpour"])

        # Check boolean conditions

        test = self.sequence_parser.parse("{object where canPourIn=true}").children[0]
        self.assertEqual(1, len(test.conditions))
        self.assertEqual(True, test.conditions["canpourin"])

    def test_parse_pronouns(self):
        pronoun_types = ["pron", "pron obj", "pron sub", "pron pos", "pron paj", "pron posabs", "pron posadj"]
        for type in pronoun_types:
            test = self.sequence_parser.parse(
                "{" + type + "}").children[0]
            self.assertIsNotNone(test)

        # Check shorthands
        pairs = [("pron", "pron obj"), ("pron pos", "pron paj"), ("pron pos", "pron posadj"),
                 ("pron pab", "pron posabs")]
        for first, second in pairs:
            first_wildcard = self.sequence_parser.parse(
                "{" + first + "}").children[0]
            second_wildcard = self.sequence_parser.parse("{" + second + "}").children[0]
            self.assertEqual(first_wildcard, second_wildcard)

    def test_expand_shorthand(self):
        test = self.rule_parser.parse("$test    = top choice | (level one (level two alpha | level two beta))")
        result = expand_shorthand(test)
        self.assertEqual(len(result), 3)

    def test_parse_choice(self):
        test = self.sequence_parser.parse("( oneword | two words)")
        self.assertEqual(len(test.children[0].children), 2)
        test = self.sequence_parser.parse("( front | back | main | rear ) $ndoor")
        self.assertEqual(len(test.children[0].children), 4)

        top_choice = self.sequence_parser.parse("front | back")
        top_choice_short = self.sequence_parser.parse("(front | back)")
        self.assertEqual(top_choice, top_choice_short)

        short_mix_choice = self.sequence_parser.parse("aa | aa ba")
        self.assertEqual(len(short_mix_choice.children), 1)
        self.assertEqual(len(short_mix_choice.children[0].children), 2)

        complex_choice = self.sequence_parser.parse(
            "everyone | all the (people | men | women | guests | elders | children)")
        self.assertEqual(len(complex_choice.children), 1)
        self.assertEqual(len(complex_choice.children[0].children), 2)

    def test_parse_void(self):
        test_rule = '{void meta: The Professional Walker must leave the arena and walk through ' \
                    'a crowd of at least 5 people, say "$whattosay", find a t-shirt, ' \
                    'the Professional Walker must lead the robot to {room 2} }'
        test = self.sequence_parser.parse(test_rule)
        self.assertEqual(len(test.children), 1)
        self.assertEqual(len(test.children[0].metadata), 36)
