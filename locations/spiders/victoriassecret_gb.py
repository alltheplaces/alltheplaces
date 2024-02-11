import re

import scrapy

from locations.items import Feature


class VictoriasSecretGBSpider(scrapy.Spider):
    name = "victorias_secret_gb"
    item_attributes = {
        "brand": "Victoria's Secret",
        "brand_wikidata": "Q332477",
        "country": "GB",
    }
    allowed_domains = ["victoriassecret.co.uk"]
    start_urls = ["https://www.victoriassecret.co.uk/store-locator"]

    def parse(self, response):
        for store in response.xpath('//li[@class="vs-store"]'):
            item = Feature()
            item["name"] = " ".join(
                filter(
                    None,
                    map(
                        str.strip,
                        store.xpath('./button[@class="vs-store-btn"]/descendant-or-self::text()').getall(),
                    ),
                )
            ).replace(", find us in the Next store", "")
            item["phone"] = (
                store.xpath('./div[@class="vs-store-details"]/div[@class="vs-store-address"]/strong/text()')
                .get("")
                .strip()
            )
            item["addr_full"] = (
                ", ".join(
                    filter(
                        None,
                        map(
                            str.strip,
                            store.xpath(
                                './div[@class="vs-store-details"]/div[@class="vs-store-address"]/descendant-or-self::text()'
                            ).getall(),
                        ),
                    )
                ).replace(item["phone"], "")
                + "United Kingdom"
            )
            item["ref"] = item["phone"]

            postcode_re = re.search(r"(\w{1,2}\d{1,2}\w? \d\w{2})", item["addr_full"])
            if postcode_re:
                item["postcode"] = postcode_re.group(1)

            if "PINK" in item["name"]:
                item["brand"] = "Pink"
                item["brand_wikidata"] = "Q20716793"

            yield item
