import json
from typing import Any, Iterable

from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import SitemapSpider
from w3lib.url import url_query_parameter

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class LaBoutiqueDuCoiffeurSpider(SitemapSpider, StructuredDataSpider):
    name = "la_boutique_du_coiffeur"
    item_attributes = {
        "brand": "La Boutique du Coiffeur",
        "brand_wikidata": "Q104600156",
        "name": "La Boutique du Coiffeur",
    }
    sitemap_urls = ["https://www.laboutiqueducoiffeur.com/fr-fr/sitemap-google?name=sitemap-storeSitemap"]
    sitemap_rules = [(r"/fr-fr/m/[^/]+-\d+$", "parse_sd")]
    search_for_email = False
    search_for_image = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = url_query_parameter(response.url, "store_id")
        item["branch"] = item.pop("name")
        item.pop("email", None)
        if locations := response.xpath("//@data-locations").get():
            location = json.loads(locations)[0]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["country"] = (
                Selector(text=location["infoWindowHtml"]).xpath("//address/span/text()").get("").split()[-1]
            )
        item["opening_hours"] = OpeningHours()
        for rule in ld_data.get("openingHoursSpecification", []):
            item["opening_hours"].add_range(rule["dayOfWeek"].rsplit("/", 1)[-1], rule.get("open"), rule.get("close"))
        apply_category(Categories.SHOP_HAIRDRESSER_SUPPLY, item)
        yield item
