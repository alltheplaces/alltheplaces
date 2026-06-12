import json
import re
from typing import Iterable
from urllib.parse import unquote

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, DAYS_FULL
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class FineWineGoodSpiritsSpider(SitemapSpider):
    name = "fine_wine_good_spirits"
    item_attributes = {"brand": "Fine Wine & Good Spirits", "brand_wikidata": "Q64514776"}
    sitemap_urls = ["https://www.finewineandgoodspirits.com/productSitemap.xml"]
    sitemap_rules = [(r"/product/store-\d+", "parse")]

    def parse(self, response: Response) -> Iterable[Feature]:
        location = next(
            iter(
                DictParser.get_nested_key(
                    json.loads(
                        unquote(
                            re.match(
                                r"window\.state = JSON\.parse\(decodeURI\(\"(.+?)\"\)\)",
                                response.xpath('//script[contains(text(), "window.state = ")]/text()').get(),
                            ).group(1)
                        )
                    ),
                    "products",
                ).values()
            )
        )

        item = Feature()
        item["ref"] = response.url.split("-")[-1]
        item["lat"] = location["b2cStore_latitude"]
        item["lon"] = location["b2cStore_longitude"]
        item["website"] = response.url
        item["country"] = "US"

        item["street_address"] = response.xpath('//h1[@class="heading_1"]/text()').get()
        item["addr_full"] = merge_address_lines(
            [item["street_address"], response.xpath('string(//h1[@class="heading_1"]/following-sibling::p)').get()]
        )
        item["phone"] = response.xpath('//a[contains(@href, "tel:")]/@href').get("").replace("tel:", "")
        item["email"] = response.xpath('//a[contains(@href, "mailto:")]/text()').get()

        img_url = response.urljoin(location["primaryFullImageURL"])
        # Only save the image if it is an actual photo, not a placeholder
        if "img/no-image" not in img_url:
            item["image"] = img_url

        oh = OpeningHours()
        for day in map(str.lower, DAYS_FULL):
            oh.add_range(day, location["b2cStore_{}OpenTime".format(day)], location["b2cStore_{}CloseTime".format(day)])
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_ALCOHOL, item)

        yield item
