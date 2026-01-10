# Hublist

A Python script that aggregates, cleans, and verifies DC++ hub lists from multiple sources.

## Features

- **Multi-source aggregation**: Downloads hub lists from various online sources
- **Smart deduplication**: Identifies and merges duplicate hubs based on addresses, failovers, and metadata
- **Hub verification**: Optional ping verification using DCPing tool
- **Smart filtering**: Removes full hubs and explicitly offline hubs, keeps others with offline status
- **Concurrent processing**: Multi-threaded ping operations for faster verification
- **Output formats**: Generates both XML and compressed BZ2 versions
- **Configurable**: Command-line options for timeout, workers, output files, and more

## Installation

### Prerequisites

- Python 3.6 or higher
- DCPing tool (optional, for hub verification)

### DCPing Installation (Optional)

DCPing is required for hub verification. You can build it from source:

```bash
# Clone the repository
git clone https://github.com/direct-connect/go-dcpp.git
go build ./cmd/dcping
```

The script is compatible with DCPing version v0.26.0 or later.

## Usage

### Basic Usage (Without Verification)

```bash
python3 hublist.py
```

This will download hub lists, deduplicate entries, and generate `hublist.xml` and `hublist.xml.bz2` without ping verification.

### With Hub Verification

```bash
python3 hublist.py --ping-tool /path/to/dcping
```

### Command-line Options

```bash
python3 hublist.py --help
```

Available options:
- `--ping-tool PATH`: Path to DCPing executable for hub verification
- `--no-ping`: Skip hub verification even if ping tool is available
- `--timeout SECONDS`: Network timeout in seconds (default: 10)
- `--output FILE`: Output XML filename (default: hublist.xml)
- `--max-ping-workers NUM`: Maximum concurrent ping workers (default: 5)
- `--ping-timeout SECONDS`: Ping timeout per hub in seconds (default: 15)
- `--verbose, -v`: Enable verbose output
- `--help`: Show help message

## How It Works

### 1. Download Phase

The script downloads hub lists from configured sources.

### 2. Processing Phase

1. **Parsing**: Extracts hub information from XML/BZ2 files
2. **Normalization**: Completes missing protocols and ports
3. **Filtering**: Removes hubs with unsupported encodings or protocols
4. **Deduplication**: Identifies and merges duplicate hubs using:
   - Direct address comparison
   - Failover address matching
   - Name/Description/Encoding matching (for NMDC hubs)

### 3. Verification Phase (Optional)

If DCPing is provided:
- Pings each hub to verify online status
- **Removes full hubs** (ErrCode 226) and **explicitly offline hubs**
- **Keeps hubs with other errors** (timeout, network issues) with 'Offline' status
- Updates hub statistics (users, shared data, etc.)

### 4. Output Generation

Creates two files:
- `hublist.xml`: Clean, deduplicated hub list in XML format
- `hublist.xml.bz2`: Compressed version for efficient distribution

## Configuration

### Source Lists

Edit the following variables in `hublist.py`:

```python
OWN_HUBLIST = "https://dcnf.github.io/Hublist/ownDataHublist.xml"
INTERNET_HUBLISTS = [
    "https://www.te-home.net/?do=hublist&get=hublist.xml",
    "https://dchublist.org/hublist.xml.bz2",
    # ... more sources
]
LOCAL_HUBLISTS = []  # Add local file paths here
```

### Supported Protocols and Encodings

The script supports:
- **Protocols**: ADC, ADCS, DCHUB, DCHUBS, NMDC, NMDCS
- **NMDC Encodings**: UTF-8, CP1250-1257, GB18030

### Hub Attributes

The script processes these hub attributes:
- Address, Name, Description, Users, Country
- Shared, Minshare, Minslots, Maxhubs, Maxusers
- Reliability, Rating, Encoding, Software, Website
- Email, ASN, Operators, Bots, Infected, Status, Failover

## Which attribute is used in most-used DC clients?

- DC++: [dcpp/FavoriteManager.cpp#l322](https://sourceforge.net/p/dcplusplus/code/ci/66549d/tree/dcpp/FavoriteManager.cpp#l322)
- AirDC++: [modules/HublistManager.cpp#L58](https://github.com/airdcpp/airdcpp-windows/blob/c8e3dc4/airdcpp/airdcpp/modules/HublistManager.cpp#L58)
- EiskaltDC++: [dcpp/FavoriteManager.cpp#L255](https://github.com/eiskaltdcpp/eiskaltdcpp/blob/1d113ac/dcpp/FavoriteManager.cpp#L255)
- FlyLinkDC: [windows/PublicHubsFrm.cpp#L53](https://github.com/pavel-pimenov/flylinkdc-r6xx/blob/92da92a/windows/PublicHubsFrm.cpp#L53)

### Debug Mode

Use verbose output to see detailed processing:
```bash
python3 hublist.py --ping-tool ./dcping --verbose
```

## License

This project is licensed under the GPLv2 or later License - see the [LICENSE](LICENSE) file for details.
