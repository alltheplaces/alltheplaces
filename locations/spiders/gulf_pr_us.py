import re
from html import unescape

from chompjs import parse_js_object
from scrapy import Request, Selector, Spider
from scrapy.http import FormRequest

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature


class GulfPRUSSpider(Spider):
    name = "gulf_pr_us"
    item_attributes = {"brand": "Gulf Oil", "brand_wikidata": "Q5617505"}
    allowed_domains = ["www.gulfoil.com"]

    @staticmethod
    def make_request(page: int) -> FormRequest:
        formdata = {
            "page": str(page),
            "field_geofield_proximity[value]": "500000",
            "units_of_measurements": "6371",
            "field_geofield_proximity[source_configuration][origin_address]": "new",
            "view_name": "station_locator_search_block",
            "view_display_id": "block_2",
        }
        return FormRequest(
            url="https://www.gulfoil.com/views/ajax?_wrapper_format=drupal_ajax",
            formdata=formdata,
            method="POST",
            meta={"page": page},
        )

    def start_requests(self):
        yield self.make_request(1)

    def parse(self, response):
        js_blob = parse_js_object(response.text.removeprefix("<textarea>").removesuffix("</textarea>"))
        results = None
        for command in js_blob:
            if command["command"] == "insert" and command["method"] == "replaceWith":
                results = Selector(text=command["data"])
                break

        if results is None:
            return

        for result in results.xpath('//section[@role="article"]'):
            url = "https://www.gulfoil.com" + result.xpath("./@about").get()
            meta = {
                "atm": result.xpath('.//li[contains(text(), "ATM")]/text()').get() is not None,
                "convenience_store": result.xpath('.//li[contains(text(), "Convenience Store")]/text()').get()
                is not None,
                "diesel": result.xpath('.//li[contains(text(), "Diesel Fuel")]/text()').get() is not None,
                "ethanol": result.xpath('.//li[contains(text(), "Ethanol")]/text()').get() is not None,
                "toilets": result.xpath('.//li[contains(text(), "Public Restrooms")]/text()').get() is not None,
            }
            yield Request(url=url, callback=self.parse_station, meta=meta)

        if len(results.xpath('//a[@rel="next"]')) > 0:
            yield self.make_request(response.meta["page"] + 1)

    def parse_station(self, response):
        properties = {
            "ref": response.xpath(
                '//div[contains(@class, "field--name-field-csv-id")]/div[@class="field__item"]/text()'
            ).get(),
            "name": unescape(response.xpath('//span[contains(@class, "field--name-title")]/text()').get()),
            "lat": re.findall(
                r"\-?[\d\.]+",
                response.xpath(
                    '//div[contains(@class, "field--name-field-geofield")]/div[@class="field__item"]/text()'
                ).get(),
            )[1],
            "lon": re.findall(
                r"\-?[\d\.]+",
                response.xpath(
                    '//div[contains(@class, "field--name-field-geofield")]/div[@class="field__item"]/text()'
                ).get(),
            )[0],
            "housenumber": response.xpath(
                '//div[contains(@class, "field--name-field-streetno")]/div[@class="field__item"]/text()'
            ).get(),
            "street": response.xpath(
                '//div[contains(@class, "field--name-field-site-street")]/div[@class="field__item"]/text()'
            ).get(),
            "city": response.xpath(
                '//div[contains(@class, "field--name-field-site-city")]/div[@class="field__item"]/text()'
            ).get(),
            "state": response.xpath(
                '//div[contains(@class, "field--name-field-site-state")]/div[@class="field__item"]/text()'
            ).get(),
            "postcode": response.xpath(
                '//div[contains(@class, "field--name-field-zipcode")]/div[@class="field__item"]/text()'
            ).get(),
            "phone": response.xpath(
                '//div[contains(@class, "field--name-field-phonenumber")]/div[@class="field__item"]/text()'
            ).get(),
            "website": response.url,
        }
        if properties["state"] == "PR":
            properties["country"] = "PR"
            properties.pop("state", None)
        else:
            properties["country"] = "US"
        apply_yes_no(Fuel.DIESEL, properties, response.meta["diesel"], False)
        apply_yes_no(Fuel.E85, properties, response.meta["ethanol"], False)
        apply_yes_no(Extras.TOILETS, properties, response.meta["toilets"], False)
        apply_yes_no(Extras.ATM, properties, response.meta["atm"], False)
        if response.meta["convenience_store"]:
            apply_category(Categories.SHOP_CONVENIENCE, properties)
        yield Feature(**properties)
