import bz2
import urllib, urllib.request, urllib.parse
import sys
import xml.etree.cElementTree as ET
import socket

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

urls = [ 
    # list based on:
    # - https://sourceforge.net/p/dcplusplus/code/ci/default/tree/dcpp/SettingsManager.cpp#l197
    # - https://github.com/airdcpp/airgit/blob/master/airdcpp/airdcpp/SettingsManager.cpp#L339
    # - https://github.com/pavel-pimenov/flylinkdc-r5xx/blob/master/compiled/Settings/flylinkdc-config-r5xx.xml#L22
    "http://www.te-home.net/?do=hublist&get=hublist.xml",
    "http://dchublist.org/hublist.xml.bz2",
    "https://dchublist.ru/hublist.xml.bz2",
    #"http://hublist.eu/hublist.xml.bz2", # cloudflare
    #"http://dchublists.com/?do=hublist&get=hublist.xml", # unknown error
    #"http://www.hublista.hu/hublist.xml.bz2", # too many timeout
    "http://dchublist.biz/?do=hublist.xml.bz2",
]
xml_files = []

# Download files (and extract if necessary)
for url in urls:
    print('Will download hub list from', url)
    xml_file = urllib.request.urlopen(url).read()
    if url.endswith('.bz2'):
        xml_file = bz2.decompress(xml_file)
    xml_files.append(xml_file)

# Parsing XML files
colsets = []
hubs = dict()
for xml_file, url in zip(xml_files, urls):
    root = ET.fromstring(xml_file)
    cols = list(root.iter('Column'))
    colset = set()
    for c in cols:
        colset.add((c.attrib['Name'], c.attrib['Type']))
    colsets.append(colset)

    for hub in root.iter('Hub'): 

        # Add DCHUB protocol to url if no protocol is specified
        if not urllib.parse.urlparse(hub.attrib['Address']).scheme:
            print('Adding dchub:// to hub adress with unspecified protocol', hub.attrib['Address'])
            hub.attrib['Address'] = "dchub://" + hub.attrib['Address']

        # Add DCHUB optional port to url if no port is specified
        if urllib.parse.urlparse(hub.attrib['Address']).scheme == "dchub" and not urllib.parse.urlparse(hub.attrib['Address']).port:
            print('Adding :411 to hub adress with unspecified port', hub_adr)
            hub.attrib['Address'] = hub.attrib['Address'] + ":411"

        # Remove duplicate hubs
        try:
            ip = get_host_ip(urllib.parse.urlparse(hub.attrib['Address']).hostname)
            hub_adr = urllib.parse.urlparse(hub.attrib['Address']).scheme + "://" + ip + ":" + str(urllib.parse.urlparse(hub.attrib['Address']).port)
            if hub_adr in hubs.keys():
                print('Dropping duplicate hub', hub_adr, 'from hub list', url)
                for key in hubs[hub_adr].keys():
                    if key not in hubs[hub_adr].keys():
                        hubs[hub_adr][key] = hub[key]
                continue
        except:
            print(hub.attrib['Address'], 'does not respond to ping, IGNORED')
            continue
        hubs[hub_adr] = hub

# Keep all colums encountered
colnames = set.union(*colsets)
print('Columns in output file:', [c[0] for c in colnames])

# Prepare output file
merge_root = ET.Element('Hublist')
merge_hubs = ET.SubElement(merge_root, 'Hubs')
merge_cols = ET.SubElement(merge_hubs, 'Columns')
for cn in colnames:
    name, type_ = cn
    ET.SubElement(merge_cols, 'Column', Name=name, Type=type_)

for hub_adr, hub_elem in hubs.items():
    attribs = {}
    for k in colnames:
        c, type_ = k
        if c in hub_elem.attrib:
            attribs[c] = hub_elem.attrib[c]
        else:
            # Inserting default value
            attribs[c] = ''
    ET.SubElement(merge_hubs, 'Hub', attribs)

indent(merge_root)
merge_tree = ET.ElementTree(merge_root)
merge_tree.write('hublist.xml', encoding='UTF-8', xml_declaration=True)

# bz2
tarbz2contents = bz2.compress(open('hublist.xml', 'rb').read(), 9)
fh = open('hublist.xml.bz2', "wb")
fh.write(tarbz2contents)
fh.close()
