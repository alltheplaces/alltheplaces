import html
from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import extract_phone


class ProperJobGBSpider(SitemapSpider):
    name = "proper_job_gb"
    item_attributes = {"brand": "Proper Job", "brand_wikidata": "Q83741810"}
    sitemap_urls = ["https://www.properjob.biz/wpsl_stores-sitemap.xml"]
    sitemap_rules = [(r"/stores/[^/]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location = chompjs.parse_js_object(response.text[response.text.index("wpslMap_0") :])["locations"][0]
        brand, _, branch = html.unescape(location["store"]).partition("–")
        if brand.strip() != "Proper Job":
            return

        item = DictParser.parse(location)
        item["addr_full"] = None
        item["street_address"] = merge_address_lines([location["address"], location["address2"]])
        item["website"] = response.url
        item["branch"] = branch.strip()

        extract_phone(item, response)
        if item.get("phone") == "N/A":
            item["phone"] = None

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//table[@class="wpsl-opening-hours"]//tr'):
            day = rule.xpath("./td[1]/text()").get()
            if rule.xpath("./td[2]/text()").get() == "Closed":
                item["opening_hours"].set_closed(day)
            else:
                item["opening_hours"].add_range(
                    day, *rule.xpath("./td/time/text()").get().split(" - "), time_format="%I:%M %p"
                )

        apply_category(Categories.SHOP_HARDWARE, item)
        yield item
