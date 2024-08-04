import json

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.pipelines.phone_clean_up import PhoneCleanUpPipeline
from locations.storefinders.where2getit import Where2GetItSpider


class MattressFirmUSSpider(Where2GetItSpider):
    name = "mattress_firm_us"
    api_endpoint = "https://api.slippymap.com/mattressfirmsites/rest/getlist"
    api_key = "88FD3C6E-2B22-11EE-86CD-EF1E9DC6E625"

    def parse_item(self, item, location, **kwargs):
        # Apply basic information common to each brand
        apply_category(Categories.SHOP_BED, item)

        if location["mattress_firm_clearance_center"] == "yes":
            item["brand"] = "Mattress Firm Clearance"
            item["brand_wikidata"] = "Q6791878"
        elif location["sleep_expert_store"] == "yes":
            item["brand"] = "Sleep Experts"
            item["brand_wikidata"] = "Q7539688"
        else:
            item["brand"] = "Mattress Firm"
            item["brand_wikidata"] = "Q6791878"

        item["branch"] = item.pop("name").removeprefix(item["brand"]).strip()

        # Store attributes
        # (also includes payment methods, but that's not shown on the website)
        attributes = {kv["id"]: kv["value"] for kv in json.loads(location["attributes"])}
        if "has_delivery" in attributes:
            apply_yes_no(Extras.DELIVERY, item, attributes["has_delivery"] == "yes", attributes["has_delivery"] != "no")

        # Extra contact info
        project_meta = json.loads(location["project_meta"])
        item["facebook"] = project_meta.get("Facebook URL")
        apply_category(
            {
                "contact:sms": PhoneCleanUpPipeline().normalize_numbers(
                    project_meta.get("SMS Phone Number", ""), item["country"], self
                )
            },
            item,
        )

        yield item
