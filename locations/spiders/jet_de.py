import json
import re

import scrapy
from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.items import Feature


class JetDESpider(scrapy.Spider):
    name = "jet_de"
    item_attributes = {"brand": "Jet", "brand_wikidata": "Q568940"}
    start_urls = ["https://www.jet.de/tankstellen-suche"]

    def parse(self, response, **kwargs):
        for location in json.loads(re.search(r"stationsData: (\[.+\])\n}", response.text).group(1)):
            if "fuel" not in location["features"]:
                continue
            item = Feature()
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            popup = Selector(text=location["cardHtml"])
            item["ref"] = item["website"] = response.urljoin(popup.xpath('//a[@class="link-ts-list"]/@href').get())
            item["addr_full"] = (
                popup.xpath('normalize-space(//div[contains(@class, "search-result-header")]/h2/text())')
                .get()
                .removeprefix("JET ")
            )
            apply_category(Categories.FUEL_STATION, item)
            yield item
