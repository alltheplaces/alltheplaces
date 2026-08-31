import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class PdqUSSpider(SitemapSpider):
    name = "pdq_us"
    item_attributes = {"brand": "PDQ", "brand_wikidata": "Q87675367"}
    sitemap_urls = ["https://www.eatpdq.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/(?!find-a-location).*", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location_dict = json.loads(response.xpath("//@data-context").get()).get("location", {})
        item = DictParser.parse(location_dict)
        item["lat"] = location_dict.get("mapLat")
        item["lon"] = location_dict.get("mapLng")
        item["branch"] = location_dict.get("addressTitle").removeprefix("PDQ").strip()
        item["addr_full"] = merge_address_lines([location_dict.get("addressLine1"), location_dict.get("addressLine2")])
        item["ref"] = response.url.split("/")[-1]
        item["website"] = response.url

        oh = OpeningHours()
        if hours_str := " ".join(
            [
                t.strip()
                for t in response.xpath("//h3[contains(text(), 'STORE HOURS')]/following-sibling::p//text()").getall()
                if t.strip()
            ]
        ):
            oh.add_ranges_from_string(hours_str)

        item["opening_hours"] = oh

        if contact_node := response.xpath("//h3[contains(text(), 'CONTACT')]/following-sibling::p"):
            contact_text = " ".join(contact_node.xpath(".//text()").getall())

            if phone_match := re.search(r"(\d{3}-\d{3}-\d{4})", contact_text):
                item["phone"] = phone_match.group(1)

            if email_match := re.search(r"([\w\.-]+@[\w\.-]+\.\w+)", contact_text):
                item["email"] = email_match.group(1)

        yield item
