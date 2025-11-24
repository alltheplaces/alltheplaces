from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RottenRobbieUSSpider(StructuredDataSpider):
    name = "rotten_robbie_us"
    item_attributes = {"brand": "Rotten Robbie", "brand_wikidata": "Q87378070"}
    start_urls = ["https://rottenrobbie.com/locations"]
    wanted_types = ["LocalBusiness"]
    json_parser = "chompjs"

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"], item["ref"] = item.pop("name").split(" - Store #")
        apply_category(Categories.FUEL_STATION, item)
        yield item
