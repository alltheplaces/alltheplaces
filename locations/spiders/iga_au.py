import re
from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class IgaAUSpider(CrawlSpider):
    name = "iga_au"
    item_attributes = {"brand": "IGA", "brand_wikidata": "Q5970945"}
    allowed_domains = ["www.iga.com.au"]
    start_urls = [
        "https://www.iga.com.au/stores/act/",
        "https://www.iga.com.au/stores/nsw/",
        "https://www.iga.com.au/stores/nt/",
        "https://www.iga.com.au/stores/qld/",
        "https://www.iga.com.au/stores/sa/",
        "https://www.iga.com.au/stores/tas/",
        "https://www.iga.com.au/stores/vic/",
        "https://www.iga.com.au/stores/wa/",
    ]
    rules = [
        Rule(
            LinkExtractor(allow=r"\/stores\/", restrict_xpaths='//ul[contains(@class, "states-list")]'),
            callback="parse_store",
        )
    ]

    def parse_store(self, response: Response) -> Iterable[Feature]:
        properties = {
            "ref": response.url,
            "name": response.xpath('//h1[@id="store-name"]/text()').get(),
            "addr_full": merge_address_lines(
                [
                    response.xpath('//div[@id="store-address-line-1"]/text()').get(),
                    response.xpath('//div[@id="store-address-line-2"]/text()').get(),
                ]
            ),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        if phone := response.xpath('//a[@id="phone-no"]/@href').get():
            properties["phone"] = phone.removeprefix("tel:")
        apply_category(Categories.SHOP_SUPERMARKET, properties)

        hours_string = " ".join(response.xpath('//table[@id="store-hours-table"]//text()').getall())
        properties["opening_hours"].add_ranges_from_string(hours_string)

        # The source data only provides URLs to Google Maps via CID or via
        # URL redirect service goo.gl which will be shutdown in the 2nd half
        # of 2025.
        if google_maps_url_cid := response.xpath(
            '//a[contains(@href, "https://maps.google.com/maps?cid=")]/@href'
        ).get():
            if m := re.search(r"\Wcid=(\d+)\b", google_maps_url_cid):
                properties["extras"]["ref:google:cid"] = m.group(1)

        yield Feature(**properties)
