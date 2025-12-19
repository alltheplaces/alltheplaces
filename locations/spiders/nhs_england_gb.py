from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.spiders.nhs_scotland_gb import ignore
from locations.structured_data_spider import StructuredDataSpider


class NhsEnglandGBSpider(SitemapSpider, StructuredDataSpider):
    name = "nhs_england_gb"
    sitemap_urls = [
        # Dentists and GPs get their own sitemap files, with structured data, great:
        "https://www.nhs.uk/sitemap-profiles-dentist.xml",
        "https://www.nhs.uk/sitemap-profiles-gp.xml",
        # TODO: opticians, pharmacies and hospitals are exposed via a search interface
        # All available services: https://www.nhs.uk/nhs-services/
    ]
    wanted_types = ["Dentist", "Physician", "LocalBusiness"]

    def pre_process_data(self, ld_data, **kwargs):
        for rule in ld_data.get("openingHoursSpecification", []):
            rule["dayOfWeek"] = rule["dayOfWeek"]["name"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = item["website"].replace("http://", "https://")
        if not item["website"].startswith("https://"):
            item["website"] = response.url
        item["addr_full"] = item.pop("street_address")
        if "/services/gp-surgery/" in response.url:
            apply_category(Categories.DOCTOR_GP, item)
        elif "/services/dentist/" in response.url:
            apply_category(Categories.DENTIST, item)
        if not ignore(item):
            yield item
