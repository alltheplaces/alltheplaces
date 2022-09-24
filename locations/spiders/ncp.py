# -*- coding: utf-8 -*-
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


from locations.structured_data_spider import StructuredDataSpider


class NCPGB(CrawlSpider, StructuredDataSpider):
    name = "ncp_gb"
    item_attributes = {"brand": "NCP", "brand_wikidata": "Q6971273"}
    allowed_domains = ["www.ncp.co.uk"]
    start_urls = ["https://www.ncp.co.uk/parking-solutions/cities/"]
    rules = [
        Rule(
            LinkExtractor(
                allow={
                    ".*/parking-solutions/cities/.*",
                    ".*/parking-solutions/airports/.*",
                    ".*/car-parks/.*",
                }
            ),
            callback="parse_sd",
            follow=True,
        )
    ]
    download_delay = 0.5
    wanted_types = ["ParkingFacility"]
