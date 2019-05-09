#!/usr/bin/python3
# -*- coding: utf-8 -*-

import bz2
import socket
import sys
import urllib, urllib.request, urllib.parse
import xml.etree.cElementTree as ET
from subprocess import run, PIPE

##### CAN BE CONFIGURED #####

own_hublist = "https://dcnf.github.io/Hublist/ownDataHublist.xml"

internet_hublists = [
    # list based on:
    # - https://sourceforge.net/p/dcplusplus/code/ci/default/tree/dcpp/SettingsManager.cpp#l197
    # - https://github.com/airdcpp/airgit/blob/master/airdcpp/airdcpp/SettingsManager.cpp#L339
    # - https://github.com/pavel-pimenov/flylinkdc-r5xx/blob/master/compiled/Settings/flylinkdc-config-r5xx.xml#L22
    "http://www.te-home.net/?do=hublist&get=hublist.xml",
    "http://dchublist.org/hublist.xml.bz2",
    "https://dchublist.ru/hublist.xml.bz2",
    #"http://hublist.eu/hublist.xml.bz2", # cloudflare
    #"http://www.hublista.hu/hublist.xml.bz2", # too many timeout
    "http://dchublist.biz/?do=hublist.xml.bz2",
]

local_hublists = [
    #"/home/user/file.xml",
]

# timeout in seconds
timeout = 10
socket.setdefaulttimeout(timeout)

##### END OF THE CONFIGURATION #####

# List of attributes, in the form (attribute name, type)
attributes = (
        # useful for all
        ('Address', 'string'),
        ('Name', 'string'),
        ('Description', 'string'),
        ('Users', 'int'),
        ('Country', 'string'),
        ('Shared', 'bytes'),
        ('Minshare', 'bytes'),
        ('Minslots', 'int'),
        ('Maxhubs', 'int'),
        ('Maxusers', 'int'),
        ('Reliability', 'string'),
        ('Rating', 'string'),
        # normally useful, for NMDC
        ('Encoding', 'string'),
        # useful for flylinkdc
        ('Software', 'string'),
        ('Website', 'string'),
        ('Email', 'string'),
        ('ASN', 'string'),
        ('Operators', 'int'),
        ('Bots', 'int'),
        ('Infected', 'int'),
        # useful for website
        ('Status', 'string'),
        # useful for this script
        ('Failover', 'string'),
)

# Supported NMDC Encoding (should be in lower)
supported_encoding = ['utf-8', 'cp1250', 'cp1251', 'cp1252', 'cp1253', 'cp1254', 'cp1256', 'cp1257','gb18030']

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

def hub_addr_compare(adrr_hub1, adrr_hub2):
    if urllib.parse.urlparse(adrr_hub1).hostname != urllib.parse.urlparse(adrr_hub2).hostname:
        return False
    if urllib.parse.urlparse(adrr_hub1).port != urllib.parse.urlparse(adrr_hub2).port:
        return False
    return True

def reorder(hub):
    # yes, it's priorizing adcs
    if urllib.parse.urlparse(hub.attrib['Address']).scheme == 'adcs':
        if urllib.parse.urlparse(hub.attrib['Address']).query.startswith('kp='):
            return 1
        else:
            return 2
    elif urllib.parse.urlparse(hub.attrib['Address']).scheme == 'adc':
        return 3
    else:
        return 4

def hub_merge(hub1, hub2):
    # Set attributes with no value in hub1 from value in hub2
    for att, _ in attributes:
        if att in hub2.attrib:
            if (hub1.attrib.get(att) == None or hub1.attrib.get(att) == '') and hub2.attrib.get(att) != None and hub2.attrib.get(att) != '':
                hub1.attrib[att] = hub2.attrib[att]
    return hub1

xml_files = []

# Download files (and extract if necessary)
internet_hublists.insert(0, own_hublist)

for url in internet_hublists:
    print('Will download hub list from', url)
    xml_file = urllib.request.urlopen(url).read()
    if url.endswith('.bz2'):
        xml_file = bz2.decompress(xml_file)
    xml_files.append(xml_file)

# Import local file
for local_hublist in local_hublists:
    print('Loading hub list from', local_hublist)
    if local_hublist.endswith('.bz2'):
        local_hublist = bz2.BZ2File(local_hublist)
    root = ET.parse(local_hublist).getroot()
    xml_files.append(ET.tostring(root).decode())

# Parsing XML files
hubs = []

for xml_file in xml_files:
    root = ET.fromstring(xml_file)

    for hub in root.iter('Hub'):

        # Add DCHUB protocol to url if no protocol is specified
        if not urllib.parse.urlparse(hub.attrib['Address']).scheme:
            hub.attrib['Address'] = 'dchub://' + hub.attrib['Address']

        # Add NMDC optional port to url if no port is specified
        if urllib.parse.urlparse(hub.attrib['Address']).scheme == 'dchub' and not urllib.parse.urlparse(hub.attrib['Address']).port:
            hub.attrib['Address'] = hub.attrib['Address'] + ':411'

        # Delete if no Encoding is set
        if urllib.parse.urlparse(hub.attrib['Address']).scheme in ('dchub', 'dchubs', 'nmdc', 'nmdcs'):
            if hub.attrib.get('Encoding') != None and hub.attrib.get('Encoding') != '':
                if hub.attrib['Encoding'].lower() in supported_encoding:
                    hubs.append(hub)
                else:
                    print('Unknown encoding:', hub.attrib.get('Encoding'), hub.attrib['Address'])
        elif urllib.parse.urlparse(hub.attrib['Address']).scheme in ('adc', 'adcs'):
            hub.attrib['Encoding'] = 'UTF-8'
            hubs.append(hub)
        else:
            print('Unknown scheme:', urllib.parse.urlparse(hub.attrib['Address']).scheme, hub.attrib['Address'])

hubs.sort(key=reorder)

clean_hubs = []

while len(hubs) != 0:
    hub = hubs[0]
    isPublic = True

    if len(sys.argv) >= 2:
        cmd = [sys.argv[1], 'ping', hub.attrib['Address'], '--out=xml-line', '--hubs=2', '--slots=6', '--share=324882100000']

        if urllib.parse.urlparse(hub.attrib['Address']).scheme in ('dchub', 'dchubs', 'nmdc', 'nmdcs'):
            cmd.append('--encoding=' + hub.attrib['Encoding'])

        output = run(cmd, check=False, stdout=PIPE).stdout
        hub_response = ET.fromstring(output)
        print(hub_response.attrib['Address'])
        if hub_response.attrib['Status'] == 'Error':
            if hub_response.attrib.get('ErrCode') == '226':
                isPublic = False
            else:
                hub_response = hub

    else:
        hub_response = hub

    if isPublic:
        duplicata_hubs = [ h for h in hubs if (hub_addr_compare(h.attrib['Address'], hub_response.attrib['Address']) or hub_addr_compare(h.attrib['Address'], hub_response.attrib.get('Failover'))) ]

        for duplicata_hub in duplicata_hubs:
            hub_response = hub_merge(hub_response, duplicata_hub)

        clean_hubs.append(hub_response)

    hubs = [ h for h in hubs if (not hub_addr_compare(h.attrib['Address'], hub_response.attrib['Address']) and not hub_addr_compare(h.attrib['Address'], hub_response.attrib.get('Failover'))) ]

# Prepare output file
merge_root = ET.Element('Hublist', Name='The DCNF Hublist', Address='https://dcnf.github.io/Hublist/')
merge_hubs = ET.SubElement(merge_root, 'Hubs')
merge_cols = ET.SubElement(merge_hubs, 'Columns')

# do columns
for name, type_ in attributes:
    ET.SubElement(merge_cols, 'Column', Name=name, Type=type_)

# populate hub columns
for hub_add in clean_hubs:
    attribs = {}
    for name, _ in attributes:
        if name in hub_add.attrib and hub_add.attrib.get(name) != None:
            attribs[name] = hub_add.attrib.get(name)
        else:
            # Inserting no value
            attribs[name] = ''
    ET.SubElement(merge_hubs, 'Hub', attribs)

indent(merge_root)
merge_tree = ET.ElementTree(merge_root)
merge_tree.write('hublist.xml', encoding='UTF-8', xml_declaration=True)

# bz2
tarbz2contents = bz2.compress(open('hublist.xml', 'rb').read(), 9)
fh = open('hublist.xml.bz2', 'wb')
fh.write(tarbz2contents)
fh.close()
