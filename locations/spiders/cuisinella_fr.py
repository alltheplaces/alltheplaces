import html

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CuisinellaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "cuisinella_fr"
    item_attributes = {"brand": "Cuisinella", "brand_wikidata": "Q3007012"}
    sitemap_urls = ["https://www.ma.cuisinella/robots.txt"]
    sitemap_rules = [(r"/fr-fr/magasins/[\w-]+/[\w-]+", "parse")]

    def pre_process_data(self, ld_data: dict, **kwargs):
        # Currently 100% malformed eg
        # {
        #     "@type": "GeoCoordinates",
        #     "latitude": "16.242304, -61.562389?.Latitude",
        #     "longitude": "16.242304, -61.562389?.Longitude",
        # }

        if (ld_data.get("geo") or {}).get("latitude").endswith("?.Latitude"):
            ld_data["geo"]["latitude"], ld_data["geo"]["longitude"] = (
                ld_data["geo"]["latitude"].split("?", 1)[0].split(", ", 1)
            )

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["image"] = None
        item["branch"] = html.unescape(item.pop("name"))
        yield item
