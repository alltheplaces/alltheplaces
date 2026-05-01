from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MendocinoFarmsUSSpider(CrawlSpider, StructuredDataSpider):
    name = "mendocino_farms_us"
    item_attributes = {"brand": "Mendocino Farms", "brand_wikidata": "Q110671982"}
    start_urls = ["https://www.mendocinofarms.com/locations"]
    rules = [Rule(LinkExtractor(restrict_xpaths='//li[@class="location-item"]/a'), "parse")]
    search_for_amenity_features = False
    search_for_twitter = False
    search_for_facebook = False
    json_parser = "chompjs"  # Some pages include broken json eg https://www.mendocinofarms.com/locations/609-main
    time_format = "%I:%M%p"
    # The site lists both LocalBusiness and Restaurant. Both of these are accepded by StructuredDataSpider by default, so only allowing one removes duplicates.
    wanted_types = ["LocalBusiness"]

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        for rule in ld_data["openingHoursSpecification"]:
            if rule.get("opens") and "am" not in rule["opens"]:
                rule["opens"] += "am"
            if rule.get("closes") and "pm" not in rule["closes"]:
                rule["closes"] += "pm"

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = response.url

        apply_category(Categories.RESTAURANT, item)

        yield item
