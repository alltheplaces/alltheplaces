from typing import Iterable

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser


class SpotlightSpider(SitemapSpider):
    name = "spotlight"
    item_attributes = {"brand": "Spotlight", "brand_wikidata": "Q105960982"}
    sitemap_urls = [
        "https://www.spotlightstores.com/sitemap/store/store-sitemap.xml",
        "https://www.spotlightstores.com/nz/sitemap/store/store-sitemap.xml",
        "https://www.spotlightstores.com/sg/sitemap/store/store-sitemap.xml",
    ]
    sitemap_rules = [(r"/store/[-\w]+/[-\w]+/[-\w]+$", "parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False, "DUPEFILTER_CLASS": "scrapy.dupefilters.BaseDupeFilter"}

    def parse(self, response: Response) -> Iterable[Feature]:
        store_json = response.xpath('//script[@id="storeJson"]/text()').get()
        item = LinkedDataParser.parse_ld(
            chompjs.parse_js_object(
                store_json.split("const jsonLd =", 1)[1].split('"openingHoursSpecification"')[0].rstrip().rstrip(",")
                + "}"
            )
        )
        item["ref"] = response.xpath('//div[@id="maps_canvas"]/@data-storeid').get()
        item["branch"] = item.pop("name").removeprefix("Spotlight ")
        item["website"] = response.url

        item["opening_hours"] = OpeningHours()
        for rule in chompjs.parse_js_object(store_json.split("const storeData =", 1)[1])["openingHoursRaw"]:
            item["opening_hours"].add_range(
                DAYS_EN[rule["dayOfWeek"]], rule["opens"], rule["closes"], time_format="%I:%M%p"
            )

        apply_category(Categories.SHOP_FABRIC, item)

        yield item
