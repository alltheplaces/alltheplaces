import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT

RESTAURANTS = {
    "Bar + Block": ("Bar + Block", "Q117599706", Categories.RESTAURANT),
    "Beefeater": ("Beefeater", "Q4879766", Categories.RESTAURANT),
    "Brewers Fayre": ("Brewers Fayre", "Q4962678", Categories.PUB),
    "Chef & Brewer": ("Chef & Brewer", "Q5089491", Categories.PUB),
    "Table Table": ("Table Table", "Q16952586", Categories.RESTAURANT),
    "Thyme Bar & Grill": ("Thyme", "Q120645568", Categories.RESTAURANT),
    "Toby Carvery": ("Toby Carvery", "Q7811777", Categories.RESTAURANT),
}


class PremierInnSpider(SitemapSpider, StructuredDataSpider):
    name = "premier_inn"
    item_attributes = {"brand": "Premier Inn", "brand_wikidata": "Q2108626"}
    sitemap_urls = ("https://www.premierinn.com/sitemap-english.xml",)
    sitemap_rules = [(r"gb/en/hotels/[^/]+/[^/]+/[^/]+/[^/]+.html", "parse")]
    wanted_types = ["Hotel"]
    user_agent = BROWSER_DEFAULT

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if response.xpath('//section[@class="seo-hotel-listings"]'):
            self.crawler.stats.inc_value("{}/listing_page".format(self.name))
            # Page with multiple hotels that has the same URL format as single-hotel pages
            return

        blob = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if not blob:
            # There is currently 27 pages with Microdata, the rest have a next.js blob
            # The website is presumably moving away from Microdata :(
            # Once that happens we can remove half of this spider.
            self.crawler.stats.inc_value("{}/missing_blob".format(self.name))
            self.logger.warning("Missing blob {}".format(response.url))
            yield from self.parse_sd(response) or []
            return

        location = DictParser.get_nested_key(json.loads(blob), "hotelInformationBySlug")

        item = DictParser.parse(location)
        item["branch"] = item.pop("name")
        item["street_address"] = merge_address_lines(
            [
                location["address"]["addressLine1"],
                location["address"]["addressLine2"],
                location["address"]["addressLine3"],
            ]
        )
        item["ref"] = location["hotelId"]
        item["phone"] = location["contactDetails"]["phone"]
        item["website"] = response.url

        if item.get("country") == "United Kingdom (the)":
            item["country"] = "GB"

        self.brand(item, location["brand"])

        if restaurant := RESTAURANTS.get((location.get("restaurant") or {}).get("name")):
            rest = Feature()
            rest["lat"], rest["lon"], rest["country"] = item.get("lat"), item.get("lon"), item.get("country")
            rest["ref"] = "{}-restaurant".format(item["ref"])
            rest["name"] = rest["brand"] = restaurant[0]
            rest["brand_wikidata"] = restaurant[1]
            apply_category(restaurant[2], rest)
            yield rest

        yield item

    def post_process_item(self, item, response, ld_data, **kwargs):
        if isinstance(item["city"], list):
            item["city"] = item["city"][-1]
        item["ref"] = response.xpath('//meta[@itemprop="hotelCode"]/@content').get()
        item["branch"] = response.xpath('//ol[@class="nav breadcrumb--path"]/li[last()]/text()').get()

        if item.get("country") == "United Kingdom (the)":
            item["country"] = "GB"

        self.brand(item, response.xpath('//meta[@itemprop="hotelBrand"]/@content').get())

        yield item

    def brand(self, item: Feature, code: str):
        if code == "HUB":
            item["name"] = "hub by Premier Inn"
        elif code == "PI":  # Normal
            item["name"] = "Premier Inn"
        elif code == "PID":  # Normal DE
            item["name"] = "Premier Inn"
        elif code == "ZIP":
            item["name"] = "ZIP by Premier Inn"
        else:
            self.crawler.stats.inc_value("{}/unmapped_brand/{}".format(self.name, code))
            self.logger.warning("Unmapped brand {} ({})".format(code, item["website"]))
