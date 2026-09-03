from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class MmaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "mma_fr"
    item_attributes = {"brand": "MMA", "brand_wikidata": "Q3331046"}
    sitemap_urls = ["https://agence.mma.fr/home.sitemap.xml"]
    wanted_types = ["InsuranceAgency"]
    drop_attributes = ["facebook", "image"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = (item.pop("name", "") or "").removeprefix("AGENCE D'ASSURANCE MMA ")
        item["opening_hours"] = self.parse_opening_hours(ld_data)
        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item

    def parse_opening_hours(self, ld_data: dict) -> OpeningHours:
        oh = OpeningHours()
        for l in ld_data["openingHours"]:
            day, times = l.split(" ", 1)
            if times == "Fermée":
                oh.set_closed(day)
            else:
                for t in times.strip().split(" "):
                    oh.add_range(day, *t.split("-"))
        return oh
