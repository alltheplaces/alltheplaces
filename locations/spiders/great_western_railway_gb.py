from scrapy import Request

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.structured_data_spider import StructuredDataSpider


class GreatWesternRailwayGBSpider(StructuredDataSpider):
    name = "great_western_railway_gb"
    item_attributes = {"operator": "Great Western Railway", "operator_wikidata": "Q1419438"}
    start_urls = ["https://www.gwr.com/api/stations"]
    wanted_types = ["TrainStation"]
    search_for_twitter = False
    search_for_facebook = False
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for location in response.json():
            if location["operator"] == "GW":
                yield Request(response.urljoin(location["url"]), callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["extras"]["ref:crs"] = item["ref"]

        apply_category(Categories.TRAIN_STATION, item)

        yield item
