import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class ScotrailGBSpider(SitemapSpider):
    name = "scotrail_gb"
    item_attributes = {"operator": "ScotRail", "operator_wikidata": "Q18356161"}
    sitemap_urls = ["https://www.scotrail.co.uk/default/sub/sitemaps/content--station/sitemap.xml"]
    sitemap_rules = [(r"/plan-your-journey", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["extras"]["ref:crs"] = response.url.split("/")[-1]
        item["name"] = response.xpath("//h1/text()").get().replace("Station", "").strip()

        item["website"] = response.url

        for marker in DictParser.get_nested_key(
            json.loads(response.xpath('//script[@data-drupal-selector="drupal-settings-json"]/text()').get()), "markers"
        ):
            if marker["location_type"] == "location":
                item["lat"] = marker["lat"]
                item["lon"] = marker["lon"]
                break

        apply_category(Categories.TRAIN_STATION, item)

        yield item
