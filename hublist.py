#!/usr/bin/python3
# -*- coding: utf-8 -*-

import bz2
import socket
import sys
import urllib
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from subprocess import run, PIPE
import concurrent.futures
import argparse
import time

##### CONFIGURATION #####

OWN_HUBLIST = "https://dcnf.github.io/Hublist/ownDataHublist.xml"

INTERNET_HUBLISTS = [
    # list based on:
    # - DC++: [dcpp/SettingsManager.cpp#l198](https://sourceforge.net/p/dcplusplus/code/ci/730492fc723149c32229e997467477d19e4f4539/tree/dcpp/SettingsManager.cpp#l198)
    # - DC++: [dcpp/SettingsManager.cpp#l197](https://sourceforge.net/p/dcplusplus/code/ci/eb139c8d81a96ed6627b6fda8c94ffb325a0a308/tree/dcpp/SettingsManager.cpp#l197)
    # - AirDC++: [airdcpp/airdcpp/settings/SettingsManager.cpp#L444](https://github.com/airdcpp/airdcpp-windows/blob/bbecdd9e14015118cefbe8801f508b7eff6f3867/airdcpp/airdcpp/settings/SettingsManager.cpp#L444)
    # - AirDC++: [airdcpp/airdcpp/SettingsManager.cpp#L426](https://github.com/airdcpp/airdcpp-windows/blob/8c359424d883ba836b344383c862ba0b386fc30b/airdcpp/airdcpp/SettingsManager.cpp#L426)
    # - FlyLinkDC: [compiled/Settings/flylinkdc-config-r6xx.xml#L19](https://github.com/pavel-pimenov/flylinkdc-r6xx/blob/e4a93a0da785ebdd23217ebb91316445d410f800/compiled/Settings/flylinkdc-config-r6xx.xml#L19)
    # - FlyLinkDC: [compiled/Settings/flylinkdc-config-r6xx.xml#L19](https://github.com/pavel-pimenov/flylinkdc-r6xx/blob/094f312eb07718f1583a7e08da4abe4557d01835/compiled/Settings/flylinkdc-config-r6xx.xml#L19)
    # - EiskaltDC++: [dcpp/SettingsManager.cpp#L165](https://github.com/eiskaltdcpp/eiskaltdcpp/blob/697db4b03e3d9ffa48b3d4c74fd043dee7663266/dcpp/SettingsManager.cpp#L165)
    # - EiskaltDC++: [dcpp/SettingsManager.cpp#L165](https://github.com/eiskaltdcpp/eiskaltdcpp/blob/9b65fdd4f51b93a90a63ac84d638b7ff1f79771d/dcpp/SettingsManager.cpp#L165)
    # - BlackLink: [client/ConfCore.cpp#L22](https://github.com/zipper9/blacklink/blob/bf987fcb4077ffd6232461314e4e90acdb3167f6/client/ConfCore.cpp#L22)
    "https://www.te-home.net/?do=hublist&get=hublist.xml",
    "https://dchublist.org/hublist.xml.bz2",
    "https://dchublist.ru/hublist.xml.bz2",
    "https://dchublist.biz/?do=hublist.xml.bz2",
    "https://hublist.pwiam.com/hublist.xml",
    "https://dchublists.com/?do=hublist&get=hublist.xml.bz2",
    "https://dcnf.github.io/Hublist/hublist.xml.bz2", # a backup
]

LOCAL_HUBLISTS = [
    #"/home/user/file.xml",
]

# Default timeout in seconds
DEFAULT_TIMEOUT = 10

# Multithreading
MAX_CONCURRENT_PINGS = 5
PING_TIMEOUT = 15

# Supported NMDC Encodings
SUPPORTED_ENCODING = ['utf-8', 'cp1250', 'cp1251', 'cp1252', 'cp1253', 'cp1254', 'cp1256', 'cp1257', 'gb18030']

# Protocol schemas - centralized definition
PROTOCOLS = {
    'dchub': {'type': 'dc', 'secure': False},
    'dchubs': {'type': 'dc', 'secure': True},
    'nmdc': {'type': 'dc', 'secure': False},
    'nmdcs': {'type': 'dc', 'secure': True},
    'adc': {'type': 'adc', 'secure': False},
    'adcs': {'type': 'adc', 'secure': True},
}

# Derived constants for backward compatibility (using sets for performance)
SUPPORTED_SCHEMAS_DC = {p for p, info in PROTOCOLS.items() if info['type'] == 'dc'}
SUPPORTED_SCHEMAS_DC_SECURE = {p for p, info in PROTOCOLS.items() if info['type'] == 'dc' and info['secure']}
SUPPORTED_SCHEMAS_DC_UNSECURE = {p for p, info in PROTOCOLS.items() if info['type'] == 'dc' and not info['secure']}
SUPPORTED_SCHEMAS_ADC = {p for p, info in PROTOCOLS.items() if info['type'] == 'adc'}
SUPPORTED_SCHEMAS_ADC_SECURE = {p for p, info in PROTOCOLS.items() if info['type'] == 'adc' and info['secure']}
SUPPORTED_SCHEMAS_ADC_UNSECURE = {p for p, info in PROTOCOLS.items() if info['type'] == 'adc' and not info['secure']}

# Helper functions for protocol checking
def is_dc_protocol(scheme):
    """Check if scheme is a DC protocol (dchub, dchubs, nmdc, or nmdcs)"""
    return scheme in SUPPORTED_SCHEMAS_DC

def is_adc_protocol(scheme):
    """Check if scheme is an ADC protocol (adc or adcs)"""
    return scheme in SUPPORTED_SCHEMAS_ADC

def is_secure_protocol(scheme):
    """Check if scheme is a secure protocol (dchubs, nmdcs, or adcs)"""
    return scheme in SUPPORTED_SCHEMAS_DC_SECURE or scheme in SUPPORTED_SCHEMAS_ADC_SECURE

def is_unsecure_protocol(scheme):
    """Check if scheme is an unsecure protocol (dchub, nmdc, or adc)"""
    return scheme in SUPPORTED_SCHEMAS_DC_UNSECURE or scheme in SUPPORTED_SCHEMAS_ADC_UNSECURE

def get_protocol_type(scheme):
    """Get protocol type ('dc' or 'adc') for a given scheme"""
    if scheme in PROTOCOLS:
        return PROTOCOLS[scheme]['type']
    return None

def is_protocol_secure(scheme):
    """Check if a specific protocol scheme is secure"""
    if scheme in PROTOCOLS:
        return PROTOCOLS[scheme]['secure']
    return False

# Hub attributes
HUB_ATTRIBUTES = (
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
    # useful for NMDC
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

##### FUNCTIONS #####

def indent(elem, level=0):
    """Pretty-print XML with indentation"""
    """from http://effbot.org/zone/element-lib.htm#prettyprint"""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def addr_complete(addr_hub):
    """Complete hub address with protocol and port if missing"""
    if "://" not in addr_hub:
        addr_hub = 'dchub://' + addr_hub

    url_info = urllib.parse.urlparse(addr_hub)
    if url_info.scheme == 'dchub' and not url_info.port:
        addr_hub = addr_hub + ':411'

    return addr_hub

def hub_addr_compare(addr_hub1, addr_hub2):
    """Compare two hub addresses (scheme, hostname and port)"""
    url1 = urllib.parse.urlparse(addr_hub1)
    url2 = urllib.parse.urlparse(addr_hub2)

    # Compare scheme
    if url1.scheme != url2.scheme:
        return False

    # Case-insensitive hostname comparison
    hostname1 = url1.hostname.lower() if url1.hostname else ''
    hostname2 = url2.hostname.lower() if url2.hostname else ''

    if hostname1 != hostname2:
        return False
    if url1.port != url2.port:
        return False
    return True

def duplicate_hub(hub1, hub2):
    """Check if two hubs are duplicates"""
    # Check addresses
    if hub_addr_compare(hub1.attrib['Address'], hub2.attrib['Address']):
        return True

    # Check failover addresses
    failover1 = hub1.attrib.get('Failover')
    failover2 = hub2.attrib.get('Failover')

    if failover1 and hub_addr_compare(failover1, hub2.attrib['Address']):
        return True
    if failover2 and hub_addr_compare(failover2, hub1.attrib['Address']):
        return True
    if failover1 and failover2 and hub_addr_compare(failover1, failover2):
        return True

    # Check name, description and encoding for NMDC hubs
    url1 = urllib.parse.urlparse(hub1.attrib['Address'])
    url2 = urllib.parse.urlparse(hub2.attrib['Address'])

    if is_dc_protocol(url1.scheme) and is_dc_protocol(url2.scheme):
        name1 = hub1.attrib.get('Name')
        name2 = hub2.attrib.get('Name')
        desc1 = hub1.attrib.get('Description')
        desc2 = hub2.attrib.get('Description')
        enc1 = hub1.attrib.get('Encoding')
        enc2 = hub2.attrib.get('Encoding')

        if name1 and name2 and desc1 and desc2 and enc1 and enc2:
            return name1 == name2 and desc1 == desc2 and enc1 == enc2

    return False

def priorize_hub(hub):
    """Determine hub priority for sorting"""
    scheme = urllib.parse.urlparse(hub.attrib['Address']).scheme

    if is_adc_protocol(scheme) and is_protocol_secure(scheme):
        if urllib.parse.urlparse(hub.attrib['Address']).query.startswith('kp='):
            return 1  # ADCS with key
        return 2      # ADCS
    elif is_adc_protocol(scheme) and not is_protocol_secure(scheme):
        return 3      # ADC
    elif is_dc_protocol(scheme) and is_protocol_secure(scheme):
        return 4      # DCHUBS/NMDCS
    elif is_dc_protocol(scheme) and not is_protocol_secure(scheme):
        return 5      # DCHUB/NMDC
    return 6          # Other

def hub_merge(hub1, hub2):
    """Merge attributes from hub2 into hub1 (missing attributes only)"""
    for att, _ in HUB_ATTRIBUTES:
        if att in hub2.attrib:
            if (hub1.attrib.get(att) is None or hub1.attrib.get(att) == '') and \
               hub2.attrib.get(att) is not None and hub2.attrib.get(att) != '':
                hub1.attrib[att] = hub2.attrib[att]
    return hub1

def download_with_retry(url, timeout, max_retries=3):
    """Download URL with retry logic"""
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'HublistAggregator/1.0'})
            response = urllib.request.urlopen(req, timeout=timeout)
            content = response.read()

            if url.endswith('.bz2'):
                content = bz2.decompress(content)

            return content
        except (urllib.error.URLError, socket.timeout, ConnectionError) as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  Retry {attempt + 1}/{max_retries} in {wait}s...")
                time.sleep(wait)
            else:
                print(f"  Failed after {max_retries} attempts: {e}")
                return None
        except bz2.BZ2Error as e:
            print(f"  BZ2 decompression error: {e}")
            return None

    return None

def ping_hub(hub, ping_tool, timeout):
    """Ping a single hub and return result"""
    hub_response = hub
    hub_to_keep = True

    try:
        cmd = [ping_tool, 'ping', hub.attrib['Address'],
               '--out=xml-line', '--hubs=2', '--slots=6', '--share=324882100000']

        if is_dc_protocol(urllib.parse.urlparse(hub.attrib['Address']).scheme):
            cmd.append('--encoding=' + hub.attrib['Encoding'])

        result = run(cmd, check=False, stdout=PIPE, stderr=PIPE, timeout=timeout)

        if result.returncode != 0:
            hub_response.attrib['Status'] = 'Offline'
            return hub_response, hub_to_keep  # Keep with offline status

        hub_response = ET.fromstring(result.stdout)
        hub_response.attrib['Address'] = addr_complete(hub_response.attrib['Address'])

        if hub_response.attrib.get('Status') == 'Error':
            if hub_response.attrib.get('ErrCode') == '226':
                return hub_response, False
            elif hub_response.attrib.get('Status') == 'Offline':
                return hub_response, False
            else:
                hub.attrib['Status'] = 'Offline'
                hub_response = hub
                return hub_response, hub_to_keep  # Keep with offline status

        return hub_response, hub_to_keep

    except Exception as e:
        print(f"  Ping error: {e}")
        hub.attrib['Status'] = 'Offline'
        return hub, hub_to_keep  # Keep with offline status

def process_hubs_concurrently(hubs, ping_tool, timeout, max_workers):
    """Process hubs with concurrent pings"""
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_hub = {
            executor.submit(ping_hub, hub, ping_tool, timeout): hub
            for hub in hubs
        }

        for future in concurrent.futures.as_completed(future_to_hub):
            hub = future_to_hub[future]
            try:
                hub_response, hub_to_keep = future.result()
                results.append((hub, hub_response, hub_to_keep))
            except Exception as e:
                print(f"Exception pinging hub {hub.attrib['Address']}: {e}")
                hub.attrib['Status'] = 'Offline'
                results.append((hub, hub, True))  # Keep with offline status

    return results

##### MAIN FUNCTION #####

def main():
    parser = argparse.ArgumentParser(description='Aggregate and clean DC++ hub lists')
    parser.add_argument('--ping-tool', help='Path to ping tool for hub verification')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT,
                       help=f'Network timeout in seconds (default: {DEFAULT_TIMEOUT})')
    parser.add_argument('--no-ping', action='store_true',
                       help='Skip hub verification even if ping tool is available')
    parser.add_argument('--output', default='hublist.xml',
                       help='Output XML file (default: hublist.xml)')
    parser.add_argument('--max-ping-workers', type=int, default=MAX_CONCURRENT_PINGS,
                       help=f'Maximum concurrent ping workers (default: {MAX_CONCURRENT_PINGS})')
    parser.add_argument('--ping-timeout', type=int, default=PING_TIMEOUT,
                       help=f'Ping timeout in seconds (default: {PING_TIMEOUT})')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')

    args = parser.parse_args()

    socket.setdefaulttimeout(args.timeout)

    print("=== Hublist Aggregator ===")
    print(f"Timeout: {args.timeout}s")
    if args.ping_tool and not args.no_ping:
        print(f"Ping tool: {args.ping_tool}")
        print(f"Ping workers: {args.max_ping_workers}")
        print(f"Ping timeout: {args.ping_timeout}s")
    else:
        print("Ping verification: Disabled")
    print()

    # Download hub lists
    print("Downloading hub lists...")
    xml_contents = []
    all_sources = [OWN_HUBLIST] + INTERNET_HUBLISTS

    for url in all_sources:
        print(f"  {url}")
        content = download_with_retry(url, args.timeout)
        if content:
            xml_contents.append(content)
            print("    ✓ Success")
        else:
            print("    ✗ Failed")

    # Load local files
    for local_file in LOCAL_HUBLISTS:
        print(f"  {local_file} (local)")
        try:
            if local_file.endswith('.bz2'):
                with bz2.BZ2File(local_file, 'rb') as f:
                    content = f.read()
            else:
                with open(local_file, 'rb') as f:
                    content = f.read()

            xml_contents.append(content)
            print("    ✓ Success")
        except Exception as e:
            print(f"    ✗ Error: {e}")

    if not xml_contents:
        print("Error: No hub lists could be loaded!")
        return 1

    # Parse and process hubs
    print(f"\nParsing {len(xml_contents)} hub lists...")
    all_hubs = []

    for content in xml_contents:
        try:
            root = ET.fromstring(content)
            for hub in root.iter('Hub'):
                if 'Address' not in hub.attrib:
                    continue

                hub.attrib['Address'] = addr_complete(hub.attrib['Address'])

                if hub.attrib.get('Failover'):
                    hub.attrib['Failover'] = addr_complete(hub.attrib['Failover'])

                scheme = urllib.parse.urlparse(hub.attrib['Address']).scheme

                if is_dc_protocol(scheme):
                    encoding = hub.attrib.get('Encoding', '').lower()
                    if encoding in SUPPORTED_ENCODING:
                        all_hubs.append(hub)
                    elif args.verbose:
                        print(f"  Skipping DC hub with unsupported encoding: {encoding}")
                elif is_adc_protocol(scheme):
                    hub.attrib['Encoding'] = 'UTF-8'
                    all_hubs.append(hub)
                elif args.verbose:
                    print(f"  Skipping hub with unsupported scheme: {scheme}")

        except ET.ParseError as e:
            print(f"  XML parse error: {e}")

    print(f"Found {len(all_hubs)} hubs total")

    # Sort by priority
    all_hubs.sort(key=priorize_hub)

    # First aggregate/merge duplicates to get unique hubs
    print("\nAggregating and merging duplicates...")
    unique_hubs = []
    hubs_to_process = list(all_hubs)  # Work on a copy

    while hubs_to_process:
        current_hub = hubs_to_process[0]

        # Find and merge all duplicates of this hub
        for other_hub in list(hubs_to_process):
            if other_hub != current_hub and duplicate_hub(other_hub, current_hub):
                current_hub = hub_merge(current_hub, other_hub)
                hubs_to_process.remove(other_hub)

        unique_hubs.append(current_hub)
        hubs_to_process.remove(current_hub)

    print(f"Aggregated to {len(unique_hubs)} unique hubs")

    # Ping hubs if requested
    clean_hubs = []

    if args.ping_tool and not args.no_ping:
        print(f"\nPinging {len(unique_hubs)} unique hubs...")
        hub_results = process_hubs_concurrently(
            unique_hubs, args.ping_tool, args.ping_timeout, args.max_ping_workers
        )

        # After pinging, we need to re-aggregate because:
        print("\nRe-aggregating after ping...")

        # Collect all ping results that should be kept
        pinged_hubs_to_keep = []
        removed_count = 0

        for _, processed_hub, hub_to_keep in hub_results:
            if hub_to_keep:
                pinged_hubs_to_keep.append(processed_hub)
            else:
                removed_count += 1

        final_hubs = []
        hubs_to_process = pinged_hubs_to_keep

        while hubs_to_process:
            current_hub = hubs_to_process[0]

            # Find and merge all duplicates of this hub
            for other_hub in list(hubs_to_process):
                if other_hub != current_hub and duplicate_hub(other_hub, current_hub):
                    current_hub = hub_merge(current_hub, other_hub)
                    hubs_to_process.remove(other_hub)

            final_hubs.append(current_hub)
            hubs_to_process.remove(current_hub)

        clean_hubs = final_hubs

        # Count online/offline
        online_count = 0
        offline_count = 0
        for hub in clean_hubs:
            if hub.attrib.get('Status') == 'Offline':
                offline_count += 1
            else:
                online_count += 1

        print(f"  Added to list: {online_count + offline_count} (Online: {online_count}, Offline: {offline_count})")
        print(f"  Removed: {removed_count}")
    else:
        # Process without pinging
        print("\nProcessing hubs (no ping verification)...")
        clean_hubs = unique_hubs
        print(f"  Processed: {len(clean_hubs)} hubs")

    print(f"\nFinal list: {len(clean_hubs)} unique hubs")

    # Generate output XML
    print(f"\nGenerating {args.output}...")
    root = ET.Element('Hublist',
                     Name='The DCNF Hublist',
                     Address='https://dcnf.github.io/Hublist/',
                     Generated=time.strftime('%Y-%m-%d %H:%M:%S'))

    hubs_elem = ET.SubElement(root, 'Hubs')
    cols_elem = ET.SubElement(hubs_elem, 'Columns')

    for name, type_ in HUB_ATTRIBUTES:
        ET.SubElement(cols_elem, 'Column', Name=name, Type=type_)

    for hub in clean_hubs:
        attribs = {}
        for name, _ in HUB_ATTRIBUTES:
            value = hub.attrib.get(name)
            attribs[name] = value if value is not None else ''
        ET.SubElement(hubs_elem, 'Hub', attribs)

    indent(root)
    tree = ET.ElementTree(root)
    tree.write(args.output, encoding='UTF-8', xml_declaration=True)

    # Create compressed version
    bz2_file = args.output + '.bz2'
    print(f"Generating {bz2_file}...")
    with open(args.output, 'rb') as f:
        compressed = bz2.compress(f.read(), 9)
    with open(bz2_file, 'wb') as f:
        f.write(compressed)

    print("\n=== Done ===")
    print(f"Output files: {args.output}, {bz2_file}")
    print(f"Total hubs: {len(clean_hubs)}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
