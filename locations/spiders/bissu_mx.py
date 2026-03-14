import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature


class BissuMXSpider(CrawlSpider):
    name = "bissu_mx"
    item_attributes = {"brand": "Bissú", "brand_wikidata": "Q130466489"}
    start_urls = ["https://bissu.com/tiendas"]
    rules = [Rule(LinkExtractor(allow=r"/tiendas/", restrict_text="Bissú"), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = response.url.rsplit("/", 1)[1]
        item["website"] = response.url
        item["name"] = response.xpath("//h1/span/text()").get()

        for key, label in [
            ("postcode", "Código Postal"),
            ("city", "Ciudad"),
            ("street_address", "Dirección"),
        ]:
            query = f'(//div[@class="amlocator-block"]/span[preceding-sibling::span/text()="{label}:"])[last()]/text()'
            item[key] = response.xpath(query).get().strip()

        phone = response.xpath('//a/@href[contains(., "tel:")]').get()
        if phone:
            item["phone"] = phone.replace("tel:", "")

        location_script = response.xpath('//script[contains(., "locationData")]/text()')
        latlon_re = r"locationData:\s*{[^}]*lat:\s*([^,]*),\s*lng:\s*([^,]*)[^}]*}"
        item["lat"], item["lon"] = location_script.re(latlon_re, re.DOTALL)

        apply_category(Categories.SHOP_COSMETICS, item)

        yield item
