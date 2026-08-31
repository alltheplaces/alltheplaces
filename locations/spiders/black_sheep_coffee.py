import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BlackSheepCoffeeSpider(SitemapSpider):
    name = "black_sheep_coffee"
    item_attributes = {"brand": "Black Sheep Coffee", "brand_wikidata": "Q109745011"}
    sitemap_urls = ["https://blacksheepcoffee.co.uk/sitemap.xml"]
    sitemap_rules = [("/locations/", "parse")]
    skip_auto_cc_domain = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if lat_lon_data := response.xpath('//*[contains(text(),"latLngMarker")]/text()').get():
            item = Feature()
            item["branch"] = response.xpath("//title/text()").get().strip().removesuffix(" – Black Sheep Coffee")
            item["street_address"] = response.xpath('//*[@class="location-find-us__address"]/text()').get()
            item["addr_full"] = merge_address_lines(
                response.xpath('//*[@class="location-find-us__address"]//text()').getall()
            )
            item["lat"], item["lon"] = re.search(r"LatLng\((-?\d+\.\d+),\s*(-?\d+\.\d+)\);\s*", lat_lon_data).groups()
            item["ref"] = item["website"] = response.url
            oh = OpeningHours()
            for day_time in response.xpath('//*[@class="location-find-us__address flex f-space-between"]//p'):
                day_time_text = merge_address_lines(day_time.xpath(".//text()").getall())
                oh.add_ranges_from_string(day_time_text)
            item["opening_hours"] = oh

            yield item
