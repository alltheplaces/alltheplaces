import json
import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

ROCOMAMAS_CATEGORIES = {
    "ROCO": Categories.RESTAURANT,
    "ROCOGO": Categories.FAST_FOOD,
}


class RocomamasSpider(SitemapSpider):
    name = "rocomamas"
    sitemap_urls = ["https://rocomamas.com/sitemap_index.xml"]
    sitemap_rules = [(r"/restaurants/[^/]+/[^/]+$", "parse_restaurant")]
    brands = {
        "ROCO": {"brand": "RocoMamas", "brand_wikidata": "Q123034964"},
        "ROCOGO": {"brand": "RocoGo", "brand_wikidata": "Q123034964"},
    }

    def parse_restaurant(self, response):
        slug = response.url.rstrip("/").split("/")[-1]
        data = json.loads(response.xpath('//script[@id="__NUXT_DATA__"]/text()').get())
        shop = next(
            {k: data[v] for k, v in obj.items()}
            for obj in data
            if isinstance(obj, dict) and "slug" in obj and data[obj["slug"]] == slug
        )

        item = DictParser.parse(shop)
        item["ref"] = shop["key"]
        item["website"] = response.url
        brand_key = "ROCOGO" if slug.startswith("rocogo") else "ROCO"
        if brand_details := self.brands.get(brand_key):
            item.update(brand_details)
        item["branch"] = item.pop("name").replace(item["brand"], "").strip()
        if m := re.search(
            r"Opening hours(.*?)(?:Loved by|$)", " ".join(response.xpath("//body//text()").getall()), re.S
        ):
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(re.sub(r"\s+", " ", m.group(1)))
        apply_category(ROCOMAMAS_CATEGORIES[brand_key], item)

        yield item
