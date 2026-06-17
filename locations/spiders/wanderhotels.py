import json
import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class WanderhotelsSpider(SitemapSpider):
    name = "wanderhotels"
    item_attributes = {"brand": "Wanderhotels", "brand_wikidata": "Q123436959"}
    sitemap_urls = ["https://www.wanderhotels.com/sitemap.xml"]
    sitemap_rules = [(r"https://www\.wanderhotels\.com/en/wanderhotels/.+", "parse")]
    custom_settings = {"DOWNLOAD_TIMEOUT": 30}

    def parse(self, response, **kwargs):
        raw_data = json.loads(re.search(r"map\":({.*}),\"master", response.text).group(1))
        item = DictParser.parse(raw_data)
        item.pop("country")
        item["phone"] = response.xpath('//a[contains(@href, "tel:")]/text()').get()
        item["email"] = response.xpath('//a[contains(@href, "mailto")]/text()').get()
        item["street_address"] = merge_address_lines([item["street"], item.pop("housenumber")])
        item["ref"] = item["website"] = response.url
        apply_category(Categories.HOTEL, item)
        yield item
