from typing import Iterable

from scrapy.http import Request, Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class IgaAUSpider(CrawlSpider):
    name = "iga_au"
    item_attributes = {"brand": "IGA", "brand_wikidata": "Q5970945"}
    allowed_domains = ["www.iga.com.au", "www.google.com", "goo.gl"]
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
    follow_google_maps_urls = True
    custom_settings = {"ROBOTSTXT_OBEY": False}  # Required for maps.google.com

    def parse_store(self, response: Response) -> Iterable[Feature | Request]:
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

        google_maps_url_cid = response.xpath('//a[contains(@href, "https://maps.google.com/maps?cid=")]/@href').get()
        google_maps_url_short = response.xpath('//a[contains(@href, "https://goo.gl/maps/")]/@href').get()
        if self.follow_google_maps_urls and google_maps_url_cid:
            google_maps_url_cid = google_maps_url_cid.replace("maps.google.com", "www.google.com")
            yield Request(
                url=google_maps_url_cid,
                callback=self.parse_coordinates_cid,
                meta={"properties": properties, "handle_httpstatus_list": [429]},
            )
        elif self.follow_google_maps_urls and google_maps_url_short:
            yield Request(
                url=google_maps_url_short,
                callback=self.parse_coordinates_short,
                meta={"properties": properties, "handle_httpstatus_list": [429]},
            )
        else:
            yield Feature(**properties)

    def parse_coordinates_cid(self, response: Response) -> Iterable[Feature]:
        properties = response.meta["properties"]
        if response.status == 429:
            self.follow_google_maps_urls = False
            self.logger.error(
                "Google Maps rate limiting encountered when following redirect to obtain feature coordinates. Coordinates could not be extracted for feature."
            )
        if self.follow_google_maps_urls and "https://www.google.com/maps/preview/place/" in response.text:
            properties["lat"], properties["lon"] = url_to_coords("https://www.google.com/maps/preview/place/" + response.text.split(r"\"https://www.google.com/maps/preview/place/", 1)[1].split(r"\"", 1)[0])
        yield Feature(**properties)

    def parse_coordinates_short(self, response: Response) -> Iterable[Feature]:
        properties = response.meta["properties"]
        if response.status == 429:
            self.follow_google_maps_urls = False
            self.logger.error(
                "Google Maps rate limiting encountered when following redirect to obtain feature coordinates. Coordinates could not be extracted for feature."
            )
        if self.follow_google_maps_urls:
            properties["lat"], properties["lon"] = url_to_coords(response.url)
        yield Feature(**properties)
