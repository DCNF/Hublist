#!/usr/bin/python3
# -*- coding: utf-8 -*-

import bz2
import logging
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

INTERNAL_HUBLIST = "https://dcnf.github.io/Hublist/hublist.xml.bz2"

EXTERNAL_HUBLISTS = [
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
SUPPORTED_ENCODING = {'utf-8', 'cp1250', 'cp1251', 'cp1252', 'cp1253', 'cp1254', 'cp1256', 'cp1257', 'gb18030'}

# Status constants
STATUS_OFFLINE = 'Offline'
STATUS_ERROR = 'Error'
ENCODING_UTF8 = 'UTF-8'

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
def is_dc_protocol(scheme: str) -> bool:
    """Check if scheme is a DC protocol (dchub, dchubs, nmdc, or nmdcs)"""
    return scheme in SUPPORTED_SCHEMAS_DC

def is_adc_protocol(scheme: str) -> bool:
    """Check if scheme is an ADC protocol (adc or adcs)"""
    return scheme in SUPPORTED_SCHEMAS_ADC

def is_secure_protocol(scheme: str) -> bool:
    """Check if scheme is a secure protocol (dchubs, nmdcs, or adcs)"""
    return PROTOCOLS.get(scheme, {}).get('secure', False)

def get_protocol_type(scheme: str) -> str | None:
    """Get protocol type ('dc' or 'adc') for a given scheme"""
    return PROTOCOLS.get(scheme, {}).get('type')

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

def indent(elem: ET.Element, level: int = 0) -> None:
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

def addr_complete(addr_hub: str) -> str:
    """Complete hub address with protocol and port if missing"""
    if "://" not in addr_hub:
        addr_hub = 'dchub://' + addr_hub

    url_info = urllib.parse.urlparse(addr_hub)
    if url_info.scheme == 'dchub' and not url_info.port:
        addr_hub = addr_hub + ':411'

    return addr_hub

def hub_addr_compare(addr_hub1: str, addr_hub2: str) -> bool:
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

def duplicate_hub(hub1: ET.Element, hub2: ET.Element) -> bool:
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

def prioritize_hub(hub: ET.Element) -> int:
    """Determine hub priority for sorting"""
    scheme = urllib.parse.urlparse(hub.attrib['Address']).scheme

    if is_adc_protocol(scheme) and is_secure_protocol(scheme):
        if urllib.parse.urlparse(hub.attrib['Address']).query.startswith('kp='):
            return 1  # ADCS with key
        return 2      # ADCS
    elif is_adc_protocol(scheme):
        return 3      # ADC
    elif is_dc_protocol(scheme) and is_secure_protocol(scheme):
        return 4      # DCHUBS/NMDCS
    elif is_dc_protocol(scheme):
        return 5      # DCHUB/NMDC
    return 6          # Other

def hub_merge(hub1: ET.Element, hub2: ET.Element, failover_map: dict) -> ET.Element:
    """Merge attributes from hub2 into hub1 (missing attributes only) and accumulate failovers"""
    addr = hub1.attrib['Address']

    # Upgrade _source: own > external > internal
    source_rank = {'own': 0, 'external': 1, 'internal': 2}
    src1 = hub1.attrib.get('_source', '')
    src2 = hub2.attrib.get('_source', '')
    if source_rank.get(src2, 99) < source_rank.get(src1, 99):
        hub1.attrib['_source'] = src2

    # Collect failovers from both hubs into failover_map
    for h in [hub1, hub2]:
        fo = h.attrib.get('Failover')
        if fo and fo not in failover_map.get(addr, []):
            failover_map.setdefault(addr, []).append(fo)

    # Merge other attributes (skip Failover, handled via failover_map)
    # Data priority: internal > external/own
    data_rank = {'internal': 0, 'external': 1, 'own': 1}
    for att, _ in HUB_ATTRIBUTES:
        if att == 'Failover':
            continue
        if att in hub2.attrib:
            val2 = hub2.attrib.get(att)
            if val2 in (None, ''):
                continue
            val1 = hub1.attrib.get(att)
            if val1 in (None, '') or data_rank.get(src2, 99) < data_rank.get(src1, 99):
                hub1.attrib[att] = val2
    return hub1

def download_with_retry(url: str, timeout: int, max_retries: int = 3) -> bytes | None:
    """Download URL with retry logic"""
    logger = logging.getLogger(__name__)
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
                logger.info("  Retry %d/%d in %ds...", attempt + 1, max_retries, wait)
                time.sleep(wait)
            else:
                logger.error("  Failed after %d attempts: %s", max_retries, e)
                return None
        except bz2.BZ2Error as e:
            logger.error("  BZ2 decompression error: %s", e)
            return None

    return None

def ping_hub(hub: ET.Element, ping_tool: str, timeout: int) -> tuple[ET.Element, bool]:
    """Ping a single hub and return result"""
    logger = logging.getLogger(__name__)
    hub_response = hub
    hub_to_keep = True

    try:
        cmd = [ping_tool, 'ping', hub.attrib['Address'],
               '--out=xml-line', '--hubs=2', '--slots=6', '--share=324882100000']

        if is_dc_protocol(urllib.parse.urlparse(hub.attrib['Address']).scheme):
            cmd.append('--encoding=' + hub.attrib['Encoding'])

        result = run(cmd, check=False, stdout=PIPE, stderr=PIPE, timeout=timeout)

        if result.returncode != 0:
            hub_response.attrib['Status'] = STATUS_OFFLINE
            return hub_response, hub_to_keep  # Keep with offline status

        hub_response = ET.fromstring(result.stdout)
        hub_response.attrib['Address'] = addr_complete(hub_response.attrib['Address'])
        hub_response.attrib['_source'] = hub.attrib.get('_source', '')
        if hub_response.attrib.get('Failover'):
            hub_response.attrib['Failover'] = addr_complete(hub_response.attrib['Failover'])

        if hub_response.attrib.get('Status') == STATUS_ERROR:
            if hub_response.attrib.get('ErrCode') == '226':
                return hub_response, False
            else:
                hub.attrib['Status'] = STATUS_OFFLINE
                hub_response = hub
                return hub_response, hub_to_keep  # Keep with offline status

        return hub_response, hub_to_keep

    except Exception as e:
        logger.error("  Ping error: %s", e)
        hub.attrib['Status'] = STATUS_OFFLINE
        return hub, hub_to_keep  # Keep with offline status

def process_hubs_concurrently(hubs: list[ET.Element], ping_tool: str, timeout: int, max_workers: int) -> list[tuple]:
    """Process hubs with concurrent pings"""
    logger = logging.getLogger(__name__)
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
                logger.error("Exception pinging hub %s: %s", hub.attrib['Address'], e)
                hub.attrib['Status'] = STATUS_OFFLINE
                results.append((hub, hub, True))  # Keep with offline status

    return results

##### MAIN FUNCTION #####

def main() -> int:
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

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(message)s'
    )
    logger = logging.getLogger(__name__)

    socket.setdefaulttimeout(args.timeout)

    logger.info("=== Hublist Aggregator ===")
    logger.info("Timeout: %ds", args.timeout)
    if args.ping_tool and not args.no_ping:
        logger.info("Ping tool: %s", args.ping_tool)
        logger.info("Ping workers: %d", args.max_ping_workers)
        logger.info("Ping timeout: %ds", args.ping_timeout)
    else:
        logger.info("Ping verification: Disabled")
    logger.info("")

    # Download hub lists
    logger.info("Downloading hub lists...")
    xml_contents = []

    # Build source list with tags
    sources = []
    sources.append((OWN_HUBLIST, 'own'))
    sources.append((INTERNAL_HUBLIST, 'internal'))
    for url in EXTERNAL_HUBLISTS:
        sources.append((url, 'external'))

    for url, source_tag in sources:
        logger.info("  %s", url)
        content = download_with_retry(url, args.timeout)
        if content:
            xml_contents.append((content, source_tag))
            logger.info("    Success")
        else:
            logger.info("    Failed")

    # Load local files
    for local_file in LOCAL_HUBLISTS:
        logger.info("  %s (local)", local_file)
        try:
            if local_file.endswith('.bz2'):
                with bz2.BZ2File(local_file, 'rb') as f:
                    content = f.read()
            else:
                with open(local_file, 'rb') as f:
                    content = f.read()

            xml_contents.append((content, 'external'))
            logger.info("    Success")
        except Exception as e:
            logger.error("    Error: %s", e)

    if not xml_contents:
        logger.error("Error: No hub lists could be loaded!")
        return 1

    # Parse and process hubs
    logger.info("\nParsing %d hub lists...", len(xml_contents))
    all_hubs = []
    failover_map = {}
    prev_offline_addresses = set()

    for content, source_tag in xml_contents:
        try:
            root = ET.fromstring(content)
            for hub in root.iter('Hub'):
                if 'Address' not in hub.attrib:
                    continue

                hub.attrib['Address'] = addr_complete(hub.attrib['Address'])

                if hub.attrib.get('Failover'):
                    hub.attrib['Failover'] = addr_complete(hub.attrib['Failover'])

                # Tag source
                hub.attrib['_source'] = source_tag

                # Track failovers in failover_map
                fo = hub.attrib.get('Failover')
                if fo:
                    failover_map.setdefault(hub.attrib['Address'], []).append(fo)

                # Mark hubs offline from previous session
                if source_tag == 'internal' and hub.attrib.get('Status') == STATUS_OFFLINE:
                    prev_offline_addresses.add(hub.attrib['Address'].lower())
                    if fo:
                        prev_offline_addresses.add(fo.lower())

                scheme = urllib.parse.urlparse(hub.attrib['Address']).scheme

                if is_dc_protocol(scheme):
                    encoding = hub.attrib.get('Encoding', '').lower()
                    if encoding in SUPPORTED_ENCODING:
                        all_hubs.append(hub)
                    elif args.verbose:
                        logger.debug("  Skipping DC hub with unsupported encoding: %s", encoding)
                elif is_adc_protocol(scheme):
                    hub.attrib['Encoding'] = ENCODING_UTF8
                    all_hubs.append(hub)
                elif args.verbose:
                    logger.debug("  Skipping hub with unsupported scheme: %s", scheme)

        except ET.ParseError as e:
            logger.error("  XML parse error: %s", e)

    logger.info("Found %d hubs total", len(all_hubs))

    # Sort by priority
    all_hubs.sort(key=prioritize_hub)

    # First aggregate/merge duplicates to get unique hubs
    logger.info("\nAggregating and merging duplicates...")
    unique_hubs = []
    hubs_to_process = list(all_hubs)  # Work on a copy

    while hubs_to_process:
        current_hub = hubs_to_process[0]

        # Find and merge all duplicates of this hub
        for other_hub in list(hubs_to_process):
            if other_hub != current_hub and duplicate_hub(other_hub, current_hub):
                current_hub = hub_merge(current_hub, other_hub, failover_map)
                hubs_to_process.remove(other_hub)

        unique_hubs.append(current_hub)
        hubs_to_process.remove(current_hub)

    logger.info("Aggregated to %d unique hubs", len(unique_hubs))

    # Ping hubs if requested
    clean_hubs = []

    if args.ping_tool and not args.no_ping:
        logger.info("\nPinging %d unique hubs...", len(unique_hubs))
        hub_results = process_hubs_concurrently(
            unique_hubs, args.ping_tool, args.ping_timeout, args.max_ping_workers
        )

        logger.info("\nRe-aggregating after ping...")

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
                    current_hub = hub_merge(current_hub, other_hub, failover_map)
                    hubs_to_process.remove(other_hub)

            final_hubs.append(current_hub)
            hubs_to_process.remove(current_hub)

        # Build known_addresses from external, own, and local hubs
        known_addresses = set()
        for hub in final_hubs:
            if hub.attrib.get('_source') in ('external', 'own'):
                known_addresses.add(hub.attrib['Address'].lower())
                for fo in failover_map.get(hub.attrib['Address'], []):
                    known_addresses.add(fo.lower())

        # Filter: internal hubs offline in both sessions and not referenced by other sources
        clean_hubs = []
        for hub in final_hubs:
            is_offline = hub.attrib.get('Status') == STATUS_OFFLINE
            if is_offline:
                addr = hub.attrib['Address'].lower()
                failover = hub.attrib.get('Failover', '').lower()
                was_offline_prev = (addr in prev_offline_addresses or
                                   failover in prev_offline_addresses)
                is_known = (addr in known_addresses or
                            failover in known_addresses)
                if was_offline_prev and not is_known:
                    continue
            clean_hubs.append(hub)

        # Count online/offline
        online_count = sum(1 for h in clean_hubs if h.attrib.get('Status') != STATUS_OFFLINE)
        offline_count = len(clean_hubs) - online_count

        logger.info("  Added to list: %d (Online: %d, Offline: %d)", online_count + offline_count, online_count, offline_count)
        logger.info("  Removed: %d", removed_count + (len(final_hubs) - len(clean_hubs)))
    else:
        # Process without pinging
        logger.info("\nProcessing hubs (no ping verification)...")
        clean_hubs = unique_hubs
        logger.info("  Processed: %d hubs", len(clean_hubs))

    logger.info("\nFinal list: %d unique hubs", len(clean_hubs))

    # Generate output XML
    logger.info("\nGenerating %s...", args.output)
    root = ET.Element('Hublist',
                     Name='The DCNF Hublist',
                     Address='https://dcnf.github.io/Hublist/',
                     Generated=time.strftime('%Y-%m-%d %H:%M:%S'))

    hubs_elem = ET.SubElement(root, 'Hubs')
    cols_elem = ET.SubElement(hubs_elem, 'Columns')

    for name, type_ in HUB_ATTRIBUTES:
        ET.SubElement(cols_elem, 'Column', Name=name, Type=type_)

    for hub in clean_hubs:
        # Use first failover from failover_map if available
        failovers = failover_map.get(hub.attrib['Address'], [])
        if failovers:
            hub.attrib['Failover'] = failovers[0]

        # Remove internal attributes
        hub.attrib.pop('_source', None)

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
    logger.info("Generating %s...", bz2_file)
    with open(args.output, 'rb') as f:
        compressed = bz2.compress(f.read(), 9)
    with open(bz2_file, 'wb') as f:
        f.write(compressed)

    logger.info("\n=== Done ===")
    logger.info("Output files: %s, %s", args.output, bz2_file)
    logger.info("Total hubs: %d", len(clean_hubs))

    return 0

if __name__ == "__main__":
    sys.exit(main())
