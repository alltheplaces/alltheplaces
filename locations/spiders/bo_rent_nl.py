import json
import re

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BoRentNLSpider(CrawlSpider, StructuredDataSpider):
    name = "bo_rent_nl"
    item_attributes = {"brand": "Bo-rent", "brand_wikidata": "Q126919301"}
    start_urls = [
        "https://borent.nl/auto-huren/locaties",
        "https://borent.nl/tool-rental/locations",
        "https://borent.nl/self-storage/filialen/",
    ]
    rules = [
        Rule(
            LinkExtractor(allow="/auto-huren/[^/]+$", restrict_xpaths='//*[@class="col-xs-6 singlemarker"]'),
            callback="parse_sd",
        ),
        Rule(
            LinkExtractor(allow="/tool-rental/[^/]+$", restrict_xpaths='//*[@class="col-xs-6 singlemarker"]'),
            callback="parse_tool_rental_locations",
        ),
        Rule(
            LinkExtractor(allow="/self-storage/filialen/", restrict_xpaths='//*[@class="stretched-link"]'),
            callback="parse_self_storage_locations",
        ),
    ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["lat"] = re.search(
            r"lat\s*=\s*(\d+\.\d+),", response.xpath('//*[contains(text(),"markersArray")]/text()').get()
        ).group(1)
        item["lon"] = re.search(
            r"lon\s*=\s*(\d+\.\d+),", response.xpath('//*[contains(text(),"markersArray")]/text()').get()
        ).group(1)
        # TODO: remove below line when category is added to NSI for this brand
        item["nsi_id"] = "N/A"
        apply_category(Categories.CAR_RENTAL, item)
        yield item

    def parse_tool_rental_locations(self, response):
        item = Feature()
        item["name"] = response.xpath('//*[@id="branchinfo"]/h1/text()').get()
        item["street"] = response.xpath('//*[@class="streetname"]/text()').get()
        item["housenumber"] = response.xpath('//*[@class="housenumber"]/text()').get()
        item["city"] = response.xpath('//*[@class="city"]/text()').get()
        item["postcode"] = response.xpath('//*[@class="zipcode"]/text()').get()
        item["lat"] = re.search(
            r"lat\s*=\s*(\d+\.\d+),", response.xpath('//*[contains(text(),"markersArray")]/text()').get()
        ).group(1)
        item["lon"] = re.search(
            r"lon\s*=\s*(\d+\.\d+),", response.xpath('//*[contains(text(),"markersArray")]/text()').get()
        ).group(1)
        item["ref"] = item["website"] = response.url
        apply_category(Categories.SHOP_TOOL_HIRE, item)
        oh = OpeningHours()
        for day_time in response.xpath('//*[@id="open_hours"]//*[@class="input"]'):
            day = day_time.xpath("./label/text()").get()
            time = day_time.xpath("./span/text()").get()
            if time == "Closed":
                oh.set_closed(day)
            else:
                open_time, close_time = time.split(" - ")
                oh.add_range(day=day, open_time=open_time, close_time=close_time)
            item["opening_hours"] = oh
        yield item

    def parse_self_storage_locations(self, response):
        raw_data = json.loads(
            re.search(
                r"branch\":({.*})}\]}\]",
                response.xpath('//*[contains(text(),"zipcode")]/text()').get().replace('\\"', '"'),
            ).group(1)
        )
        item = DictParser.parse(raw_data)
        for url in raw_data["breadcrumb"]:
            if "/self-storage/filialen/" in url["url"]:
                item["website"] = "https://borent.nl" + url["url"]
        item["street_address"] = item.pop("addr_full")
        oh = OpeningHours()
        for day, time in raw_data["operational_hours"].items():
            open_time = time["start_time"]
            close_time = time["end_time"]
            if open_time is None:
                oh.set_closed(day)
            else:
                oh.add_range(day=day, open_time=open_time, close_time=close_time)
        item["opening_hours"] = oh
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
