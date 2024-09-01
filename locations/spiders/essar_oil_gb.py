from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.google_url import extract_google_position
from locations.items import Feature


# TODO: Address data not consistent between pages
class EssarOilGBSpider(SitemapSpider):
    name = "essar_oil_gb"
    item_attributes = {"brand": "Essar", "brand_wikidata": "Q5399372"}
    sitemap_urls = ["https://www.essaroil.co.uk/sitemap.xml"]
    sitemap_rules = [(r"/our-forecourts/([^/]+)/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()

        extract_google_position(item, response)

        if fuels := response.xpath("//p/*[contains(., 'Fuels')]/following-sibling::span/text()").getall():
            apply_yes_no("fuel:unleaded", item, any("Unleaded" in f for f in fuels))
            apply_yes_no(Fuel.DIESEL, item, any("Diesel" in f for f in fuels))
            apply_yes_no(Fuel.OCTANE_99, item, any("99" in f for f in fuels))

        apply_category(Categories.FUEL_STATION, item)

        item["ref"] = item["website"] = response.url

        yield item
