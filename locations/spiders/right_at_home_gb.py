import json

from scrapy import Selector, Spider

from locations.categories import apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class RightAtHomeGBSpider(Spider):
    name = "right_at_home_gb"
    item_attributes = {"brand": "Right at Home", "brand_wikidata": "Q20710450"}
    start_urls = ["https://www.rightathome.co.uk/find-your-local-office/"]

    def parse(self, response, **kwargs):
        for location in json.loads(response.xpath("//@data-results").get()):
            location["url"] = response.urljoin(location["url"])
            location["address"] = merge_address_lines(Selector(text=location["address"]).xpath("//text()").getall())
            item = DictParser.parse(location)
            apply_category({"office": "company"}, item)
            yield item
