#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import bz2
import socket
import urllib, urllib.request, urllib.parse
import xml.etree.cElementTree as ET
import socket
#from subprocess import Popen, PIPE
from subprocess import check_output, run, PIPE

# List of attributes, in the form (attribute name, default value, type)
attributes = (
        # useful for all
        ('Address', '', 'string'),
        ('Name', '', 'string'),
        ('Description', '', 'string'),
        ('Users', 0, 'int'),
        ('Country', '', 'string'),
        ('Shared', 0, 'bytes'),
        ('Minshare', 0, 'bytes'),
        ('Minslots', 0, 'int'),
        ('Maxhubs', 0, 'int'),
        ('Maxusers', 0, 'int'),
        ('Reliability', 0, 'string'),
        ('Rating', '0', 'string'),
        # normally useful, for NMDC
        ('Encoding', '', 'string'),
        # useful for flylinkdc
        ('Software', '', 'string'),
        ('Website', '', 'string'),
        ('Email', '', 'string'),
        ('ASN', '', 'string'),
        ('Operators', 0, 'int'),
        ('Bots', 0, 'int'),
        ('Infected', 0, 'int'),
        # useful for website
        ('Status', 'Offline', 'string'),
        # useful for this script
        ('Failover', '', 'string'),
)

# in-place prettyprint formatter from http://effbot.org/zone/element-lib.htm#prettyprint
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

# based on https://github.com/openstack/charm-plumgrid-gateway/blob/master/hooks/charmhelpers/contrib/network/ip.py
def is_ip(address):
    try:
        # Test to see if already an IPv4 address
        socket.inet_aton(address)
        return True
    except socket.error:
        return False

def get_host_ip(hostname, fallback=None):
    if is_ip(hostname):
        return hostname
    ip_addr = socket.gethostbyname(hostname)
    return ip_addr

def hub_merge(hub1, hub2):
    """ Set attributes with no value in hub1 from value in hub2 """
    for att, _, _ in attributes:
        if att in hub2.attrib:
            if hub1.attrib.get(att) == None and hub2.attrib.get(att) != None:
                hub1.attrib[att] = hub2.attrib[att]
    return hub1


external_hublist = [
    # list based on:
    # - https://sourceforge.net/p/dcplusplus/code/ci/default/tree/dcpp/SettingsManager.cpp#l197
    # - https://github.com/airdcpp/airgit/blob/master/airdcpp/airdcpp/SettingsManager.cpp#L339
    # - https://github.com/pavel-pimenov/flylinkdc-r5xx/blob/master/compiled/Settings/flylinkdc-config-r5xx.xml#L22
    "http://www.te-home.net/?do=hublist&get=hublist.xml",
    "http://dchublist.org/hublist.xml.bz2",
    "https://dchublist.ru/hublist.xml.bz2",
    #"http://hublist.eu/hublist.xml.bz2", # cloudflare
    "http://dchublists.com/?do=hublist&get=hublist.xml",
    #"http://www.hublista.hu/hublist.xml.bz2", # too many timeout
    #"http://dchublist.biz/?do=hublist.xml.bz2", # unknown error
]
# timeout in seconds
timeout = 10
socket.setdefaulttimeout(timeout)

xml_files = []

# Download files (and extract if necessary)
for url in external_hublist:
    print('Will download hub list from', url)
    xml_file = urllib.request.urlopen(url).read()
    if url.endswith('.bz2'):
        xml_file = bz2.decompress(xml_file)
    xml_files.append(xml_file)

# checking dcping command is send
if len(sys.argv) != 2:
    print("Usage: python hublist.py [location_of_dcping]")
    sys.exit (1)

# Parsing XML files
hubs = []

for xml_file in xml_files:
    root = ET.fromstring(xml_file)

    for hub in root.iter('Hub'):

        # Add DCHUB protocol to url if no protocol is specified
        if not urllib.parse.urlparse(hub.attrib['Address']).scheme:
            print('Adding dchub:// to hub adress with unspecified protocol', hub.attrib['Address'])
            hub.attrib['Address'] = 'dchub://' + hub.attrib['Address']

        # Add NMDC optional port to url if no port is specified
        if urllib.parse.urlparse(hub.attrib['Address']).scheme == 'dchub' and not urllib.parse.urlparse(hub.attrib['Address']).port:
            print('Adding :411 to hub adress with unspecified port', hub.attrib['Address'])
            hub.attrib['Address'] = hub.attrib['Address'] + ':411'
        
        hubs.append(hub)

clean_hubs = []
DEVNULL = open(os.devnull, 'wb')
while len(hubs) != 0:
    hub = hubs[0]

    #output = check_output([sys.argv[1], 'ping', hub.attrib['Address'], '--out=xml'], stderr=DEVNULL)
    output = run([sys.argv[1], 'ping', hub.attrib['Address'], '--out=xml'], check=False, stdout=PIPE).stdout

    hub_response = ET.fromstring(output)

    print(hub_response.attrib['Address'])
    duplicata_hubs = [ h for h in hubs if h.attrib['Address'] in (hub_response.attrib['Address'], hub_response.attrib.get('Failover')) ]

    for duplicata_hub in duplicata_hubs: 
        hub_response = hub_merge(hub_response, duplicata_hub)

    clean_hubs.append(hub_response)
    hubs = [ h for h in hubs if h.attrib['Address'] not in (hub_response.attrib['Address'], hub_response.attrib.get('Failover')) ]

# Prepare output file
merge_root = ET.Element('Hublist')
merge_hubs = ET.SubElement(merge_root, 'Hubs')
merge_cols = ET.SubElement(merge_hubs, 'Columns')

# do columns
for name, _, type_ in attributes:
    ET.SubElement(merge_cols, 'Column', Name=name, Type=type_)

# poplate hub columns
for hub_add in clean_hubs:
    attribs = {}
    for name, default, type_ in attributes:
        if name in hub_add.attrib and hub_add.attrib.get(name) != None:
            attribs[name] = hub_add.attrib.get(name)
        else:
            # Inserting default value
            attribs[name] = str(default)
    ET.SubElement(merge_hubs, 'Hub', attribs)

indent(merge_root)
merge_tree = ET.ElementTree(merge_root)
merge_tree.write('hublist.xml', encoding='UTF-8', xml_declaration=True)

# bz2
tarbz2contents = bz2.compress(open('hublist.xml', 'rb').read(), 9)
fh = open('hublist.xml.bz2', 'wb')
fh.write(tarbz2contents)
fh.close()
