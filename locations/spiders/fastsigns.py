import re
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class FastsignsSpider(Spider):
    name = "fastsigns"
    item_attributes = {"brand": "Fastsigns", "brand_wikidata": "Q5437127"}
    # Not covered: Dominican Republic, Grand Cayman, Malta, United Kingdom
    json_urls = [
        "https://www.fastsigns.cl/locales/?CallAjax=AllLocations",
        "https://www.signwave.com.au/locations/?CallAjax=AllLocations",
    ]
    zyte_meta = {"zyte_api": {"httpResponseBody": True, "httpResponseHeaders": True}}

    async def start(self) -> AsyncIterator[Request]:
        # covers CA, PR, US
        yield Request("https://www.fastsigns.com/locations/", callback=self.parse_regions, meta=self.zyte_meta)
        for url in self.json_urls:
            yield Request(url, callback=self.parse_json, meta=self.zyte_meta)

    def parse_regions(self, response: Response, **kwargs: Any) -> Any:
        for href in set(response.xpath('//a[re:test(@href, "^/locations/[a-z-]+/$")]/@href').getall()):
            yield response.follow(href, callback=self.parse_region, meta=self.zyte_meta)

    def parse_region(self, response: Response, **kwargs: Any) -> Any:
        for location in response.css('li[data-role="location"]'):
            href = location.css("a.fnt_t-itm::attr(href)").get()
            item = Feature()
            item["ref"] = item["website"] = response.urljoin(href)
            item["lat"] = location.attrib.get("data-latitude")
            item["lon"] = location.attrib.get("data-longitude")
            item["branch"] = re.sub(
                r"^FASTSIGNS\W*\s+(of\s+)?",
                "",
                location.css("a.fnt_t-itm strong::text").get(""),
                flags=re.IGNORECASE,
            )
            item["addr_full"] = ", ".join(t.strip() for t in location.xpath(".//address//text()").getall() if t.strip())
            item["phone"] = location.css("a.fnt_phn::text").get()
            apply_category(Categories.CRAFT_SIGNMAKER, item)
            yield item

    def parse_json(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item.pop("name")
            item["street_address"] = merge_address_lines([location["Address1"], location["Address2"]])
            item["unit"] = location["Address2"]
            item["ref"] = location["FranchiseLocationID"]
            item["branch"] = location["FriendlyName"]
            item["website"] = response.urljoin(location["Path"])

            if location["LaunchDate"][:10] not in ("2021-07-19", "2022-07-07", "2022-08-29", "2022-11-28"):
                item["extras"]["start_date"] = location["LaunchDate"][:10]
            if location["StorefrontImage"]:
                item["image"] = response.urljoin(location["StorefrontImage"])

            if location["Country"] == "AUS":
                item["name"] = item["brand"] = "Signwave"
                item["brand_wikidata"] = "Q136850122"

            apply_category(Categories.CRAFT_SIGNMAKER, item)
            yield item
