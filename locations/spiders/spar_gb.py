from typing import Any, AsyncIterator

import scrapy
from scrapy.http import JsonRequest, Response
from twisted.python.failure import Failure

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.spar_aspiag import SPAR_SHARED_ATTRIBUTES

API_URL = "https://www.spar.co.uk/umbraco/api/storelocationapi/stores"


class SparGBSpider(scrapy.Spider):
    name = "spar_gb"
    item_attributes = SPAR_SHARED_ATTRIBUTES
    custom_settings = {"ROBOTSTXT_OBEY": False}

    # The "Services" list in each store record only ever contains Petrol Station, Post Office and Car Wash.
    # The full set of services is only exposed through the "services" filter of the same API, so the
    # stores offering each service are collected first and then looked up by store id.
    SERVICE_FILTERS = {
        "ATM": Extras.ATM,
        "Cash Back": "cash_withdrawal",
        "Off Licence": "sells:alcohol",
        "Lottery": "sells:lottery",
        "Paypoint": "paypoint",
        "Payzone": "payzone",
        "Wi-Fi": Extras.WIFI,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stores_by_service: dict[str, set[int]] = {service: set() for service in self.SERVICE_FILTERS}
        self.pending_services = len(self.SERVICE_FILTERS)
        self.failed_services: set[str] = set()

    async def start(self) -> AsyncIterator[JsonRequest]:
        for service in self.SERVICE_FILTERS:
            yield self.service_request(service, 1)

    def service_request(self, service: str, page: int) -> JsonRequest:
        return JsonRequest(
            url=f"{API_URL}?pageNumber={page}&services={service}",
            callback=self.parse_service,
            errback=self.service_failed,
            cb_kwargs={"service": service, "page": page},
        )

    def parse_service(self, response: Response, service: str, page: int) -> Any:
        stores = response.json()["storeList"]
        self.stores_by_service[service].update(store["Id"] for store in stores)
        if len(stores) == 10:
            yield self.service_request(service, page + 1)
        else:
            yield from self.service_done()

    def service_failed(self, failure: Failure) -> Any:
        service = failure.request.cb_kwargs["service"]
        self.logger.error(f"Service lookup for {service} failed, not tagging it: {failure.value!r}")
        self.crawler.stats.inc_value("atp/spar_gb/failed_service")
        self.failed_services.add(service)
        yield from self.service_done()

    def service_done(self) -> Any:
        self.pending_services -= 1
        if self.pending_services == 0:
            yield JsonRequest(url=f"{API_URL}?pageNumber=1", meta={"page": 1})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stores = response.json()["storeList"]
        if len(stores) == 10:
            page_no = response.meta["page"] + 1
            yield JsonRequest(url=f"{API_URL}?pageNumber={page_no}", meta={"page": page_no})

        for store in stores:
            item = DictParser.parse(store)
            item["website"] = "https://www.spar.co.uk" + store["StoreUrl"].rstrip("/")
            item["street_address"] = clean_address(
                [store.get("Address1"), store.get("Address2"), store.get("Address3")]
            )

            services = [s["Name"] for s in store["Services"]]

            for service, tag in self.SERVICE_FILTERS.items():
                if service in self.failed_services:
                    continue
                apply_yes_no(tag, item, store["Id"] in self.stores_by_service[service])
            apply_yes_no(Extras.CAR_WASH, item, "Car Wash" in services)
            if "Post Office" in services:
                item["extras"]["post_office"] = "post_partner"

            apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item
