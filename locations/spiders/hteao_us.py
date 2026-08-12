import re

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import extract_facebook


class HteaoUSSpider(SitemapSpider):
    name = "hteao_us"
    item_attributes = {"brand": "HTeaO", "brand_wikidata": "Q129814206"}
    sitemap_urls = ["https://hteao.com/wpsl_stores-sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+/$", "parse")]
    locations_regex = re.compile(r'"locations":\s*(\[.*?\])\s*,\s*"mapOptions"', re.DOTALL)

    def parse(self, response: Response):
        js_blob = response.xpath('//script[contains(., "CONFIGURATION")]/text()').re_first(self.locations_regex)
        if not js_blob:
            self.logger.warning(f"No location data found on {response.url}")
            return
        location = chompjs.parse_js_object(js_blob)[0]
        if "on wheels" in location["title"].lower():
            # Mobile trailer units with no fixed address, e.g. "See Socials for Updates!"
            return

        item = DictParser.parse(location)
        item["ref"] = item["website"] = response.url
        item["branch"] = item.pop("name", None)
        item["street_address"] = merge_address_lines([location.get("address1"), location.get("address2")])
        extract_facebook(item, response)

        item["opening_hours"] = OpeningHours()
        for row in response.xpath('//table[contains(@class, "wpsl-opening-hours")]/tr'):
            day = row.xpath("td[1]//text()").get("")
            for hours in row.xpath("td[2]//text()").getall():
                if hours.strip():
                    item["opening_hours"].add_ranges_from_string(f"{day} {hours}")

        apply_category(Categories.CAFE, item)

        yield item
