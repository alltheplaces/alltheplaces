from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Extras, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

SERVICE_TAGS = {
    "PARKING": Extras.PARKING,
    "RESTAURANT": "food",
    "SNACK": "food",
    "DRINK": "drink",
    "SITTING_AREA": Extras.INDOOR_SEATING,
    "AIR_CONDITIONING": Extras.AIR_CONDITIONING,
}


class EvaSpider(SitemapSpider, StructuredDataSpider):
    name = "eva"
    item_attributes = {"brand": "EVA", "brand_wikidata": "Q138313401"}
    sitemap_urls = ["https://www.eva.gg/sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+$", "parse_sd")]
    wanted_types = ["AmusementCenter"]
    drop_attributes = {"image", "twitter"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("EVA ")
        if item.get("facebook") == "https://www.facebook.com/EVAggFR":
            item["facebook"] = None
        for code in response.css('[data-sentry-component="LocationServiceIcon"] img::attr(alt)').getall():
            if code in SERVICE_TAGS:
                apply_yes_no(SERVICE_TAGS[code], item, True)
        yield item
