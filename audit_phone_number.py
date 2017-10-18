import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint

# define file to be used throughout analayis
filename = "kuala-lumpur_malaysia_sample.osm"

# updates phone number to phone number lengths dictionary
def audit_phone_number(phone_number_lengths, number):
    phone_number_lengths[len(number)].add(number)

# returns true if element is a phone number            
def is_phone_number(elem):
    return (elem.attrib['k'] == "contact:phone" or elem.attrib['k'] == "phone")

# returns dictionary of phone number lengths with respective list of phone numbers  
def audit_phone(osmfile):
    osm_file = open(osmfile, "r")
    phone_number_lengths = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_phone_number(tag):
                    audit_phone_number(phone_number_lengths, tag.attrib['v'])
    osm_file.close()
    return phone_number_lengths

# prints dictionary
phone_number_formats = audit_phone(filename)
pprint.pprint(dict(phone_number_formats))
