import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.structured_data_spider import extract_email


class SkiptonGBSpider(SitemapSpider):
    name = "skipton_gb"
    item_attributes = {"brand": "Skipton Building Society", "brand_wikidata": "Q16931747"}
    sitemap_urls = ["https://www.skipton.co.uk/robots.txt"]
    sitemap_rules = [(r"/branchfinder/[^/]+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if response.url == "https://www.skipton.co.uk/branchfinder/branches":
            return
        try:
            json_data = response.xpath('//input[@id="jsonData"]/@value').get()
            branch = json.loads(json_data)[0]
        except:
            return

        item = Feature()
        item["website"] = item["ref"] = response.url
        item["branch"] = branch["BranchName"]
        item["lat"] = branch["BranchLatitude"]
        item["lon"] = branch["BranchLongitude"]
        address = response.xpath("//address/text()").extract()
        cleaned = clean_address(address)
        item["addr_full"] = cleaned
        item["postcode"] = cleaned.split(", ")[-1]
        extract_email(item, response)
        apply_category(Categories.BANK, item)
        yield item
