from scrapy import Spider
from scrapy.http import JsonRequest

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class CorePowerYogaUSSpider(Spider):
    name = "corepower_yoga_us"
    item_attributes = {"brand": "Corepower Yoga", "brand_wikidata": "Q21015663"}
    allowed_domains = ["www.corepoweryoga.com"]
    start_urls = [
        "https://cdn.contentful.com/spaces/go5rjm58sryl/environments/master/entries?access_token=6b61TxCL9VW-1xwx-Oy4x9OOGMweRyBSDhaXCZM4d-o&include=10&limit=400&content_type=studios&select=sys.id,fields.region,fields.zenotiCenterId,fields.title,fields.slug,fields.address,fields.coordinates,fields.image,fields.openDate,fields.closed,fields.comingSoonStartDate"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        included_data = {}
        for extra_data in response.json()["includes"]["Entry"]:
            included_data[extra_data["sys"]["id"]] = extra_data["fields"]
        for location in response.json()["items"]:
            if location["fields"]["closed"]:
                continue
            properties = {
                "ref": location["sys"]["id"],
                "name": location["fields"]["title"],
                "lat": location["fields"]["coordinates"]["lat"],
                "lon": location["fields"]["coordinates"]["lon"],
                "website": "https://www.corepoweryoga.com/yoga-studios/" + location["fields"]["slug"],
            }
            address_data_ref = location["fields"]["address"]["sys"]["id"]
            if address_data_ref in included_data.keys():
                properties["street_address"] = clean_address(
                    [
                        included_data[address_data_ref].get("addressLine1"),
                        included_data[address_data_ref].get("addressLine2"),
                    ]
                )
                properties["city"] = included_data[address_data_ref]["city"]
                properties["state"] = included_data[address_data_ref]["state"]
                properties["postcode"] = included_data[address_data_ref]["zipCode"]
            yield Feature(**properties)
