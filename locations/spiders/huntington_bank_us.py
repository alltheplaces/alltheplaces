from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class HuntingtonBankUSSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "huntington_bank_us"
    item_attributes = {"brand": "Huntington Bank", "brand_wikidata": "Q798819"}
    allowed_domains = ["www.huntington.com"]
    sitemap_urls = ["https://www.huntington.com/~/media/SEO_Files/sitemap.xml"]
    sitemap_rules = [(r"branch-info", "parse_sd")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        hours = OpeningHours()
        opening_hours = ld_data.get("openingHoursSpecification") or []
        for row in opening_hours:
            day = row["dayOfWeek"].split("/")[-1][:2]
            hours.add_range(day, row["opens"], row["closes"], "%H:%M:%S")

        item["ref"] = response.xpath("//@data-branch-id").get()
        item["opening_hours"] = hours.as_opening_hours()
        item["extras"]["fax"] = ld_data.get("faxNumber")

        apply_category(Categories.BANK, item)

        # Check if branch has an ATM based on department field
        department = ld_data.get("department")
        if isinstance(department, dict) and department.get("@type") == "AutomatedTeller":
            apply_yes_no(Extras.ATM, item, True)

            atm_hours = OpeningHours()
            for row in department.get("openingHoursSpecification") or []:
                day = row["dayOfWeek"].split("/")[-1][:2]
                atm_hours.add_range(day, row["opens"], row["closes"], "%H:%M:%S")

            item["extras"]["opening_hours:atm"] = atm_hours.as_opening_hours()

        yield item
