import re

from scrapy import Selector, Spider

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class UpdateFitnessCHSpider(Spider):
    name = "update_fitness_ch"
    item_attributes = {"brand": "update Fitness", "brand_wikidata": "Q117406567"}
    start_urls = ["https://www.update-fitness.ch/standorte/"]

    def parse(self, response, **kwargs):
        script = response.xpath('//script[contains(text(), "markers")]/text()').get()

        for lat, lon, html in re.findall(
            r"new L\.LatLng\((-?\d+\.\d+), (-?\d+\.\d+)\), .+\.bindPopup\(\"(.+)\"\);", script
        ):
            item = Feature()
            item["lat"] = lat
            item["lon"] = lon

            html_selector = Selector(text=html.replace("\\'", '"'))

            item["image"] = html_selector.xpath("//img/@src").get()
            item["website"] = item["ref"] = html_selector.xpath("//a/@href").get()
            item["name"] = html_selector.xpath("//a/text()").get().strip()
            item["addr_full"] = merge_address_lines(
                html_selector.xpath('//div[@class="location-content"]//p[not(span)]/text()').getall()
            )

            yield item
