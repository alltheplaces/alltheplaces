from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class HindustanPetroleumINSpider(SitemapSpider, StructuredDataSpider):
    name = "hindustanpetroleum_in"
    item_attributes = {"brand": "Hindustan Petroleum", "brand_wikidata": "Q1619375"}
    sitemap_urls = ["https://petrolpump.hpretail.in/files/enterprise/sitemap/google/96681/locations.xml"]
    sitemap_rules = [("/Home", "parse_sd")]
    wanted_types = ["GasStation"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = ld_data.get("alternateName")
        item["name"] = None
        fuel = response.xpath('//*[@id="speakableCategoriesContent"]/*/text()').getall()
        apply_yes_no(Fuel.DIESEL, item, any("Diesel" in f for f in fuel))
        apply_category(Categories.FUEL_STATION, item)
        yield item
