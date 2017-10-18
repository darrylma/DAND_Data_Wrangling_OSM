import xml.etree.cElementTree as ET

# define file to be used throughout analayis
filename = "kuala-lumpur_malaysia_sample.osm"

# returns dictionary of all tags and respective number of occurences
def count_tags(filename):
    tags = {}
    for event, elem in ET.iterparse(filename):
        if elem.tag in tags:
            tags[elem.tag] += 1
        else:
            tags[elem.tag] = 1
    return tags

# returns set of all unique user ids
def number_of_unique_users(filename):
    users = set()
    for _, element in ET.iterparse(filename):
        if element.get("uid") not in users and element.get("uid") != None:
            users.add(element.get("uid"))
    return users

# to print out results
tags = count_tags(filename)
users = number_of_unique_users(filename)
for key in tags:
    if (key == 'node' or key == 'way'):
        print '\033[1m' + "Number of " + str(key)  + "s: " + '\033[0m' + str(tags[key])
print '\033[1m' + "Number of unique users:" + '\033[0m' + str(len(users))
