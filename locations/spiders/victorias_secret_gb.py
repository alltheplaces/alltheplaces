import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class VictoriasSecretGBSpider(scrapy.Spider):
    name = "victorias_secret_gb"
    item_attributes = {
        "brand": "Victoria's Secret",
        "brand_wikidata": "Q332477",
        "country": "GB",
    }
    allowed_domains = ["victoriassecret.co.uk"]
    start_urls = ["https://www.victoriassecret.co.uk/store-locator"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath('//li[@class="vs-store"]'):
            item = Feature()
            item["branch"] = (
                store.xpath('./button[@class="vs-store-btn"]/strong/text()').get().removesuffix(" Victoria's Secret")
            )

            addr = list()
            for line in store.xpath('./div[@class="vs-store-details"]/div[@class="vs-store-address"]//text()').getall():
                line = line.strip()
                if not line:
                    continue
                if "Opening Times" in line:
                    item["opening_hours"] = OpeningHours()
                elif item.get("opening_hours") is None:
                    addr.append(line)
                else:
                    if m := re.match(r"(\w+) - (\d\d:\d\d) - (\d\d:\d\d)", line):
                        item["opening_hours"].add_range(*m.groups())
                    elif m := re.match(r"([\s\d()]+)", line):
                        item["phone"] = m.group(1)

            item["addr_full"] = merge_address_lines(addr)

            yield item
