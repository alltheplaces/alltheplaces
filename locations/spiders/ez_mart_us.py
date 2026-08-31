import io
import json
import zipfile
from typing import Any, Iterable

import chompjs
from scrapy import Request, Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


def store_ref(value: Any) -> str | None:
    if value in (None, "null", ""):
        return None
    return str(int(float(value)))


class EzMartUSSpider(Spider):
    """
    EZ Mart is a chain of convenience stores in Michigan operated by
    Blarney Castle Oil. The store finder used to be a WP Go Maps
    WordPress plugin, but is now a Google My Maps embed. Coordinates are
    only available from the My Maps viewer's embedded JSON, while the
    postcode and 24 hour flag are only available from the KML export, so
    both are fetched and merged by store number.
    """

    name = "ez_mart_us"
    item_attributes = {"brand": "EZ Mart"}
    allowed_domains = ["blarneycastleoil.com", "google.com"]
    start_urls = ["https://www.blarneycastleoil.com/ez-mart"]

    def parse(self, response: Response) -> Iterable[Request]:
        if mid := response.xpath('//iframe[contains(@src, "google.com/maps/d/")]/@src').re_first(r"[?&]mid=([\w-]+)"):
            yield Request(f"https://www.google.com/maps/d/kml?mid={mid}", callback=self.parse_kml)

    def parse_kml(self, response: Response) -> Iterable[Request]:
        kmz = zipfile.ZipFile(io.BytesIO(response.body))
        kml = kmz.open(kmz.filelist[0]).read()
        selector = Selector(text=kml, type="xml")
        selector.remove_namespaces()

        extra_fields = {}
        for placemark in selector.xpath("//Placemark"):
            ref = store_ref(placemark.xpath('.//Data[@name="Store Number"]/value/text()').get())
            if not ref:
                continue
            extra_fields[ref] = {
                "postcode": placemark.xpath('.//Data[@name="Zip"]/value/text()').get(),
                "twentyfour_hour": placemark.xpath('.//Data[@name="24 HR"]/value/text()').get() == "Y",
            }

        mid = response.url.split("mid=")[1].split("&")[0]
        yield Request(
            f"https://www.google.com/maps/d/viewer?femb=1&mid={mid}",
            callback=self.parse_stores,
            cb_kwargs={"extra_fields": extra_fields},
        )

    def parse_stores(self, response: Response, extra_fields: dict) -> Iterable[Feature]:
        raw = response.xpath('//script[contains(text(), "_pageData")]/text()').re_first(r"var _pageData = (.*);")
        page_data = chompjs.parse_js_object(json.loads(raw))
        stores = page_data[1][6][0][12][0][13][0]
        for store in stores:
            yield from self.parse_store(store, extra_fields)

    def parse_store(self, store: list, extra_fields: dict) -> Iterable[Feature]:
        lat, lon = store[1][0][0]

        fields: dict[str, Any] = {}
        if (name_field := store[5][0]) and name_field[1]:
            fields["name"] = name_field[1][0]
        for label, values, _kind in store[5][3]:
            cleaned = [v for v in values if v not in (None, "null")]
            fields[label] = cleaned[-1] if cleaned else None

        ref = store_ref(fields.get("Store Number"))

        item = Feature()
        item["ref"] = ref
        item["name"] = fields.get("name")
        item["lat"] = lat
        item["lon"] = lon
        item["street_address"] = fields.get("Address")
        item["city"] = fields.get("City")
        item["state"] = "MI"
        item["phone"] = fields.get("Phone #")

        apply_category(Categories.SHOP_CONVENIENCE, item)

        extra = extra_fields.get(ref, {})
        if extra.get("postcode"):
            item["postcode"] = extra["postcode"]
        if extra.get("twentyfour_hour"):
            oh = OpeningHours()
            oh.add_days_range(DAYS, "00:00", "23:59")
            item["opening_hours"] = oh

        yield item
