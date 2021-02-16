import csv
from collections import defaultdict

import importlib_resources

from gpsr_command_understanding.generator.xml_parsers import ObjectParser, LocationParser, NameParser, GesturesParser, \
    QuestionParser


class KnowledgeBase:
    def __init__(self, items, attributes):
        self.by_name = items
        self.attributes = attributes

    @staticmethod
    def from_dir(xml_path):
        raw_ontology_xml = list(map(lambda x: importlib_resources.open_text(xml_path, x),
                                     ["objects.xml", "locations.xml", "names.xml", "gestures.xml", "questions.xml", "whattosay.txt", "categories.txt"]))
        kb = KnowledgeBase.from_component_paths(*raw_ontology_xml)
        # Clean up IO to avoid warnings
        for stream in raw_ontology_xml:
            stream.close()
        return kb

    @staticmethod
    def from_component_paths(objects_xml_file, locations_xml_file, names_xml_file, gestures_xml_file,
                             questions_xml_file, sayings_file, categories_file):
        object_parser = ObjectParser(objects_xml_file)
        locations_parser = LocationParser(locations_xml_file)
        names_parser = NameParser(names_xml_file)
        gestures_parser = GesturesParser(gestures_xml_file)
        question_parser = QuestionParser(questions_xml_file)

        sayings = sayings_file.readlines()
        sayings = list(map(str.strip, sayings))

        # Drop the header
        categories_data = categories_file.readlines()[1:]
        categories_data  = list(map(tuple, csv.reader(categories_data)))
        categories_plural = list(map(lambda x: x[0], categories_data))

        objects = object_parser.all_objects()
        names = names_parser.all_names()
        locations = locations_parser.get_all_locations()
        gestures = list(gestures_parser.get_gestures())
        questions = list(question_parser.get_question_answer_dict().keys())
        attributes = {"object": object_parser.get_attributes(), "location": locations_parser.get_attributes(), "category": {}}

        attributes["object"]["category"] = object_parser.get_objects_to_categories()
        attributes["category"]["singular"] = {x[0]: x[1] for x in categories_data}
        attributes["location"]["in"] = locations_parser.get_room_locations_are_in()

        by_name = {
            "object": objects,
            "category": categories_plural,
            "name": names,
            "location": locations,
            "gesture": gestures,
            "question": questions,
            "whattosay": sayings
        }
        return KnowledgeBase(by_name, attributes)


class AnonymizedKnowledgebase:
    def __init__(self):
        names = [
            "object",
            "category",
            "name",
            "location",
            "gesture",
            "question",
            "whattosay"
        ]
        rooms = ["room" + str(i) for i in range(3)]
        self.by_name = {name: [name + str(i) for i in range(3)] for name in names}
        self.by_name["location"] += rooms
        self.attributes = {"object": {"type": defaultdict(lambda: "known"),
                                      "category": defaultdict(lambda: "category1")},
                           "location": {"isplacement": defaultdict(lambda: True),
                                        "isbeacon": defaultdict(lambda: True),
                                        "isroom": defaultdict(lambda: False),
                                        "in": defaultdict(lambda: "room1")},
                           "category": {"singular": {x: x for x in self.by_name["category"]}}}
        for room in rooms:
            self.attributes["location"]["isroom"][room] = True

        # Make sure the defaultdicts have concrete values set for all the known keys
        for object in self.by_name["object"]:
            self.attributes["object"]["type"][object]
            self.attributes["object"]["category"][object]
        for location in self.by_name["location"]:
            self.attributes["location"]["isplacement"][location]
            self.attributes["location"]["isbeacon"][location]
            self.attributes["location"]["in"][location]
