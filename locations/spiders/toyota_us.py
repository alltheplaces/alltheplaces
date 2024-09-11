import json
from datetime import timedelta

from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import SocialMedia, get_social_media, set_social_media
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES


class ToyotaUSSpider(JSONBlobSpider):
    name = "toyota_us"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES

    start_urls = ["https://www.toyota.com/dealers/directory/"]

    URI_MAPPING = {
        "Website": "website",
        "Facebook": SocialMedia.FACEBOOK,
        "Twitter": SocialMedia.TWITTER,
        "Youtube": SocialMedia.YOUTUBE,
        # "Google":
        # "Yahoo Local"
        "Yelp": SocialMedia.YELP,
        "Instagram": SocialMedia.INSTAGRAM,
        "Email": "email",
        "Pinterest": SocialMedia.PINTEREST,
        "LinkedIn": SocialMedia.LINKEDIN,
    }
    CONTACT_TYPES = {
        "Main Dealer": "dealer",
        "Service": "service",
        "Parts": "parts",
        "Sales": "sales",
        "Parts and Service Departments": "service",
    }
    HOURS_TYPES = {
        "General": "general",
        "Service": "service",
        "Parts": "parts",
    }

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.fetch_states)

    def fetch_states(self, response):
        for state in response.xpath('.//li[@class="state-name"]'):
            link = state.xpath("a/@href").get()
            name = state.xpath("a/@title").get()
            yield Request(url="https://www.toyota.com" + link, callback=self.fetch_cities, meta={"state": name})

    def fetch_cities(self, response):
        for city in response.xpath(".//li[@data-city-name]/@data-city-name").getall():
            yield Request(
                url=f"https://www.toyota.com/service/tcom/dealerRefresh/city/{city.lower().replace('.', '')}/state/{response.meta['state'].lower()}",
                callback=self.parse,
            )

    def extract_json(self, response):
        dealers = json.loads(response.text)["showDealerLocatorDataArea"]["dealerLocator"]
        if len(dealers) == 0:
            self.crawler.stats.inc_value(f"atp/{self.name}/no_dealers_found/{response.url}")
            return []
        else:
            return dealers[0]["dealerLocatorDetail"]

    def post_process_item(self, item, response, location):
        apply_category(Categories.SHOP_CAR, item)
        item["ref"] = location["dealerParty"]["partyID"]["value"]
        item["name"] = location["dealerParty"]["specifiedOrganization"]["companyName"]["value"]

        item["lat"] = location["proximityMeasureGroup"]["geographicalCoordinate"]["latitudeMeasure"]["value"]
        item["lon"] = location["proximityMeasureGroup"]["geographicalCoordinate"]["longitudeMeasure"]["value"]

        contacts = location["dealerParty"]["specifiedOrganization"]["primaryContact"]

        unknown_contacts = [
            contact for contact in contacts if contact["departmentName"]["value"] not in self.CONTACT_TYPES.keys()
        ]
        for contact in unknown_contacts:
            if "jobTitle" not in contact:
                self.crawler.stats.inc_value(
                    f"atp/{self.name}/unknown_contact_name/{contact['departmentName']['value']}"
                )

        for contact_type, prefix in self.CONTACT_TYPES.items():
            try:
                contact = [contact for contact in contacts if contact["departmentName"]["value"] == contact_type][0]
            except IndexError:
                continue
            if "postalAddress" in contact:
                self.parse_address(item, contact.get("postalAddress"))
            self.parse_contact(item, contact, prefix)

        for hours_type in location["hoursOfOperation"]:
            self.parse_hours(item, hours_type)

        yield item

    def parse_address(self, item, address):
        for key, location_value in {
            "city": address["cityName"]["value"],
            "street_address": address["lineOne"]["value"],
            "country": address["countryID"],
            "postcode": address["postcode"]["value"],
            "state": address["stateOrProvinceCountrySubDivisionID"]["value"],
        }.items():
            if item.get(key) is None:
                item[key] = location_value

    def parse_contact(self, item, contact, prefix):
        phones = []
        faxes = []
        for number in contact["telephoneCommunication"]:
            if number["channelCode"]["value"] == "Phone":
                phones.append(number["completeNumber"]["value"])
            elif number["channelCode"]["value"] == "Fax":
                phones.append(number["completeNumber"]["value"])
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/unknown_contact_type/{number['channelCode']['value']}")
        if item.get("phone") is None and phones != []:
            item["phone"] = "; ".join(phones)
        elif phones != []:
            item["extras"][prefix + ":phone"] = "; ".join(phones)
        if item["extras"].get("fax") is None and faxes != []:
            item["extras"]["fax"] = "; ".join(faxes)
        elif faxes != []:
            item["extras"][prefix + ":fax"] = "; ".join(faxes)

        for uri in contact["uricommunication"]:
            if match := self.URI_MAPPING.get(uri["channelCode"]["value"]):
                if get_social_media(item, match) is None:
                    set_social_media(item, match, uri["uriid"]["value"])
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/unknown_uri/{uri['channelCode']['value']}")

    def parse_hours(self, item, hours_type):
        oh = OpeningHours()
        for day_times in hours_type["daysOfWeek"]:
            if "availabilityStartTimeMeasure" in day_times:
                units_start = day_times["availabilityStartTimeMeasure"]["unitCode"]
                units_end = day_times["availabilityEndTimeMeasure"]["unitCode"]
                oh.add_range(
                    day_times["dayOfWeekCode"],
                    str(timedelta(minutes=day_times["availabilityStartTimeMeasure"]["value"])),
                    str(timedelta(minutes=day_times["availabilityEndTimeMeasure"]["value"])),
                    time_format="%H:%M:%S",
                )
                if units_start != "MINUTE":
                    self.crawler.stats.inc_value(f"atp/{self.name}/unknown_time_unit/{units_start}")
                if units_end != "MINUTE":
                    self.crawler.stats.inc_value(f"atp/{self.name}/unknown_time_unit/{units_end}")
            else:
                oh.set_closed(day_times["dayOfWeekCode"])

        if suffix := self.HOURS_TYPES.get(hours_type["hoursTypeCode"]):
            if item.get("opening_hours") is None:
                item["opening_hours"] = oh.as_opening_hours()
            else:
                item["extras"]["opening:hours:" + suffix] = oh.as_opening_hours()
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_opening_hours_type/{hours_type['hoursTypeCode']}")
