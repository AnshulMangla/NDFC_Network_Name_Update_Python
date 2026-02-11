#!/usr/bin/env python3
"""
NDFC Network Display Name Updater
A Python script to connect to Nexus Dashboard Fabric Controller (NDFC) via REST API,
retrieve network details based on displayName, and update the displayName.

"""

import requests
import json
import urllib3
import sys
import os
from typing import Dict, List, Optional
from getpass import getpass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class NDFCClient:
    """NDFC REST API Client"""
    
    def __init__(self, host: str, username: str, password: str, verify_ssl: bool = False):
        """
        Initialize NDFC client
        
        Args:
            host: NDFC host/IP address
            username: Username for authentication
            password: Password for authentication
            verify_ssl: Whether to verify SSL certificates
        """
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.token = None
        
        # Set up session with basic configuration
        self.session.verify = verify_ssl
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def authenticate(self) -> bool:
        """
        Authenticate with NDFC using domain-based login
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            # NDFC domain-based authentication endpoint
            login_url = f"{self.host}/login"
            
            # Get domain from environment
            domain = os.getenv('NDFC_DOMAIN', 'local')
            
            # Prepare login payload
            login_data = {
                "userName": self.username,
                "userPasswd": self.password,
                "domain": domain
            }
            
            print(f"🔐 Authenticating with domain: {domain}")
            
            # Perform login
            response = self.session.post(login_url, json=login_data, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract token if provided
                if 'token' in response_data:
                    self.token = response_data['token']
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.token}'
                    })
                elif 'jwttoken' in response_data:
                    self.token = response_data['jwttoken']
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.token}'
                    })
                
                print("Authentication successful")
                return True
            else:
                print(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Authentication error: {str(e)}")
            return False
    
    def get_all_networks(self, fabric_name: str) -> Optional[List[Dict]]:
        """
        Get all networks for a specific fabric
        
        Args:
            fabric_name: Name of the fabric
            
        Returns:
            List of network dictionaries or None if error
        """
        try:
            url = f"{self.host}/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/networks"
            
            print(f"🔍 Retrieving all networks from fabric: {fabric_name}")
            print(f"📡 API Endpoint: {url}")
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                networks = response.json()
                print(f"Successfully retrieved {len(networks)} networks")
                return networks
            else:
                print(f"Failed to retrieve networks: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Network retrieval error: {str(e)}")
            return None
    
    def find_network_by_display_name(self, fabric_name: str, display_name: str) -> Optional[Dict]:
        """
        Find a network by its displayName
        
        Args:
            fabric_name: Name of the fabric
            display_name: Display name to search for
            
        Returns:
            Network dictionary or None if not found
        """
        networks = self.get_all_networks(fabric_name)
        
        if networks is None:
            return None
        
        print(f"🔎 Searching for network with displayName: '{display_name}'")
        
        for network in networks:
            if network.get('displayName') == display_name:
                print(f"Found matching network: {network.get('networkName')}")
                return network
        
        print(f"No network found with displayName: '{display_name}'")
        print(f"📋 Available networks:")
        for network in networks:
            print(f"   - {network.get('displayName', 'N/A')} (networkName: {network.get('networkName', 'N/A')})")
        
        return None
    
    def update_network_display_name(self, fabric_name: str, network: Dict, new_display_name: str) -> bool:
        """
        Update the displayName of a network
        
        Args:
            fabric_name: Name of the fabric
            network: Original network dictionary from GET call
            new_display_name: New display name to set
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            network_name = network.get('networkName')
            if not network_name:
                print("NetworkName not found in network data")
                return False
            
            # Construct PUT API URL
            url = f"{self.host}/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/networks/{network_name}"
            
            print(f"🔄 Updating network display name...")
            print(f"📡 PUT Endpoint: {url}")
            print(f"🏷️  Old Display Name: {network.get('displayName', 'N/A')}")
            print(f"🏷️  New Display Name: {new_display_name}")
            
            # Create payload by copying original network data and updating displayName
            payload = network.copy()
            payload['displayName'] = new_display_name
            
            # Clean up the payload - remove any fields that shouldn't be in PUT
            fields_to_keep = [
                'id', 'fabric', 'networkName', 'displayName', 'networkId',
                'networkTemplate', 'networkExtensionTemplate', 'networkTemplateConfig',
                'vrf', 'tenantName', 'serviceNetworkTemplate', 'source',
                'interfaceGroups', 'primaryNetworkId', 'type', 'primaryNetworkName',
                'vlanId', 'vlanName', 'hierarchicalKey'
            ]
            
            # Create clean payload with only required fields
            clean_payload = {key: payload.get(key) for key in fields_to_keep if key in payload}
            
            # Ensure networkStatus is not included (it's read-only)
            if 'networkStatus' in clean_payload:
                del clean_payload['networkStatus']
            
            # Perform PUT request
            response = self.session.put(url, json=clean_payload, timeout=30)
            
            if response.status_code in [200, 201, 202]:
                print("Network display name updated successfully!")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        print(f"📊 Updated Network ID: {response_data.get('id', 'N/A')}")
                        print(f"🏷️  Confirmed Display Name: {response_data.get('displayName', 'N/A')}")
                except:
                    print("Update confirmed (response parsing skipped)")
                return True
            else:
                print(f"Failed to update network: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Network update error: {str(e)}")
            return False
    
    def display_network_details(self, network: Dict) -> None:
        """
        Display network details in a formatted way
        
        Args:
            network: Network dictionary
        """
        print("\n" + "="*60)
        print("NETWORK DETAILS")
        print("="*60)
        
        # Main network information
        print(f"Network Name: {network.get('networkName', 'N/A')}")
        print(f"Display Name: {network.get('displayName', 'N/A')}")
        print(f"Network ID: {network.get('networkId', 'N/A')}")
        print(f"Fabric: {network.get('fabric', 'N/A')}")
        print(f"Type: {network.get('type', 'N/A')}")
        print(f"Status: {network.get('networkStatus', 'N/A')}")
        print(f"VRF: {network.get('vrf', 'N/A')}")
        print(f"Tenant: {network.get('tenantName', 'N/A')}")
        
        # Template information
        print(f"\n Template Information:")
        print(f"   Network Template: {network.get('networkTemplate', 'N/A')}")
        print(f"   Extension Template: {network.get('networkExtensionTemplate', 'N/A')}")
        
        # Parse network template configuration if available
        if network.get('networkTemplateConfig'):
            try:
                config = json.loads(network.get('networkTemplateConfig', '{}'))
                print(f"\n  Network Configuration:")
                key_configs = {
                    'vlanId': 'VLAN ID',
                    'segmentId': 'Segment ID',
                    'mcastGroup': 'Multicast Group',
                    'gatewayIpAddress': 'Gateway IP',
                    'mtu': 'MTU',
                    'tag': 'Tag',
                    'enableIR': 'Enable IR',
                    'isLayer2Only': 'Layer 2 Only'
                }
                
                for key, label in key_configs.items():
                    value = config.get(key, '')
                    if value:
                        print(f"   {label}: {value}")
                        
            except json.JSONDecodeError:
                print("    Unable to parse network template configuration")
        
        print("\n" + "="*60)
    
    def close(self):
        """Close the session"""
        if self.session:
            self.session.close()


def get_user_input() -> tuple:
    """Get user input for connection parameters"""
    print("🔧 NDFC Network Display Name Updater")
    print("="*50)
    
    # Load from environment variables
    host = os.getenv('NDFC_HOST')
    username = os.getenv('NDFC_USERNAME')
    password = os.getenv('NDFC_PASSWORD')
    fabric_name = os.getenv('DEFAULT_FABRIC')
    domain = os.getenv('NDFC_DOMAIN', 'local')
    
    # Validate required environment variables
    if not host:
        print("NDFC_HOST not found in .env file")
        host = input("Enter NDFC Host/IP (e.g., https://10.107.70.70): ").strip()
    else:
        print(f"🌐 Using NDFC Host: {host}")
    
    if not fabric_name:
        print("DEFAULT_FABRIC not found in .env file")
        fabric_name = input("Enter Fabric Name (e.g., PeterTest): ").strip()
    else:
        print(f"Using Fabric: {fabric_name}")
    
    if not username:
        print("NDFC_USERNAME not found in .env file")
        username = input("Enter Username: ").strip()
    else:
        print(f"👤 Using Username: {username}")
    
    if not password:
        print("NDFC_PASSWORD not found in .env file")
        password = getpass("Enter Password: ")
    else:
        print("Using password from .env file")
    
    print(f"🏢 Using Login Domain: {domain}")
    
    if not host.startswith(('http://', 'https://')):
        host = f"https://{host}"
    
    # Get current and new display names
    current_display_name = input("\n🔍 Enter CURRENT Network Display Name to search: ").strip()
    
    print("\n" + "="*50)
    print("🔄 UPDATE CONFIGURATION")
    print("="*50)
    
    new_display_name = input("🏷️  Enter NEW Display Name (or press Enter to skip update): ").strip()
    
    return host, fabric_name, current_display_name, new_display_name, username, password


def main():
    """Main function"""
    try:
        # Get user input
        host, fabric_name, current_display_name, new_display_name, username, password = get_user_input()
        
        if not all([host, fabric_name, current_display_name, username, password]):
            print("Required fields missing!")
            return 1
        
        # Initialize NDFC client
        print(f"\n🔌 Connecting to NDFC at {host}")
        client = NDFCClient(host, username, password, verify_ssl=False)
        
        # Authenticate
        if not client.authenticate():
            return 1
        
        # Find network by current display name
        network = client.find_network_by_display_name(fabric_name, current_display_name)
        
        if not network:
            print("\nNetwork not found!")
            return 1
        
        # Display current network details
        client.display_network_details(network)
        
        # Update display name if new one provided
        if new_display_name and new_display_name != current_display_name:
            print(f"\n🔄 Proceeding with display name update...")
            
            # Confirm the update
            confirm = input(f"\nConfirm update from '{current_display_name}' to '{new_display_name}'? (y/n): ").lower()
            
            if confirm in ['y', 'yes']:
                if client.update_network_display_name(fabric_name, network, new_display_name):
                    print("\nNetwork display name updated successfully!")
                    
                    # Fetch and display updated network details
                    print("\n🔍 Fetching updated network details...")
                    updated_network = client.find_network_by_display_name(fabric_name, new_display_name)
                    if updated_network:
                        print("\n" + "="*60)
                        print("UPDATED NETWORK DETAILS")
                        print("="*60)
                        client.display_network_details(updated_network)
                    
                    # Option to save to file
                    save_option = input("\n Save updated network details to JSON file? (y/n): ").lower()
                    if save_option in ['y', 'yes']:
                        filename = f"network_{new_display_name.replace(' ', '_')}_updated.json"
                        with open(filename, 'w') as f:
                            json.dump(updated_network or network, f, indent=2)
                        print(f" Updated network details saved to: {filename}")
                else:
                    print("\n Failed to update network display name!")
                    return 1
            else:
                print("\n  Update cancelled by user")
        
        elif new_display_name == current_display_name:
            print("\n  New display name is same as current - no update needed")
        
        else:
            print("\n📋 No new display name provided - showing current details only")
            
            # Option to save current details to file
            save_option = input("\n Save current network details to JSON file? (y/n): ").lower()
            if save_option in ['y', 'yes']:
                filename = f"network_{current_display_name.replace(' ', '_')}.json"
                with open(filename, 'w') as f:
                    json.dump(network, f, indent=2)
                print(f"Network details saved to: {filename}")
            
    except KeyboardInterrupt:
        print("\n\n  Operation cancelled by user")
        return 1
    
    except Exception as e:
        print(f"\n Unexpected error: {str(e)}")
        return 1
    
    finally:
        if 'client' in locals():
            client.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
