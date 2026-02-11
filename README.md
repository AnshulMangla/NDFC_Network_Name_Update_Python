# NDFC Network Management Tools

A collection of Python scripts to interact with Nexus Dashboard Fabric Controller (NDFC) REST APIs for network management tasks.

## What's Included

- **`ndfc_network_retriever.py`** - Retrieve network details by displayName
- **`ndfc_network_updater.py`** - Update network displayName 

## Quick Start

### 1. Setup Virtual Environment

```bash
# Navigate to project directory
cd NDFC-Change-Network-Name

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Edit the `.env` file with your NDFC details:

```env
# NDFC Connection Configuration
NDFC_HOST=https://your-ndfc-host
NDFC_USERNAME=your_username
NDFC_PASSWORD=your_password
NDFC_DOMAIN=your_domain
DEFAULT_FABRIC=your_fabric_name
SSL_VERIFY=false
```

### 3. Run the Scripts

#### Network Updater (Read + Write)
```bash
python3 ndfc_network_updater.py
```
- Prompts for current displayName to search
- Prompts for new displayName to update to
- Shows before and after details
- Confirms changes before applying

## Files

```
NDFC-Change-Network-Name/
├── .env                        # Environment configuration
├── requirements.txt            # Python dependencies
├── ndfc_network_updater.py     # Update displayName
├── venv/                       # Virtual environment
└── README.md                   # This file
```

## Requirements

- Python 3.7+
- NDFC access with API permissions
- Network connectivity to NDFC host

## Usage Examples

### Example: Update Network DisplayName
```bash
source venv/bin/activate
python3 ndfc_network_updater.py

# Input: 
#   Current: MyNetwork_30002
#   New: MyNetwork_Production
# Output: Updated network with new displayName
```

## API Endpoints Used

- **GET** `/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks`
- **PUT** `/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric}/networks/{networkName}`
- **POST** `/login` (for authentication)
