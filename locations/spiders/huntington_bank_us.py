from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class HuntingtonBankUSSpider(SitemapSpider, StructuredDataSpider):
    name = "huntington_bank_us"
    item_attributes = {"brand": "Huntington Bank", "brand_wikidata": "Q798819"}
    allowed_domains = ["www.huntington.com"]
    sitemap_urls = ["https://www.huntington.com/~/media/SEO_Files/sitemap.xml"]
    sitemap_rules = [(r"branch-info", "parse_sd")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        hours = OpeningHours()
        opening_hours = ld_data.get("openingHoursSpecification") or []
        for row in opening_hours:
            day = row["dayOfWeek"].split("/")[-1][:2]
            hours.add_range(day, row["opens"], row["closes"], "%H:%M:%S")

        item["ref"] = response.xpath("//@data-branch-id").get()
        item["opening_hours"] = hours.as_opening_hours()

        if fax_number := ld_data.get("faxNumber"):
            item["extras"]["fax"] = fax_number

        apply_category(Categories.BANK, item)

        yield item
