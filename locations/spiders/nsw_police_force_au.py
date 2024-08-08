from scrapy.http import JsonRequest
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Request, Rule

from locations.categories import apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class NswPoliceForceAUSpider(CrawlSpider):
    name = "nsw_police_force_au"
    item_attributes = {"operator": "New South Wales Police Force", "operator_wikidata": "Q7011763"}
    allowed_domains = ["www.police.nsw.gov.au", "portal.spatial.nsw.gov.au"]
    start_urls = ["https://www.police.nsw.gov.au/about_us/regions_commands_districts"]
    rules = [
        Rule(
            LinkExtractor(
                allow=r"^https:\/\/www\.police\.nsw\.gov\.au\/about_us\/regions_commands_districts\/[\w\-]+$"
            ),
            follow=True,
        ),
        Rule(
            LinkExtractor(
                allow=r"^https:\/\/www\.police\.nsw\.gov\.au\/about_us\/regions_commands_districts\/(?:[\w\-]+\/){1,2}[\w\-]+_police_station$"
            ),
            callback="parse",
            follow=False,
        ),
    ]
    location_geometry = {}

    def start_requests(self):
        yield JsonRequest(
            url="https://portal.spatial.nsw.gov.au/server/rest/services/NSW_FOI_Emergency_Service_Facilities/FeatureServer/1/query?f=geojson",
            callback=self.parse_geometry,
        )

    def parse_geometry(self, response):
        for location in response.json()["features"]:
            self.location_geometry[location["properties"]["generalname"]] = location["geometry"]
        for url in self.start_urls:
            yield Request(url=url)

    def parse(self, response):
        properties = {
            "ref": response.url,
            "name": response.xpath('//h3[@class="p-hero__heading"]/text()').get(),
            "state": "NSW",
            "website": response.url,
        }
        if self.location_geometry.get(properties["name"].upper()):
            properties["geometry"] = self.location_geometry[properties["name"].upper()]
        for contact_line in response.xpath('//div[@itemprop="articleBody"]//p[2]//text()').getall():
            contact_line = contact_line.replace("\xa0", " ")
            if (
                "NOTE:" in contact_line.upper()
                or "NOT OPEN 24 HOURS" in contact_line.upper()
                or "FAX:" in contact_line.upper()
                or "VIEW PAC MAP" in contact_line.upper()
                or "POSTAL ADDRESS:" in contact_line.upper()
            ):
                continue
            elif "OPEN 24 HOURS" in contact_line.upper():
                properties["opening_hours"] = OpeningHours()
                properties["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
            elif "PHONE:" in contact_line.upper():
                properties["phone"] = contact_line.upper().split("PHONE:", 1)[1].strip()
            else:
                properties["addr_full"] = ", ".join(filter(None, [properties.get("addr_full"), contact_line.strip()]))
        apply_category({"amenity": "police"}, properties)
        yield Feature(**properties)
