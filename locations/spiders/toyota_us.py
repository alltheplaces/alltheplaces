import json

import scrapy
from scrapy.linkextractors import LinkExtractor

from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES


class ToyotaUSSpider(scrapy.Spider):
    name = "toyota_us"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    allowed_domains = ["www.toyota.com"]
    start_urls = ["https://www.toyota.com/dealers/directory/"]

    link_extractor = LinkExtractor(restrict_css=".dealership-state")

    def parse(self, response):
        for link in self.link_extractor.extract_links(response):
            yield scrapy.Request(link.url)

        for dealer_ref in response.xpath("//a/@data-code").getall():
            yield scrapy.Request(
                f"https://www.toyota.com/ToyotaSite/rest/dealerRefresh/locateDealers?&dealerCode={dealer_ref}",
                callback=self.parse_dealer,
            )

    def parse_dealer(self, response):
        j = json.loads(response.text)
        info = j["showDealerLocatorDataArea"]["dealerLocator"][0]["dealerLocatorDetail"][0]
        contact = info["dealerParty"]["specifiedOrganization"]["primaryContact"][0]
        lat = info["proximityMeasureGroup"]["geographicalCoordinate"]["latitudeMeasure"]["value"]
        lon = info["proximityMeasureGroup"]["geographicalCoordinate"]["longitudeMeasure"]["value"]
        ref = info["dealerParty"]["partyID"]["value"]
        name = info["dealerParty"]["specifiedOrganization"]["companyName"]["value"]

        addr_full = contact["postalAddress"]["lineOne"]["value"]
        city = contact["postalAddress"]["cityName"]["value"]
        country = contact["postalAddress"]["countryID"]
        postcode = contact["postalAddress"]["postcode"]["value"]
        state = contact["postalAddress"]["stateOrProvinceCountrySubDivisionID"]["value"]

        phone = contact["telephoneCommunication"][0]["completeNumber"]["value"]
        website = contact["uricommunication"][0]["uriid"]["value"]
        opening_hours = (
            self.parse_hours(info["hoursOfOperation"][0]["daysOfWeek"]) if "hoursOfOperation" in info else None
        )

        return Feature(
            ref=ref,
            lat=lat,
            lon=lon,
            name=name,
            country=country,
            state=state,
            city=city,
            addr_full=addr_full,
            postcode=postcode,
            phone=phone,
            website=website,
            opening_hours=opening_hours,
        )

    def parse_hours(self, days_of_week_obj):
        opening_hours = OpeningHours()
        for x in days_of_week_obj:
            if "availabilityStartTimeMeasure" not in x:
                continue
            day = x["dayOfWeekCode"][:2]
            open_hr, open_min = divmod(x["availabilityStartTimeMeasure"]["value"], 60)
            close_hr, close_min = divmod(x["availabilityEndTimeMeasure"]["value"], 60)
            opening_hours.add_range(day, f"{open_hr}:{open_min:02}", f"{close_hr}:{close_min:02}")
        return opening_hours.as_opening_hours()
