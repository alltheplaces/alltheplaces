import json

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class LoxamFrSpider(SitemapSpider):
    name = "loxam_fr"
    item_attributes = {"brand": "Loxam", "brand_wikidata": "Q3264407"}
    allowed_domains = ["agence.loxam.fr"]
    sitemap_urls = [
        "https://agence.loxam.fr/locationsitemap1.xml",
        "https://agence.loxam.fr/locationsitemap2.xml",
        "https://agence.loxam.fr/locationsitemap3.xml",
    ]
    sitemap_rules = [("", "parse_store")]
    requires_proxy = True

    def parse_hours(self, item, store_hours):
        oh = OpeningHours()
        for hours in store_hours.split(","):
            if hours:
                day = hours.split(" ")[0]
                open_time = hours.split(" ")[1].split("-")[0]
                close_time = hours.split(" ")[1].split("-")[1]
                oh.add_range(day, open_time, close_time, "%H:%M")
            item["opening_hours"] = oh.as_opening_hours()

    def parse_store(self, response):
        script_content = response.xpath('//script[contains(@type,"application/ld+json")]')
        for content in script_content:
            json_data = json.loads(content.xpath("./text()").get(), strict=False)
            if "address" in json_data:
                item = DictParser.parse(json_data)
                item["ref"] = json_data["url"].split("-")[0][1:]
                self.parse_hours(
                    item, json_data["openingHours"].replace(" - ", "-").replace("  ", "").replace("\n", "")
                )
                item["website"] = response.request.url
                yield item
