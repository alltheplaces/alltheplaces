from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class HuntingtonBankUSSpider(SitemapSpider, StructuredDataSpider):
    name = "huntington_bank_us"
    item_attributes = {"brand": "Huntington Bank", "brand_wikidata": "Q798819", "extras": Categories.BANK.value}
    allowed_domains = ["www.huntington.com"]
    sitemap_urls = ["https://www.huntington.com/~/media/SEO_Files/sitemap.xml"]
    sitemap_rules = [(r"branch-info", "parse_sd")]
    user_agent = BROWSER_DEFAULT

    def post_process_item(self, item, response, ld_data):
        hours = OpeningHours()
        opening_hours = ld_data.get("openingHoursSpecification") or []
        for row in opening_hours:
            day = row["dayOfWeek"].split("/")[-1][:2]
            hours.add_range(day, row["opens"], row["closes"], "%H:%M:%S")

        item["ref"] = response.xpath("//@data-branch-id").get()
        item["opening_hours"] = hours.as_opening_hours()

        if fax_number := ld_data.get("faxNumber"):
            item["extras"]["fax"] = fax_number

        yield item
