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
    # - DC++: [dcpp/SettingsManager.cpp#l197](https://sourceforge.net/p/dcplusplus/code/ci/66549dcdcb1e12750be91ad361b4f3fa00ab67d8/tree/dcpp/SettingsManager.cpp#l197)
    # - AirDC++: [airdcpp/airdcpp/SettingsManager.cpp#L427](https://github.com/airdcpp/airdcpp-windows/blob/b863d8626d95d0ee483572a5139f8f569b558c3f/airdcpp/airdcpp/SettingsManager.cpp#L427)
    # - FlyLinkDC: [compiled/Settings/flylinkdc-config-r6xx.xml#L19](https://github.com/pavel-pimenov/flylinkdc-r6xx/blob/7fb959fe864198e9d50270b12ec37c29011d364e/compiled/Settings/flylinkdc-config-r6xx.xml#L19)
    # - EiskaltDC++: [dcpp/SettingsManager.cpp#L165](https://github.com/eiskaltdcpp/eiskaltdcpp/blob/390374214032dd537943a589ce38aaf46fe20da6/dcpp/SettingsManager.cpp#L165)
    "http://www.te-home.net/?do=hublist&get=hublist.xml",
    "http://dchublist.org/hublist.xml.bz2",
    "https://dchublist.ru/hublist.xml.bz2",
    "http://dchublist.biz/?do=hublist.xml.bz2",
    "https://dcnf.github.io/Hublist/hublist.xml.bz2", # a backup
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

def addr_complete(addr_hub):
    # Add DCHUB protocol to url if no protocol is specified
    if not urllib.parse.urlparse(addr_hub).scheme:
        addr_hub = 'dchub://' + addr_hub

    # Add NMDC optional port to url if no port is specified
    if urllib.parse.urlparse(addr_hub).scheme == 'dchub' and not urllib.parse.urlparse(addr_hub).port:
        addr_hub = addr_hub + ':411'

    return addr_hub

def hub_addr_compare(adrr_hub1, adrr_hub2):
    if urllib.parse.urlparse(adrr_hub1).hostname != urllib.parse.urlparse(adrr_hub2).hostname:
        return False
    if urllib.parse.urlparse(adrr_hub1).port != urllib.parse.urlparse(adrr_hub2).port:
        return False
    return True

def duplicate_hub(hub1, hub2):

    ## Check addr

    # First check: normal address hub1
    if hub_addr_compare(hub1.attrib['Address'], hub2.attrib['Address']):
        return True
    # Second check: failover address hub1
    has_hub1_failover = (hub1.attrib.get('Failover') != None and hub1.attrib.get('Failover') != '')
    if has_hub1_failover:
        if hub_addr_compare(hub1.attrib['Failover'], hub2.attrib['Address']):
            return True
    # Third check: failover address hub2
    if hub2.attrib.get('Failover') != None and hub2.attrib.get('Failover') != '':
        if hub_addr_compare(hub2.attrib['Failover'], hub1.attrib['Address']):
             return True
        if has_hub1_failover and hub_addr_compare(hub2.attrib['Failover'], hub1.attrib['Failover']):
            return True

    ## Check status

    if hub1.attrib.get('Status') != None and hub1.attrib.get('Status') != '' and hub2.attrib.get('Status') != None and hub2.attrib.get('Status') != '':
        if hub1.attrib['Status'] != hub2.attrib['Status']:
            return False

    ## Check same element Name, Description and Encoding

    if hub1.attrib.get('Name') != None and hub1.attrib.get('Name') != '' and hub2.attrib.get('Name') != None and hub2.attrib.get('Name') != '':
        if hub1.attrib.get('Description') != None and hub1.attrib.get('Description') != '' and hub2.attrib.get('Description') != None and hub2.attrib.get('Description') != '':
            if hub1.attrib.get('Encoding') != None and hub1.attrib.get('Encoding') != '' and hub2.attrib.get('Encoding') != None and hub2.attrib.get('Encoding') != '':
                return (hub1.attrib['Name'] == hub2.attrib['Name']) and (hub1.attrib['Description'] == hub2.attrib['Description']) and (hub1.attrib['Encoding'] == hub2.attrib['Encoding'])

    return False

def priorize_hub(hub):
    # adcs with kp, adcs
    # then adc, dchubs / nmdcs
    # and then others
    if urllib.parse.urlparse(hub.attrib['Address']).scheme == 'adcs':
        if urllib.parse.urlparse(hub.attrib['Address']).query.startswith('kp='):
            return 1
        else:
            return 2
    elif urllib.parse.urlparse(hub.attrib['Address']).scheme == 'adc':
        return 3
    elif urllib.parse.urlparse(hub.attrib['Address']).scheme in ('nmdcs', 'dchubs'):
        return 4
    else:
        return 5

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

        hub.attrib['Address'] = addr_complete(hub.attrib['Address'])

        # Same for failover
        if hub.attrib.get('Failover') != None and hub.attrib.get('Failover') != '':
            hub.attrib['Failover'] = addr_complete(hub.attrib['Failover'])

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

hubs.sort(key=priorize_hub)

clean_hubs = []

while len(hubs) != 0:
    hub = hubs[0]
    hubToKeep = True

    if len(sys.argv) >= 2:
        cmd = [sys.argv[1], 'ping', hub.attrib['Address'], '--out=xml-line', '--hubs=2', '--slots=6', '--share=324882100000']

        if urllib.parse.urlparse(hub.attrib['Address']).scheme in ('dchub', 'dchubs', 'nmdc', 'nmdcs'):
            cmd.append('--encoding=' + hub.attrib['Encoding'])

        output = run(cmd, check=False, stdout=PIPE).stdout
        hub_response = ET.fromstring(output)

        hub_response.attrib['Address'] = addr_complete(hub_response.attrib['Address'])

        print('URL returned by the hub', hub.attrib['Address'], '~', hub_response.attrib['Address'])

        if hub_response.attrib['Status'] == 'Error':
            if hub_response.attrib.get('ErrCode') == '226':
                hubToKeep = False
            elif hub.attrib.get('Status') == 'Offline':
                hubToKeep = False
            else:
                hub.attrib['Status'] = 'Offline'
                hub_response = hub
    else:
        hub_response = hub

    if hubToKeep:
        duplicata_hubs = [ h for h in hubs if (duplicate_hub(h, hub_response)) ]

        for duplicata_hub in duplicata_hubs:
            hub_response = hub_merge(hub_response, duplicata_hub)

    hubs = [ h for h in hubs if (not duplicate_hub(h, hub_response)) ]

    # if URL is redirected, we removed the old URL in the list too
    if hub.attrib['Address'] != hub_response.attrib['Address']:
        hubs = [ h for h in hubs if (not duplicate_hub(h, hub)) ]

        # we merge duplicate clean_hub
        duplicata_clean_hubs = [ c for c in clean_hubs if (duplicate_hub(c, hub_response)) ]
        for duplicata_clean_hub in duplicata_clean_hubs:
            hub_response = hub_merge(hub_response, duplicata_clean_hub)
        clean_hubs = [ c for c in clean_hubs if (not duplicate_hub(c, hub_response)) ]

    if hubToKeep:
        clean_hubs.append(hub_response)

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
