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
        item["ref"] = location["b2cStore_id"]
        item["lat"] = location["b2cStore_latitude"]
        item["lon"] = location["b2cStore_longitude"]
        item["website"] = response.url
        item["country"] = "US"

        item["street_address"] = merge_address_lines(
            [location["b2cStore_address1"], location["b2cStore_address2"], location["b2cStore_address3"]]
        )
        item["city"] = location["b2cStore_city"]
        item["state"] = location["b2cStore_state"]
        item["postcode"] = location["b2cStore_zip"]
        item["phone"] = location["b2cStore_phoneNumber"]
        item["email"] = location["b2cStore_contactEmail"]

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
