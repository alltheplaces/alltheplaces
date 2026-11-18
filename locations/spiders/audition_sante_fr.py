import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class AuditionSanteFRSpider(SitemapSpider):
    name = "audition_sante_fr"
    item_attributes = {"brand": "Audition Santé", "brand_wikidata": "Q141156321"}
    sitemap_urls = ["https://www.auditionsante.fr/sitemap.xml"]
    sitemap_rules = [(r"/centre-auditif/[^/]+/[^/]+/[^/]+_s_\w+/$", "parse")]

    def parse(self, response):
        components = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())["props"]["pageProps"][
            "data"
        ]["components"]
        store = components[0]["slides"][0]["storeConfig"]["storeData"]
        store.pop("region")  # department, not region
        item = DictParser.parse(store)
        coordinates = next(c for c in components if c["__typename"] == "WebsiteLocationMapSection")["mapData"][0][
            "coordinate"
        ]
        item["lat"], item["lon"] = coordinates["latitude"], coordinates["longitude"]
        item["street_address"] = merge_address_lines([store["addressLine1"], store["addressLine2"]])
        item["branch"] = (
            item.pop("name")
            .removeprefix("Audioprothésiste ")
            .removesuffix(" Audition Santé")
            .removesuffix(" AuditionSanté")
        )
        item["website"] = response.url

        item["opening_hours"] = OpeningHours()
        for day in store["hours"]:
            if day["isClosed"]:
                item["opening_hours"].set_closed(day["day"])
            for interval in day["openIntervals"] or []:
                item["opening_hours"].add_range(day["day"], interval["start"], interval["end"])

        apply_category(Categories.SHOP_HEARING_AIDS, item)
        yield item
