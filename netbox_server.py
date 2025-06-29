from mcp.server.fastmcp import FastMCP
from netbox_client import NetBoxRestClient
from typing import Optional
import os

# MCP Server Initialization
mcp = FastMCP("NetBox", log_level="DEBUG")
netbox = None

# NetBox Object Type Mappings
NETBOX_OBJECT_TYPES = {
    # DCIM
    "cables": "dcim/cables",
    "console-ports": "dcim/console-ports",
    "console-server-ports": "dcim/console-server-ports",
    "devices": "dcim/devices",
    "device-bays": "dcim/device-bays",
    "device-roles": "dcim/device-roles",
    "device-types": "dcim/device-types",
    "front-ports": "dcim/front-ports",
    "interfaces": "dcim/interfaces",
    "inventory-items": "dcim/inventory-items",
    "locations": "dcim/locations",
    "manufacturers": "dcim/manufacturers",
    "modules": "dcim/modules",
    "module-bays": "dcim/module-bays",
    "module-types": "dcim/module-types",
    "platforms": "dcim/platforms",
    "power-feeds": "dcim/power-feeds",
    "power-outlets": "dcim/power-outlets",
    "power-panels": "dcim/power-panels",
    "power-ports": "dcim/power-ports",
    "racks": "dcim/racks",
    "rack-reservations": "dcim/rack-reservations",
    "rack-roles": "dcim/rack-roles",
    "regions": "dcim/regions",
    "sites": "dcim/sites",
    "site-groups": "dcim/site-groups",
    "virtual-chassis": "dcim/virtual-chassis",
    # IPAM
    "asns": "ipam/asns", "asn-ranges": "ipam/asn-ranges", "aggregates": "ipam/aggregates",
    "fhrp-groups": "ipam/fhrp-groups", "ip-addresses": "ipam/ip-addresses", "ip-ranges": "ipam/ip-ranges",
    "prefixes": "ipam/prefixes", "rirs": "ipam/rirs", "roles": "ipam/roles", "route-targets": "ipam/route-targets",
    "services": "ipam/services", "vlans": "ipam/vlans", "vlan-groups": "ipam/vlan-groups", "vrfs": "ipam/vrfs",
    # Circuits
    "circuits": "circuits/circuits", "circuit-types": "circuits/circuit-types",
    "circuit-terminations": "circuits/circuit-terminations", "providers": "circuits/providers",
    "provider-networks": "circuits/provider-networks",
    # Virtualization
    "clusters": "virtualization/clusters", "cluster-groups": "virtualization/cluster-groups",
    "cluster-types": "virtualization/cluster-types", "virtual-machines": "virtualization/virtual-machines",
    "vm-interfaces": "virtualization/interfaces",
    # Tenancy
    "tenants": "tenancy/tenants", "tenant-groups": "tenancy/tenant-groups", "contacts": "tenancy/contacts",
    "contact-groups": "tenancy/contact-groups", "contact-roles": "tenancy/contact-roles",
    # VPN
    "ike-policies": "vpn/ike-policies", "ike-proposals": "vpn/ike-proposals", "ipsec-policies": "vpn/ipsec-policies",
    "ipsec-profiles": "vpn/ipsec-profiles", "ipsec-proposals": "vpn/ipsec-proposals", "l2vpns": "vpn/l2vpns",
    "tunnels": "vpn/tunnels", "tunnel-groups": "vpn/tunnel-groups",
    # Wireless
    "wireless-lans": "wireless/wireless-lans", "wireless-lan-groups": "wireless/wireless-lan-groups",
    "wireless-links": "wireless/wireless-links",
    # Extras
    "config-contexts": "extras/config-contexts", "custom-fields": "extras/custom-fields", "export-templates": "extras/export-templates",
    "image-attachments": "extras/image-attachments", "jobs": "extras/jobs", "saved-filters": "extras/saved-filters",
    "scripts": "extras/scripts", "tags": "extras/tags", "webhooks": "extras/webhooks"
}

ALLOWED_FILTERS = {
    "racks": {"site", "status", "role", "tag", "q"},
    "devices": {"site", "rack", "role", "status", "manufacturer", "tag", "q"},
    "ip-addresses": {"address", "vrf", "status", "q"},
    "sites": {"name", "slug", "status", "region", "tag", "q"},
    # Add more as needed...
}

FRIENDLY_FILTERS = {
    "site_name": "site", "datacenter": "site", "rack_role": "role", "device_type": "type", "ip": "address", "search": "q",
    "site_slug": "slug", "datacenter_name": "name"
}

def normalize_object_type(obj_type: str) -> str:
    from difflib import get_close_matches
    if obj_type in NETBOX_OBJECT_TYPES:
        return obj_type
    plural_map = {"site": "sites", "rack": "racks", "device": "devices", "vlan": "vlans", "ip-address": "ip-addresses"}
    if obj_type in plural_map:
        return plural_map[obj_type]
    close = get_close_matches(obj_type, NETBOX_OBJECT_TYPES.keys(), n=1, cutoff=0.8)
    if close:
        return close[0]
    raise ValueError(f"Invalid object_type '{obj_type}'. Must be one of:\n" + "\n".join(sorted(NETBOX_OBJECT_TYPES.keys())))

def validate_and_map_filters(obj_type: str, filters: Optional[dict]) -> dict:
    allowed = ALLOWED_FILTERS.get(obj_type, set())
    if not filters:
        return {}
    result = {}
    for k, v in filters.items():
        api_key = FRIENDLY_FILTERS.get(k, k)
        if api_key in allowed:
            result[api_key] = v
        else:
            print(f"Warning: Ignoring unsupported filter '{k}' for {obj_type}")
    return result

@mcp.tool()
def netbox_get_objects(object_type: str, filters: Optional[dict] = None):
    normalized_type = normalize_object_type(object_type)
    endpoint = NETBOX_OBJECT_TYPES[normalized_type]
    validated_filters = validate_and_map_filters(normalized_type, filters)
    return netbox.get(endpoint, params=validated_filters)

@mcp.tool()
def netbox_get_object_by_id(object_type: str, object_id: int):
    normalized_type = normalize_object_type(object_type)
    endpoint = f"{NETBOX_OBJECT_TYPES[normalized_type]}/{object_id}"
    return netbox.get(endpoint)

@mcp.tool()
def netbox_get_changelogs(filters: dict):
    endpoint = "core/object-changes"
    return netbox.get(endpoint, params=filters)

if __name__ == "__main__":
    netbox_url = os.getenv("NETBOX_URL", "http://localhost:8000/")
    netbox_token = os.getenv("NETBOX_TOKEN", "4ab203e0949fd1bde910ad0a9bb4ac5784950cd2")
    if not netbox_url or not netbox_token:
        raise ValueError("NETBOX_URL and NETBOX_TOKEN must be set in environment or hardcoded.")
    netbox = NetBoxRestClient(url=netbox_url, token=netbox_token)
    mcp.run(transport="stdio")
