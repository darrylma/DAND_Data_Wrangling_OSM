import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint

# define file to be used throughout analayis
filename = "kuala-lumpur_malaysia_sample.osm"

# returns true if element is a street name            
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

# returns true if element is a zipcode           
def is_zipcode(elem):
    return (elem.attrib['k'] == "addr:postcode")

# updates street name to zipcode dictionary if zipcode length is not equal to 5 characters
def audit_zip_type(elem, incorrect_zipcodes, zipcode):
    if len(zipcode) != 5:
        for tag in elem.iter('tag'):
            if is_street_name(tag):
                incorrect_zipcodes[zipcode].add(tag.attrib['v'])

# returns dictionary of incorrect zipcodes and street names associated with the zipcode  
def audit_zip(osmfile):
    osm_file = open(osmfile, "r")
    incorrect_zipcodes = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_zipcode(tag):
                    audit_zip_type(elem, incorrect_zipcodes, tag.attrib['v'])
    osm_file.close()
    return incorrect_zipcodes

# prints dictionary
inc_zipcodes = audit_zip(filename)
pprint.pprint(dict(inc_zipcodes))
