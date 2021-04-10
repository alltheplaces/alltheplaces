# -*-
import json
import scrapy
from scrapy.linkextractors import LinkExtractor

from locations.items import GeojsonPointItem


class ToyotaSpider(scrapy.Spider):
    name = "toyota"
    item_attributes = {
        "brand": "Toyota",
        "brand_wikidata": "Q53268",
    }
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
        info = j["showDealerLocatorDataArea"]["dealerLocator"][0][
            "dealerLocatorDetail"
        ][0]
        contact = info["dealerParty"]["specifiedOrganization"]["primaryContact"][0]
        lat = info["proximityMeasureGroup"]["geographicalCoordinate"][
            "latitudeMeasure"
        ]["value"]
        lon = info["proximityMeasureGroup"]["geographicalCoordinate"][
            "longitudeMeasure"
        ]["value"]
        ref = info["dealerParty"]["partyID"]["value"]
        name = info["dealerParty"]["specifiedOrganization"]["companyName"]["value"]

        addr_full = contact["postalAddress"]["lineOne"]["value"]
        city = contact["postalAddress"]["cityName"]["value"]
        country = contact["postalAddress"]["countryID"]
        postcode = contact["postalAddress"]["postcode"]["value"]
        state = contact["postalAddress"]["stateOrProvinceCountrySubDivisionID"]["value"]

        phone = contact["telephoneCommunication"][0]["completeNumber"]["value"]
        website = contact["uricommunication"][0]["uriid"]["value"]

        return GeojsonPointItem(
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
        )

