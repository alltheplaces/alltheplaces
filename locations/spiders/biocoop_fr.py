import json
import re
from typing import Any

from scrapy import Selector
from scrapy.http import Response

from scrapy.spiders import XMLFeedSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class BiocoopFRSpider(XMLFeedSpider):
    name = "biocoop_fr"
    item_attributes = {"brand": "Biocoop", "brand_wikidata": "Q2904039"}
    allowed_domains = ["www.biocoop.fr"]
    start_urls = ["https://www.biocoop.fr//rest/V1/searchstores/query/all"]
    itertag = "item"
    custom_settings = {
        "DOWNLOAD_TIMEOUT": 60  # their server is quite slow, can take more than 15s to answer in peak hours
    }

    def parse_node(self, response: Response, selector: Selector) -> Any:
        item = Feature()
        item["ref"] = selector.xpath("code/text()").get()
        item["branch"] = re.sub(r"BIOCOOP", "", selector.xpath("name/text()").get(""), flags=re.IGNORECASE)
        item["street_address"] = selector.xpath("street/text()").get()
        item["city"] = selector.xpath("city/text()").get()
        item["postcode"] = selector.xpath("postcode/text()").get()
        item["lat"] = selector.xpath("latitude/text()").get()
        item["lon"] = selector.xpath("longitude/text()").get()
        item["phone"] = selector.xpath("telephone/text()").get()
        item["opening_hours"] = self.decode_hours(json.loads(selector.xpath("openinghours_json/text()").get()))
        item["website"] = selector.xpath("external_link/text()").get()
        if item["website"] == "" or item["website"] == "null":
            item["website"] = selector.xpath("store_url/text()").get()
        item["extras"]["organic"] = "only"

        apply_category(Categories.SHOP_SUPERMARKET, item)

        return item

    @staticmethod
    def decode_hours(opening_hours):
        oh = OpeningHours()
        for day in opening_hours:
            # Each day has the keys am_start, am_end, pm_start and pm_end
            # Some or all can have an empty value, we let add_range skip those

            # Let's just handle the case of the all day opening. In this case only
            # am_start and pm_end have a non-empty value
            if opening_hours[day]["am_end"] == "" and opening_hours[day]["pm_start"] == "":
                # Open all day or closed all day
                oh.add_range(day, opening_hours[day]["am_start"], opening_hours[day]["pm_end"])
            else:
                # Open for half a day or with a lunch break
                oh.add_range(day, opening_hours[day]["am_start"], opening_hours[day]["am_end"])
                oh.add_range(day, opening_hours[day]["pm_start"], opening_hours[day]["pm_end"])
        return oh
