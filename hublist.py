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
    # - DC++: [dcpp/SettingsManager.cpp#l197](https://sourceforge.net/p/dcplusplus/code/ci/eb139c8d81a96ed6627b6fda8c94ffb325a0a308/tree/dcpp/SettingsManager.cpp#l197)
    # - AirDC++: [airdcpp/airdcpp/SettingsManager.cpp#L426](https://github.com/airdcpp/airdcpp-windows/blob/8c359424d883ba836b344383c862ba0b386fc30b/airdcpp/airdcpp/SettingsManager.cpp#L426)
    # - FlyLinkDC: [compiled/Settings/flylinkdc-config-r6xx.xml#L19](https://github.com/pavel-pimenov/flylinkdc-r6xx/blob/094f312eb07718f1583a7e08da4abe4557d01835/compiled/Settings/flylinkdc-config-r6xx.xml#L19)
    # - EiskaltDC++: [dcpp/SettingsManager.cpp#L165](https://github.com/eiskaltdcpp/eiskaltdcpp/blob/9b65fdd4f51b93a90a63ac84d638b7ff1f79771d/dcpp/SettingsManager.cpp#L165)
    "https://www.te-home.net/?do=hublist&get=hublist.xml",
    "https://dchublist.org/hublist.xml.bz2",
    "https://dchublist.ru/hublist.xml.bz2",
    "https://hublist.pwiam.com/hublist.xml",
    "http://dchublist.biz/?do=hublist.xml.bz2",
    "https://dcnf.github.io/Hublist/hublist.xml.bz2", # a backup
]

local_hublists = [
    #"/home/user/file.xml",
]

# timeout in seconds
timeout = 10

##### END OF THE CONFIGURATION #####

socket.setdefaulttimeout(timeout)

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

# Suported chemas of NMDC protocol
supported_schemas_dc = ['dchub', 'dchubs', 'nmdc', 'nmdcs']

# Suported chemas of Secure NMDC protocol
supported_schemas_dc_secure = ['dchubs', 'nmdcs']

# Suported chemas of unsecure NMDC protocol
supported_schemas_dc_unsecure = ['dchub', 'nmdc']

# Suported chemas of ADC protocol
supported_schemas_adc = ['adc', 'adcs']

# Suported chemas of Secure ADC protocol
supported_schemas_adc_secure = ['adcs']

# Suported chemas of unsecure ADC protocol
supported_schemas_adc_unsecure = ['adc']

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
    url_info = urllib.parse.urlparse(addr_hub)

    # Add DCHUB protocol to url if no protocol is specified
    if not url_info.scheme:
        addr_hub = 'dchub://' + addr_hub

    # Add NMDC optional port to url if no port is specified
    if url_info.scheme == 'dchub' and not url_info.port:
        addr_hub = addr_hub + ':411'

    return addr_hub

def hub_addr_compare(adrr_hub1, adrr_hub2):
    if urllib.parse.urlparse(adrr_hub1).hostname != urllib.parse.urlparse(adrr_hub2).hostname:
        return False
    if urllib.parse.urlparse(adrr_hub1).port != urllib.parse.urlparse(adrr_hub2).port:
        return False
    return True

def duplicate_hub(hub1, hub2):

    # CHECK ADDR

    ## First check: normal address hub1
    if hub_addr_compare(hub1.attrib['Address'], hub2.attrib['Address']):
        return True

    has_hub1_failover = (hub1.attrib.get('Failover') != None and hub1.attrib.get('Failover') != '')
    has_hub2_failover = (hub2.attrib.get('Failover') != None and hub2.attrib.get('Failover') != '')

    ## Second check: failover address hub1
    if has_hub1_failover:
        if hub_addr_compare(hub1.attrib['Failover'], hub2.attrib['Address']):
            return True

    ## Third check: failover address hub2
    if has_hub2_failover:
        if hub_addr_compare(hub2.attrib['Failover'], hub1.attrib['Address']):
            return True

    ## Fourth check: failover address hub
    if has_hub1_failover and has_hub2_failover:
        if hub_addr_compare(hub1.attrib['Failover'], hub2.attrib['Failover']):
            return True

    # CHECK STATUS

    if hub1.attrib.get('Status') != None and hub1.attrib.get('Status') != '' and hub2.attrib.get('Status') != None and hub2.attrib.get('Status') != '':
        if hub1.attrib['Status'] != hub2.attrib['Status']:
            return False

    # CHECK SAME ELEMENT NAME,
    # DESCRIPTION
    # AND ENCODING

    if hub1.attrib.get('Name') != None and hub1.attrib.get('Name') != '' and hub2.attrib.get('Name') != None and hub2.attrib.get('Name') != '':
        if hub1.attrib.get('Description') != None and hub1.attrib.get('Description') != '' and hub2.attrib.get('Description') != None and hub2.attrib.get('Description') != '':
            if hub1.attrib.get('Encoding') != None and hub1.attrib.get('Encoding') != '' and hub2.attrib.get('Encoding') != None and hub2.attrib.get('Encoding') != '':
                return (hub1.attrib['Name'] == hub2.attrib['Name']) and (hub1.attrib['Description'] == hub2.attrib['Description']) and (hub1.attrib['Encoding'] == hub2.attrib['Encoding'])

    return False

def priorize_hub(hub):
    # Priority:
    # - ADCS with key
    # - ADCS
    # - ADC
    # - DCHUBS / NMDCS
    # - DCHUB / NMDC
    # - are there any others?
    if urllib.parse.urlparse(hub.attrib['Address']).scheme in supported_schemas_adc_secure:
        if urllib.parse.urlparse(hub.attrib['Address']).query.startswith('kp='):
            return 1
        else:
            return 2
    elif urllib.parse.urlparse(hub.attrib['Address']).scheme in supported_schemas_adc_unsecure:
        return 3
    elif urllib.parse.urlparse(hub.attrib['Address']).scheme in supported_schemas_dc_secure:
        return 4
    elif urllib.parse.urlparse(hub.attrib['Address']).scheme in supported_schemas_dc_unsecure:
        return 5
    else:
        return 6

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
hubs_from_xml = []

for xml_file in xml_files:
    root = ET.fromstring(xml_file)

    for hub_element in root.iter('Hub'):

        hub_element.attrib['Address'] = addr_complete(hub_element.attrib['Address'])

        # Same for failover
        if hub_element.attrib.get('Failover') != None and hub_element.attrib.get('Failover') != '':
            hub_element.attrib['Failover'] = addr_complete(hub_element.attrib['Failover'])

        # Delete if no Encoding is set
        if urllib.parse.urlparse(hub_element.attrib['Address']).scheme in supported_schemas_dc:
            if hub_element.attrib.get('Encoding') != None and hub_element.attrib.get('Encoding') != '':
                if hub_element.attrib['Encoding'].lower() in supported_encoding:
                    hubs_from_xml.append(hub_element)
                else:
                    print('Unknown encoding:', hub_element.attrib.get('Encoding'), hub_element.attrib['Address'])
        elif urllib.parse.urlparse(hub_element.attrib['Address']).scheme in ('adc', 'adcs'):
            hub_element.attrib['Encoding'] = 'UTF-8'
            hubs_from_xml.append(hub_element)
        else:
            print('Unknown scheme:', urllib.parse.urlparse(hub_element.attrib['Address']).scheme, hub_element.attrib['Address'])

hubs_from_xml.sort(key=priorize_hub)

clean_hubs = []

while len(hubs_from_xml) != 0:
    hub_from_xml = hubs_from_xml[0]

    hubToKeep = True

    if len(sys.argv) >= 2:
        cmd = [sys.argv[1], 'ping', hub_from_xml.attrib['Address'], '--out=xml-line', '--hubs=2', '--slots=6', '--share=324882100000']

        if urllib.parse.urlparse(hub_from_xml.attrib['Address']).scheme in supported_schemas_dc:
            cmd.append('--encoding=' + hub_from_xml.attrib['Encoding'])

        output = run(cmd, check=False, stdout=PIPE).stdout
        hub_response = ET.fromstring(output)

        hub_response.attrib['Address'] = addr_complete(hub_response.attrib['Address'])

        print('URL returned by the hub', hub_from_xml.attrib['Address'], '~', hub_response.attrib['Address'])

        if hub_response.attrib['Status'] == 'Error':
            if hub_response.attrib.get('ErrCode') == '226':
                hubToKeep = False
            elif hub_response.attrib.get('Status') == 'Offline':
                hubToKeep = False
            else:
                hub_from_xml.attrib['Status'] = 'Offline'
                hub_response = hub_from_xml
    else:
        hub_response = hub_from_xml

    for duplicata_hub in list(hubs_from_xml):
        if (duplicate_hub(duplicata_hub, hub_response)):
            hub_response = hub_merge(hub_response, duplicata_hub)
            hubs_from_xml.remove(duplicata_hub)

    # if URL is redirected, we also removed the old URL from the list too
    if hub_from_xml.attrib['Address'] != hub_response.attrib['Address']:
        for duplicata_hub in list(hubs_from_xml):
            if (duplicate_hub(duplicata_hub, hub_from_xml)):
                hubs_from_xml.remove(duplicata_hub)

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
