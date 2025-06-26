import asyncio
import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def build_openai_tools():
    common_object_types = [
        "aggregates", "asn-ranges", "asns", "cables", "circuit-terminations",
        "circuit-types", "circuits", "cluster-groups", "cluster-types", "clusters",
        "config-contexts", "console-ports", "console-server-ports", "contact-groups",
        "contact-roles", "contacts", "custom-fields", "device-bays", "device-roles",
        "device-types", "devices", "export-templates", "fhrp-groups", "front-ports",
        "ike-policies", "ike-proposals", "image-attachments", "interfaces", "inventory-items",
        "ip-addresses", "ip-ranges", "ipsec-policies", "ipsec-profiles", "ipsec-proposals",
        "jobs", "l2vpns", "locations", "manufacturers", "module-bays", "module-types",
        "modules", "platforms", "power-feeds", "power-outlets", "power-panels", "power-ports",
        "prefixes", "provider-networks", "providers", "rack-reservations", "rack-roles",
        "racks", "regions", "rirs", "roles", "route-targets", "saved-filters", "scripts",
        "services", "site-groups", "sites", "tags", "tenant-groups", "tenants", "tunnel-groups",
        "tunnels", "virtual-chassis", "virtual-machines", "vlan-groups", "vlans",
        "vm-interfaces", "vrfs", "webhooks", "wireless-lan-groups", "wireless-lans", "wireless-links"
    ]

    return [
        {
            "type": "function",
            "function": {
                "name": "netbox_get_objects",
                "description": "Retrieve NetBox objects by type and optional filters.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object_type": {
                            "type": "string",
                            "enum": common_object_types
                        },
                        "filters": {
                            "type": "object",
                            "description": "Optional key-value filters.",
                            "additionalProperties": {"type": ["string", "number", "boolean"]}
                        }
                    },
                    "required": ["object_type"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "netbox_get_object_by_id",
                "description": "Retrieve a specific NetBox object by its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object_type": {"type": "string"},
                        "id": {"type": "integer"}
                    },
                    "required": ["object_type", "id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "netbox_get_changelogs",
                "description": "Retrieve changelogs for a specific NetBox object by ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object_type": {"type": "string"},
                        "id": {"type": "integer"}
                    },
                    "required": ["object_type", "id"]
                }
            }
        }
    ]


async def main():
    load_dotenv()
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    tools = build_openai_tools()

    server_params = StdioServerParameters(command="python3", args=["netbox_server.py"])
    syracuse_filter_applied = False

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            messages = [{"role": "user", "content": "Tell me all about the DM-Syracuse datacenter."}]

            while True:
                response = await openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
                )

                tool_calls = response.choices[0].message.tool_calls
                if not tool_calls:
                    print("Final Assistant Response:\n", response.choices[0].message.content)
                    break

                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)

                    if (
                        function_name == "netbox_get_objects"
                        and args.get("object_type") == "sites"
                        and not args.get("filters")
                        and not syracuse_filter_applied
                    ):
                        args["filters"] = {"name": "DM-Syracuse"}
                        syracuse_filter_applied = True
                        print("Applying site name filter for DM-Syracuse")

                    result = await session.call_tool(function_name, arguments=args)
                    print(f"Raw tool call result: {result}")

                    if not result.content:
                        print(f"\n🔹 Executed {function_name} with args {args}\n🔸 Result: (no content returned)")
                        print("❌ No results found. Ending conversation to prevent infinite loop.")
                        return

                    print(f"\n🔹 Executed {function_name} with args {args}\n🔸 Result: {result.content[0].text}")
                    messages.append({"role": "assistant", "content": None, "tool_calls": [tool_call]})
                    messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result.content[0].text})


if __name__ == "__main__":
    asyncio.run(main())
