import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import extract_phone


class ScotmidGBSpider(SitemapSpider):
    name = "scotmid_gb"
    item_attributes = {"brand": "Scotmid", "brand_wikidata": "Q7435719"}
    sitemap_urls = ["https://scotmid.coop/wpsl_stores-sitemap.xml"]
    sitemap_rules = [(r"/store/([^/]+)/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location = json.loads(re.search(r"wpslMap_0 = (\{.+\});", response.text).group(1))["locations"][0]
        item = DictParser.parse(location)
        item["addr_full"] = None
        item["street_address"] = merge_address_lines([location["address"], location["address2"]])
        item["branch"] = location["store"]
        item["website"] = response.url
        extract_phone(item, response)

        for css_class in response.xpath('//main[@id="content"]/@class').get().split(" "):
            if css_class.startswith("wpsl_store_category-"):
                store_type = css_class.removeprefix("wpsl_store_category-")
                break
        else:
            raise Exception("Unknown store type")

        if store_type == "post-offices":
            return  # Skip post offices
        elif store_type == "scotmid":
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif store_type == "semichem":
            item["brand"] = "Semichem"
            item["brand_wikidata"] = "Q17032096"
        elif store_type == "lakes-and-dales":
            item["name"] = item["brand"] = "Lakes & Dales Co-operative"
            item["brand_wikidata"] = "Q110620660"
            apply_category(Categories.SHOP_CONVENIENCE, item)
        elif store_type == "funeral-branches":
            item["name"] = item["brand"] = "Scotmid Funerals"
            item["brand_wikidata"] = "Q125940846"
            apply_category(Categories.SHOP_FUNERAL_DIRECTORS, item)

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//table[@class="wpsl-opening-hours"]//tr'):
            day = rule.xpath("./td[1]/text()").get()
            if rule.xpath("./td[2]/text()").get() == "Closed":
                item["opening_hours"].set_closed(day)
            else:
                item["opening_hours"].add_range(day, *rule.xpath("./td/time/text()").get().split(" - "))

        yield item
