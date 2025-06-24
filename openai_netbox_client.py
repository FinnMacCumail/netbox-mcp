import asyncio
from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json
import os
from dotenv import load_dotenv

async def main():
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_client = AsyncOpenAI(api_key=openai_api_key)

    # Define MCP server parameters (matches your client-studio snippet)
    server_params = StdioServerParameters(
        command="python3",
        args=["netbox_server.py"]
    )

    # Connect to the server
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Register OpenAI tools
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "netbox_get_objects",
                        "description": (
                            "Retrieve NetBox objects by type and optional filters.\n\n"
                            "Valid object_type values are:\n"
                            "- aggregates\n"
                            "- asn-ranges\n"
                            "- asns\n"
                            "- cables\n"
                            "- circuit-terminations\n"
                            "- circuit-types\n"
                            "- circuits\n"
                            "- cluster-groups\n"
                            "- cluster-types\n"
                            "- clusters\n"
                            "- config-contexts\n"
                            "- console-ports\n"
                            "- console-server-ports\n"
                            "- contact-groups\n"
                            "- contact-roles\n"
                            "- contacts\n"
                            "- custom-fields\n"
                            "- device-bays\n"
                            "- device-roles\n"
                            "- device-types\n"
                            "- devices\n"
                            "- export-templates\n"
                            "- fhrp-groups\n"
                            "- front-ports\n"
                            "- ike-policies\n"
                            "- ike-proposals\n"
                            "- image-attachments\n"
                            "- interfaces\n"
                            "- inventory-items\n"
                            "- ip-addresses\n"
                            "- ip-ranges\n"
                            "- ipsec-policies\n"
                            "- ipsec-profiles\n"
                            "- ipsec-proposals\n"
                            "- jobs\n"
                            "- l2vpns\n"
                            "- locations\n"
                            "- manufacturers\n"
                            "- module-bays\n"
                            "- module-types\n"
                            "- modules\n"
                            "- platforms\n"
                            "- power-feeds\n"
                            "- power-outlets\n"
                            "- power-panels\n"
                            "- power-ports\n"
                            "- prefixes\n"
                            "- provider-networks\n"
                            "- providers\n"
                            "- rack-reservations\n"
                            "- rack-roles\n"
                            "- racks\n"
                            "- regions\n"
                            "- rirs\n"
                            "- roles\n"
                            "- route-targets\n"
                            "- saved-filters\n"
                            "- scripts\n"
                            "- services\n"
                            "- site-groups\n"
                            "- sites\n"
                            "- tags\n"
                            "- tenant-groups\n"
                            "- tenants\n"
                            "- tunnel-groups\n"
                            "- tunnels\n"
                            "- virtual-chassis\n"
                            "- virtual-machines\n"
                            "- vlan-groups\n"
                            "- vlans\n"
                            "- vm-interfaces\n"
                            "- vrfs\n"
                            "- webhooks\n"
                            "- wireless-lan-groups\n"
                            "- wireless-lans\n"
                            "- wireless-links\n\n"
                            "Optional filters can be applied as key-value pairs (e.g., site, status, role)."
                        ),
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "object_type": {
                                    "type": "string",
                                    "enum": [
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
                        "description": "Retrieve a specific NetBox object by its ID (e.g., a site, device, or rack).",
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


            messages = [{"role": "user", "content": "Tell me all about the Syracuse datacenter."}]

            # First OpenAI call with available tools
            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )

            # Process tool calls dynamically
            while True:
                tool_calls = response.choices[0].message.tool_calls
                if not tool_calls:
                    print("Final Assistant Response:\n", response.choices[0].message.content)
                    break

                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)

                    result = await session.call_tool(function_name, arguments=args)
                    print(f"\n🔹 Executed {function_name} with args {args}\n🔸 Result: {result.content[0].text}")

                    # Append result text (extracted from content) to messages
                    messages.append({"role": "assistant", "content": None, "tool_calls": [tool_call]})
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result.content[0].text
                    })


                # Next OpenAI call with updated conversation context
                response = await openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
                )

if __name__ == "__main__":
    asyncio.run(main())
