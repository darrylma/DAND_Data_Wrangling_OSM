# load libraries
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import csv
import codecs
import cerberus
import schema
import os

# define file to be used throughout analayis
filename = "kuala-lumpur_malaysia_sample.osm"

# regular expressions
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
street_type_re = re.compile(r'^\b\S+\.?', re.IGNORECASE)

# expected streetnames
expected = ["Jalan", "Lorong", "Persiaran", "Lebuhraya", "Perindustrian",
            "Kampung", "Lebuh", "Changkat", "Tengkat", "Lengkok", 
            "Lingkaran", "Pintasan", "Taman", "Apartment", "Desa", "Batu"]

# mapping to correct abbreviations and mispellings
mapping = { "jalan": "Jalan",
            "Leboh": "Lebuh",
            "Jln": "Jalan",
            "Kg.": "Kampung",
            "Kg" : "Kampung",
            "apartment" : "Apartment",
            "Bt" : "Batu"
          }

# to add streetname to these entries
missing_streetname = ["SS", "PJ"]

# output csv filenames
NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

# declaring schema and field names in schema
SCHEMA = schema.schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

# corrects street name's abbreviations, mispellings and format 
def update_streetname(name, mapping):

    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            if street_type in mapping:
                name = name.replace(street_type, mapping[street_type])
            elif any(e in name for e in expected):
                for e in expected:
                    if e in name:
                        position = name.index(e)
                        name = name[position:]
            elif name[:2] in missing_streetname or (name == "P14G1" or name == '5/109F'):
                name = "Jalan " + name
            elif name == '19 Persiran KLCC':
                name = "Persiaran KLCC"
        else:
            name = name
    return name

# corrects zipcode to adhere to 5 character length 
def update_zipcode(zipcode):
    
    correct_zipcode = zipcode
    if zipcode =='462000':
        correct_zipcode = '46200'
    elif zipcode =='5400':
        correct_zipcode = '54000'
    elif zipcode =='56000 ':
        correct_zipcode = '56000'
    elif zipcode =='6800':
        correct_zipcode = '68000'
    return correct_zipcode

# corrects phone number format to adhere to following format: +60xxxxxxxxx
def update_phonenumber(number):
    
    # remove all '(', ')', ' ' and '-' 
    number = number.replace('(','').replace(')','').replace(' ','').replace('-','')
    
    # remove all preceding 0's
    i = 0
    while number[i] == '0':
        number = number[i+1:]
    
    # append '+60' if neccessary
    if number[0] != '+':
        number = '+' + number[:]
    if number[1] != '6':
        number = number[0] + '6' + number[1:]
    if number[2] != '0':
        number = number[:2] + '0' + number[2:]
    if number[3] == '0':
        number = number[:3] + number[4:]
    
    # keep only first phone number if multiple phone numbers are provided
    if any(char in number for char in [';','/',',']):
        number_list = number.replace(';',',').replace('/',',').split(',')
        number = number_list[0]
    return number

# to update incorrect street names, zipcodes and phone numbers
def update_value(value, tag_type):
    
    if tag_type == "addr:street":
        value = update_streetname(value, mapping)
    elif tag_type == "addr:postcode":
        value = update_zipcode(value)
    elif tag_type == "contact:phone" or tag_type == "phone":
        value = update_phonenumber(value)
    return value
    
def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=problemchars, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    node_tag_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    if element.tag == 'node':
        # to handle node attributes
        for node_field in node_attr_fields:
            node_attribs[node_field] = element.get(node_field)
        
        # to handle node tag attributes
        for tag in element.iter('tag'):
            if not(problem_chars.search(tag.get("k"))):
                node_tag_attribs = {}
                for node_tag_field in NODE_TAGS_FIELDS:
                    if node_tag_field == "id":
                        node_tag_attribs["id"] = node_attribs["id"]
                    elif node_tag_field == "value":
                        node_tag_attribs["value"] = tag.get("v")
                    elif node_tag_field == "key":
                        if ":" in tag.get("k"):
                            type_value, key_value = tag.get("k").split(":",1)
                            node_tag_attribs["key"] = key_value
                            node_tag_attribs["type"] = type_value
                        else:
                            node_tag_attribs["key"] = tag.get("k")
                            node_tag_attribs["type"] = default_tag_type
                # to update values of street name, zipcode and phone number if incorrect
                tag_type = tag.get("k")
                if (tag_type == "addr:street" or tag_type == "addr:postcode" or tag_type == "contact:phone" or tag_type == "phone"):
                    node_tag_attribs["value"] = update_value(node_tag_attribs["value"], tag_type)
                tags.append(node_tag_attribs)
        return {'node': node_attribs, 'node_tags': tags}
    
    
    elif element.tag == 'way':
        # to handle way attributes
        for way_field in way_attr_fields:
            way_attribs[way_field] = element.get(way_field)
        
        # to handle way tag attributes
        for tag in element.iter('tag'):
            if not(problem_chars.search(tag.get("k"))):
                way_tag_attribs = {}
                for way_tag_field in WAY_TAGS_FIELDS:
                    if way_tag_field == "id":
                        way_tag_attribs["id"] = way_attribs["id"]
                    elif way_tag_field == "value":
                        way_tag_attribs["value"] = tag.get("v")
                    elif way_tag_field == "key":
                        if ":" in tag.get("k"):
                            type_value, key_value = tag.get("k").split(":",1)
                            way_tag_attribs["key"] = key_value
                            way_tag_attribs["type"] = type_value
                        else:
                            way_tag_attribs["key"] = tag.get("k")
                            way_tag_attribs["type"] = default_tag_type
                # to update values of street name, zipcode and phone number if incorrect
                tag_type = tag.get("k")            
                if (tag_type == "addr:street" or tag_type == "addr:postcode" or tag_type == "contact:phone" or tag_type == "phone"):
                    way_tag_attribs["value"] = update_value(way_tag_attribs["value"], tag_type)
                tags.append(way_tag_attribs)
        
        # to handle way node attributes
        position = 0 
        for nd in element.iter('nd'):
            way_node_attribs = {}
            way_node_attribs["position"] = position
            way_node_attribs["id"] = way_attribs["id"]
            way_node_attribs["node_id"] = nd.get('ref')
            way_nodes.append(way_node_attribs)
            position += 1
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])

if not(os.path.isfile(NODES_PATH) and os.path.isfile(NODE_TAGS_PATH) and os.path.isfile(WAYS_PATH) and os.path.isfile(WAY_NODES_PATH) and os.path.isfile(WAY_TAGS_PATH)):
    process_map(filename, validate=True)
