from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS_DK, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class SkoringenDKNOSpider(SitemapSpider, StructuredDataSpider):
    name = "skoringen_dk_no"
    item_attributes = {"brand": "Skoringen", "brand_wikidata": "Q12001172"}
    sitemap_urls = ["https://www.skoringen.dk/sitemap.xml", "https://www.skoringen.no/sitemap.xml"]
    sitemap_rules = [(r"/find-butik/.+", "parse_sd"), (r"/finn-butikk/.+", "parse_sd")]

    def post_process_item(self, item, response: Response, ld_data, **kwargs):
        item["phone"] = response.xpath('//*[contains(@href, "tel:")]/text()').get()
        item["website"] = item["ref"] = response.url
        apply_category(Categories.SHOP_SHOES, item)
        extract_google_position(item, response)
        item["branch"] = item.pop("name").removeprefix("Skoringen, ")
        item["opening_hours"] = OpeningHours()
        for row in response.xpath("//app-opening-hours-row"):
            item["opening_hours"].add_ranges_from_string(
                " ".join(
                    row.xpath('.//*[contains(@class, "__week-day") or contains(@class, "__hours")]//text()').getall()
                ),
                days=DAYS_DK,
                closed=["lukket"],
            )
        item.pop("image", None)  # Generic placeholder image, not per-location
        yield item
