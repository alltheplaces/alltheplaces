import json

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class LandmarkCinemasCASpider(Spider):
    name = "landmark_cinemas_ca"
    item_attributes = {"brand": "Landmark Cinemas", "brand_wikidata": "Q6484762"}
    start_urls = ["https://www.landmarkcinemas.com/"]

    def parse(self, response, **kwargs):
        for ref in response.xpath('//select[@id="preflocationHomepage"]/option/@value').getall():
            if ref != "-1":
                yield JsonRequest(
                    url=f"https://www.landmarkcinemas.com/umbraco/api/baseapi/GetCinemaInfo?cinemaId={ref}",
                    callback=self.parse_location,
                )

    def parse_location(self, response, **kwargs):
        location = json.loads(response.json())
        item = DictParser.parse(location)
        item["name"] = location["CinemaName"]
        item["website"] = item["ref"] = f'https://www.landmarkcinemas.com{location["CinemaInfoUrl"]}'
        item["image"] = f'https://www.landmarkcinemas.com{location["Image"]}'
        item["street_address"] = merge_address_lines([location["Address1"], location["Address2"]])

        yield item
