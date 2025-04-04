import chompjs
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class UfcGymUSSpider(SitemapSpider):
    name = "ufc_gym_us"
    item_attributes = {"brand": "UFC GYM", "brand_wikidata": "Q122511683"}
    sitemap_urls = ["https://www.ufcgym.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/[-\w]+$", "parse")]

    def sitemap_filter(self, entries):
        for entry in entries:
            if "list" not in entry["loc"]:
                yield entry

    def parse(self, response, **kwargs):
        if data := response.xpath('//script[@id="__NEXT_DATA__"]/text()').get():
            if location := chompjs.parse_js_object(data)["props"]["pageProps"].get("location"):
                location.update(location.pop("position"))
                item = DictParser.parse(location)
                item["street_address"] = item.pop("street", "")
                item["branch"] = item.pop("name")
                item["website"] = response.url
                apply_category(Categories.GYM, item)
                yield item
