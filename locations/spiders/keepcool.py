import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class KeepcoolSpider(SitemapSpider):
    name = "keepcool"
    item_attributes = {"brand": "KeepCool", "brand_wikidata": "Q100146251"}
    sitemap_urls = ["https://www.keepcool.fr/sitemap.xml"]
    sitemap_rules = [("/s/salle-de-sport-", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["branch"] = response.xpath("//h1").xpath("normalize-space()").get().removeprefix("SALLE DE SPORT")
        address_detail = response.xpath('//*[@class="d-flex-dir-wrp_gap-1"]//text()').getall()
        item["street_address"] = address_detail[0]
        item["postcode"] = address_detail[1]
        # City is not always present. Get it where we can.
        # Sometimes city is in branch name but this is not reliable as it sometimes contains city area/address lines too.
        if len(address_detail) > 2:
            item["city"] = address_detail[2]
        item["ref"] = item["website"] = response.url
        item["lat"], item["lon"] = re.search(
            r"LatLng\(\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\s*\);", response.text
        ).groups()
        apply_category(Categories.GYM, item)
        yield item
