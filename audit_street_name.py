import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint
import re

# define file to be used throughout analayis
filename = "kuala-lumpur_malaysia_sample.osm"

# expected streetnames
expected = ["Jalan", "Lorong", "Persiaran", "Lebuhraya", "Perindustrian",
            "Kampung", "Lebuh", "Changkat", "Tengkat", "Lengkok", 
            "Lingkaran", "Pintasan", "Taman", "Apartment", "Desa", "Batu"]

# regular expressions
street_type_re = re.compile(r'^\b\S+\.?', re.IGNORECASE)

# updates street name to street types dictionary if street type is not as per expected format
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

# returns true if element is a street name            
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

# returns dictionary of incorrect street types and street names with that street type  
def audit_street(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types

# prints dictionary
st_types = audit_street(filename)
pprint.pprint(dict(st_types))
