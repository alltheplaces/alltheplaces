import re

from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.spiders.vapestore_gb import clean_address


# TODO: if ever the project was to gain the concept of a secondary observation then it
#       could be that this method is amended to mark the POI as such?
def ignore(item):
    """
    Does this UK health record reference a POI which we already have via a more direct brand spider?
    In the UK various health care services may be provided by companies big and small. The NHS maintains
    a directory which we query with this spider.
    :param item: the POI to inspect
    :return: True if we think this POI is handled by a direct brand spider
    """
    name = item["name"].lower().strip().replace(",", " ")
    for ignore_str in [
        "asda ",
        "boots ",
        "lloyds ",
        "morrisons ",
        "mydentist ",
        "optical express",
        "specsavers ",
        "superdrug ",
        "tesco ",
        "vision express",
        "your local boots ",
    ]:
        if name.startswith(ignore_str):
            return True
    return False


class NHSScotlandGBSpider(Spider):
    name = "nhs_scotland_gb"
    item_attributes = {"brand": "NHS Scotland", "brand_wikidata": "Q16933548"}
    services = {
        "dental-services": Categories.DENTIST,
        "aes-and-minor-injuries-units": Categories.CLINIC_URGENT,
        "gp-practices": Categories.DOCTOR_GP,
        "hospitals": Categories.HOSPITAL,
        "opticians": Categories.SHOP_OPTICIAN,
        "pharmacies": Categories.PHARMACY,
    }
    download_delay = 0.2

    def start_requests(self):
        for service in self.services.keys():
            yield Request(
                "https://www.nhsinform.scot/scotlands-service-directory/{}?page=1&sortby=_distance&sortdir=Asc".format(
                    service
                ),
                cb_kwargs=dict(service=service),
            )

    def parse(self, response, service):
        for link in response.xpath('//h2[@class="nhsuk-heading-m"]/a/@href').getall():
            yield Request(link, callback=self.parse_service, cb_kwargs=dict(service=service))
        for link in response.xpath('//a[contains(@class, "pagination__link")]/@href').getall():
            link = re.sub(r"\?page=\d+&page=", "?page=", link)
            yield Request(link, callback=self.parse, cb_kwargs=dict(service=service))

    def parse_service(self, response, service):
        item = Feature()
        extract_google_position(item, response)
        apply_category(self.services.get(service), item)
        item["name"] = response.xpath('//input[@id="ServiceName"]/@value').get().strip()
        item["website"] = item["ref"] = response.url
        item["postcode"] = response.xpath('//input[@id="ServicePostcode"]/@value').get().strip()
        # TODO opening_hours = response.xpath('//div[@class="panel-times"]//dd').getall()
        item["addr_full"] = clean_address(response.xpath("//address/text()").getall())
        if external_url := response.xpath('//a[@class="external"]/@href').get():
            item["website"] = external_url
        if not ignore(item):
            yield item
