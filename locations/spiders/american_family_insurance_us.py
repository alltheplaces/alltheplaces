from typing import Any, Iterable
from urllib.parse import unquote

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class AmericanFamilyInsuranceUSSpider(SitemapSpider):
    name = "american_family_insurance_us"
    item_attributes = {"brand": "American Family Insurance", "brand_wikidata": "Q4743730", "country": "US"}
    sitemap_urls = ["https://www.amfam.com/sitemap.xml"]
    sitemap_rules = [(r"https://www\.amfam\.com/agents/[^/]+/[^/]+/[^/]+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        next_data = chompjs.parse_js_object(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        components = next_data["props"]["pageProps"]["layoutData"]["sitecore"]["route"]["placeholders"]["jss-main"][0][
            "placeholders"
        ]["sxa-agent-main"]

        full_name = None
        offices = []
        for component in components:
            fields = component.get("fields") or {}
            if component.get("componentName") == "LegacyAgentHero":
                full_name = fields.get("FullName", {}).get("value")
            elif component.get("componentName") == "LegacyAgentWebsiteOfficeLocations":
                offices = fields.get("Offices") or []

        agent_slug = response.url.rsplit("agents/", 1)[1].rstrip("/")

        for office in offices:
            # A satellite "office" with no real street address is a virtual-only
            # agency presence, not a physical location to map.
            street = office.get("StreetAddressLine1", {}).get("value", "").strip()
            if not street or street.upper() == "VIRTUAL AGENCY" or office.get("Donotshow", {}).get("value"):
                continue

            item = Feature()
            item["ref"] = "{}/{}".format(agent_slug, office.get("SortOrder", {}).get("value") or 1)
            item["branch"] = full_name
            item["lat"] = office.get("Latitude", {}).get("value")
            item["lon"] = office.get("Longitude", {}).get("value")
            item["street_address"] = " ".join(
                filter(None, [street, office.get("StreetAddressLine2", {}).get("value", "").strip()])
            )
            item["city"] = office.get("City", {}).get("value")
            item["state"] = office.get("State", {}).get("fields", {}).get("Value", {}).get("value")
            item["postcode"] = office.get("Zip", {}).get("value")
            item["website"] = response.url

            for pair in (office.get("Phones", {}).get("value") or "").split("&"):
                if pair.startswith("VOICE="):
                    item["phone"] = pair.split("=", 1)[1]

            if hours := office.get("OfficeHours", {}).get("value"):
                # A minority of records have their hours percent-encoded (e.g. "8%3A30%20AM").
                item["opening_hours"] = OpeningHours()
                for day_range in unquote(hours).split("&"):
                    day, _, time_range = day_range.partition("=")
                    open_time, _, close_time = time_range.partition("-")
                    item["opening_hours"].add_range(day, open_time.strip(), close_time.strip(), time_format="%I:%M %p")

            apply_category(Categories.OFFICE_INSURANCE, item)
            yield item
