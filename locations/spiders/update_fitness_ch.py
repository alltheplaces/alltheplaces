from typing import Any

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class UpdateFitnessCHSpider(StructuredDataSpider):
    name = "update_fitness_ch"
    item_attributes = {"brand": "update Fitness", "brand_wikidata": "Q117406567"}
    start_urls = ["https://www.update-fitness.ch/standorte/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for studio in response.xpath(
            '//a[@data-locations-studio][@data-is-soon="false"][@data-is-presale="false"]/@href'
        ).getall():
            yield response.follow(studio, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["branch"] = (item.pop("name", None) or "").removeprefix("update Fitness ")
        item["website"] = item["ref"] = response.url
        apply_category(Categories.GYM, item)
        yield item
