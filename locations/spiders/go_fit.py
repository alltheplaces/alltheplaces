import json

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.structured_data_spider import StructuredDataSpider


class GoFitSpider(SitemapSpider, StructuredDataSpider):
    name = "go_fit"
    item_attributes = {"brand": "GO fit", "name": "GO fit"}
    sitemap_urls = [
        "https://go-fit.es/center-sitemap.xml",
        "https://go-fit.pt/center-sitemap.xml",
        # "https://go-fit.it/center-sitemaper-sitemap.xml", coming soon
    ]
    sitemap_rules = [(r"/centros/go-fit-[-\w]+", "parse")]
    wanted_types = ["ExerciseGym"]

    def parse(self, response: Response, **kwargs):
        if "ExerciseGym" in response.text:
            yield from self.parse_sd(response)
        else:
            location = json.loads(
                json.loads(
                    response.xpath('//script[@id="header-center-js-extra"]/text()').re_first(r"var js_vars = (.+);")
                )["center"]
            )
            item = DictParser.parse(location)
            item["ref"] = response.url
            item["lat"], item["lon"] = location.get("location", [None, None])
            item["branch"] = item.pop("name").removeprefix("GO fit ")
            apply_category(Categories.GYM, item)
            yield item

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("GO fit ")

        apply_category(Categories.GYM, item)

        yield item
