import re
from json import loads
from typing import Iterable

from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class PeddersSuspensionAndBrakesAUSpider(AmastyStoreLocatorSpider):
    name = "pedders_suspension_and_brakes_au"
    item_attributes = {"brand": "Pedders Suspension & Brakes", "brand_wikidata": "Q127506238"}
    allowed_domains = ["www.pedders.com.au"]

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        if not item["email"].endswith("@pedders.com.au"):
            # Ignore authorised dealers. This is not a precise determination
            # method and some authorised dealers have @pedders.com.au email
            # addresses. It is not known how the website determines whether a
            # location is an official store or authorised dealer. FIXME.
            return
        if "DO NOT USE" in item["name"]:
            return

        item["ref"] = str(feature["id"])
        item["branch"] = item.pop("name").strip()

        slug_candidate = popup_html.xpath('//a[contains(@href, "/store/au/")]/@href').get()
        if slug_candidate:
            item["website"] = (
                "https://www.pedders.com.au" + popup_html.xpath('//a[contains(@href, "/store/au/")]/@href').get()
            )
        else:
            if m := re.search(
                r"(?<=\s)(Australian Capital Territory|ACT|New South Wales|NSW|Northern Territory|NT|Queensland|QLD|South Australia|SA|Tasmania|TAS|Victoria|VIC|Western Australia|WA)(?=\s)",
                item["addr_full"],
                flags=re.IGNORECASE,
            ):
                state_code = None
                match m.group(1).upper():
                    case "AUSTRALIAN CAPITAL TERRITORY" | "ACT":
                        state_code = "act"
                    case "NEW SOUTH WALES" | "NSW":
                        state_code = "nsw"
                    case "NORTHERN TERRITORY" | "NT":
                        state_code = "nt"
                    case "QUEENSLAND" | "QLD":
                        state_code = "qld"
                    case "TASMANIA" | "TAS":
                        state_code = "tas"
                    case "VICTORIA" | "VIC":
                        state_code = "vic"
                    case "WESTERN AUSTRALIA" | "WA":
                        state_code = "wa"
                if state_code:
                    item["website"] = (
                        "https://www.pedders.com.au/store/au/"
                        + state_code
                        + "/"
                        + re.sub(r"\W+", "-", item["branch"].lower()).strip("-")
                    )

        json_data = loads(feature["ga_json"])
        item["phone"] = json_data.get("storeNumber")

        hours_text = re.sub(r"\s+", " ", " ".join(popup_html.xpath('//div[@class="store-schedule"]//text()').getall()))
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_text)

        apply_category(Categories.SHOP_CAR_REPAIR, item)

        yield item
