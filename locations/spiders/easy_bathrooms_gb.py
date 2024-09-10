from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class EasyBathroomsGBSpider(CrawlSpider):
    name = "easy_bathrooms_gb"
    item_attributes = {"brand": "Easy Bathrooms", "brand_wikidata": "Q114348566"}
    allowed_domains = ["www.easybathrooms.com"]
    start_urls = ["https://www.easybathrooms.com/our-showrooms"]
    rules = [Rule(LinkExtractor(allow=r"^https:\/\/www\.easybathrooms\.com\/our-showrooms\/[^/]+$"), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        js_blob = response.xpath('//script[contains(text(), "function initMap()")]/text()').get()
        lat, lon = js_blob.split("google.maps.LatLng(", 1)[1].split(")", 1)[0].split(", ", 1)
        properties = {
            "ref": response.url.split("/(?!$)")[-1],
            "branch": response.xpath("//h1/span[2]/text()").get(),
            "lat": lat,
            "lon": lon,
            "addr_full": merge_address_lines(
                response.xpath('//div[contains(span/text(), "Find Us")]/ul/li/text()').getall()
            ),
            "phone": response.xpath('//span[@class="text-base"][contains(text(), "0")]/text()').get(),
            "website": response.url,
        }
        hours_string = " ".join(
            filter(None, map(str.strip, response.xpath('//div[@id="opening-times"]/ul[1]//text()').getall()))
        )
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string)

        apply_category(Categories.SHOP_BATHROOM_FURNISHING, properties)

        yield Feature(**properties)
