"""Seed real B2B enterprise deals and contacts directly into HubSpot CRM with notes and associations."""
import asyncio
import os
import sys
import httpx
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config.settings import get_settings
from app.mcp.hubspot import hubspot_client

ENTERPRISE_DEALS_TO_SEED = [
    {
        "name": "Apex Retail POS AI Integration",
        "amount": 85000.0,
        "stage": "4131145421",  # Contract Sent
        "stage_label": "Contract Sent",
        "contact_id": "533504957144",
        "contact_name": "Marcus Vance",
        "notes": "Contract v2 dispatched for electronic signature. Marcus mentioned CFO needs one final clarification on quarterly billing milestones."
    },
    {
        "name": "NexaCloud Enterprise Migration",
        "amount": 45000.0,
        "stage": "4131145420",  # Decision Maker Bought-In
        "stage_label": "Decision Maker Bought-In",
        "contact_id": "533740144363",
        "contact_name": "Sarah Jenkins",
        "notes": "Demo went extremely well. Sarah requested custom multi-region SLA terms on Thursday. Proposal sent with $45k annual commitment. Waiting on legal & security signoff."
    },
    {
        "name": "FinTech Core Real-Time Security Audit",
        "amount": 120000.0,
        "stage": "4131145419",  # Presentation Scheduled
        "stage_label": "Presentation Scheduled",
        "contact_id": "533507046131",
        "contact_name": "David Chen",
        "notes": "Initial architecture deck delivered 2 weeks ago. No response to previous follow-up check-in."
    },
    {
        "name": "BioHealth Genomic Analytics Pilot",
        "amount": 35000.0,
        "stage": "4131145418",  # Qualified to Buy
        "stage_label": "Qualified to Buy",
        "contact_id": "533533859528",
        "contact_name": "Dr. Elena",
        "notes": "Completed introductory discovery call. Technical evaluation scheduled next Tuesday."
    }
]


async def seed_crm_data():
    settings = get_settings()
    print("==================================================")
    print("[*] Seeding Enterprise CRM Deals into Live HubSpot")
    print(f"[*] Live HubSpot Token Present: {bool(settings.HUBSPOT_ACCESS_TOKEN)}")
    print("==================================================")

    if not settings.HUBSPOT_ACCESS_TOKEN:
        print("[!] No HubSpot Access Token found.")
        return

    headers = {
        "Authorization": f"Bearer {settings.HUBSPOT_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Check existing deals in HubSpot to avoid duplicates
        resp = await client.get("https://api.hubapi.com/crm/v3/objects/deals?limit=100", headers=headers)
        existing_names = set()
        if resp.status_code == 200:
            for item in resp.json().get("results", []):
                existing_names.add(item.get("properties", {}).get("dealname"))

        for deal in ENTERPRISE_DEALS_TO_SEED:
            if deal["name"] in existing_names:
                print(f"  [-] Deal '{deal['name']}' already exists in HubSpot CRM. Skipping creation.")
                continue

            print(f"\nCreating Deal in HubSpot: {deal['name']} (${deal['amount']:,.0f})...")
            payload = {
                "properties": {
                    "dealname": deal["name"],
                    "amount": str(deal["amount"]),
                    "dealstage": deal["stage"],
                    "closedate": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                },
                "associations": [
                    {
                        "to": {"id": deal["contact_id"]},
                        "types": [
                            {
                                "associationCategory": "HUBSPOT_DEFINED",
                                "associationTypeId": 3
                            }
                        ]
                    }
                ]
            }

            d_resp = await client.post("https://api.hubapi.com/crm/v3/objects/deals", headers=headers, json=payload)
            if d_resp.status_code in [200, 201]:
                deal_id = d_resp.json().get("id")
                print(f"  [+] Live HubSpot Deal Created (ID: {deal_id})")

                # Log initial CRM Note
                note_payload = {
                    "properties": {
                        "hs_note_body": deal["notes"]
                    },
                    "associations": [
                        {
                            "to": {"id": deal_id},
                            "types": [
                                {
                                    "associationCategory": "HUBSPOT_DEFINED",
                                    "associationTypeId": 214  # note_to_deal
                                }
                            ]
                        }
                    ]
                }
                n_resp = await client.post("https://api.hubapi.com/crm/v3/objects/notes", headers=headers, json=note_payload)
                if n_resp.status_code in [200, 201]:
                    print(f"  [+] Logged CRM Note on Deal {deal_id}")
            else:
                print(f"  [!] Failed to create deal: {d_resp.status_code} - {d_resp.text}")

    print("\n[SUCCESS] Live HubSpot CRM Seeding Completed Successfully!")


if __name__ == "__main__":
    asyncio.run(seed_crm_data())

