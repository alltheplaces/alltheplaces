import json
import re

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class StoragemartUSGBSpider(StructuredDataSpider):
    name = "storagemart_us_gb"
    item_attributes = {"brand": "StorageMart", "brand_wikidata": "Q16226585"}
    start_urls = [
        "https://www.storage-mart.com/sitemap/united-states",
        "https://www.storage-mart.com/en-gb/sitemap/united-kingdom",
    ]
    wanted_types = ["SelfStorage"]
    drop_attributes = {"image", "facebook", "twitter"}

    def parse(self, response, **kwargs):
        for href in set(response.xpath('//a/@href[starts-with(., "/")]').getall()):
            if re.fullmatch(r"(/en-gb)?/[a-z0-9-]+(/[a-z0-9-]+){0,3}", href) and not re.search(
                r"^(/en-gb)?/(amenities|solutions|tips|about-us|self-storage|sitemap|storage-near-me)|-storage-units$|affordable-storage|car-storage",
                href,
            ):
                yield response.follow(href, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["website"].startswith("https://www.storage-mart.com/en-gb/"):
            item["country"] = "GB"
        elif re.fullmatch(r"\d{5}(-\d{4})?", item.get("postcode") or ""):
            item["country"] = "US"
        else:
            return
        item["ref"] = item.pop("name").split()[0]
        item["branch"] = None
        if m := re.search(r'"hours":\{"office":\{"note":"[^"]*","hours":(\[.*?\])', response.text):
            item["opening_hours"] = oh = OpeningHours()
            for rule in json.loads(m.group(1)):
                if rule["open"] < 0:
                    oh.set_closed(rule["day"][:2])
                else:
                    oh.add_range(
                        rule["day"][:2],
                        f"{int(rule['open']):02d}:{int(rule['open'] % 1 * 60):02d}",
                        f"{int(rule['close']):02d}:{int(rule['close'] % 1 * 60):02d}",
                    )

        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
