import re
from typing import Any, AsyncIterator, Iterable
from urllib.parse import urljoin, urlparse

from scrapy import Spider
from scrapy.http import JsonRequest, Request, TextResponse

from locations.hours import DAYS, DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# e.g. "POINT (-73.9754571 40.6312851)", longitude first.
WKT_POINT_REGEX = re.compile(r"POINT\s*\(\s*(-?[\d.]+)\s+(-?[\d.]+)\s*\)")


def parse_address_field(address: dict | list | None, item: Feature) -> None:
    """
    Set the address of `item` from a field of the Drupal Address module, which
    many Drupal sites use for postal addresses whatever the API or page they
    expose it through.
    https://www.drupal.org/project/address
    """
    if isinstance(address, list):
        address = address[0] if address else None
    if not address:
        return
    item["street_address"] = merge_address_lines(
        [address.get("address_line1"), address.get("address_line2"), address.get("address_line3")]
    )
    item["city"] = address.get("locality")
    item["state"] = address.get("administrative_area")
    item["postcode"] = address.get("postal_code")
    item["country"] = address.get("country_code")


def parse_geofield(geofield: dict | list | None, item: Feature) -> None:
    """
    Set the coordinates of `item` from a field of the Drupal Geofield module,
    which carries "lat" and "lon" alongside the geometry as WKT.
    https://www.drupal.org/project/geofield
    """
    if isinstance(geofield, list):
        geofield = geofield[0] if geofield else None
    if not geofield:
        return
    if geofield.get("lat") is not None and geofield.get("lon") is not None:
        item["lat"], item["lon"] = geofield["lat"], geofield["lon"]
    elif m := WKT_POINT_REGEX.fullmatch((geofield.get("value") or "").strip()):
        item["lon"], item["lat"] = m.group(1), m.group(2)


def parse_office_hours(slots: list | None) -> OpeningHours | None:
    """
    Parse a field of the Drupal Office Hours module: a list of slots with
    "day" counted from 0 for Sunday, and times as integers such as 930 for
    09:30. Only open days have slots, so any other day is closed.
    https://www.drupal.org/project/office_hours
    """
    if not slots:
        return None
    oh = OpeningHours()
    open_days = set()
    for slot in slots:
        if slot.get("day") is None:
            continue
        day = DAYS_FROM_SUNDAY[int(slot["day"])]
        open_days.add(day)
        if slot.get("all_day"):
            oh.add_range(day, "00:00", "24:00")
        elif slot.get("starthours") is not None and slot.get("endhours") is not None:
            oh.add_range(
                day,
                "{:02}:{:02}".format(*divmod(int(slot["starthours"]), 100)),
                "{:02}:{:02}".format(*divmod(int(slot["endhours"]), 100)),
            )
    if not oh:
        return None
    oh.set_closed([day for day in DAYS if day not in open_days])
    return oh


class DrupalJsonApiSpider(Spider):
    """
    Drupal 8 and later can expose a site's content through the core JSON:API
    module, which serves each content type or taxonomy vocabulary at
    /jsonapi/<entity type>/<bundle> and lists them all at /jsonapi. The
    module is off by default, so check that /jsonapi responds before using
    this.
    https://www.drupal.org/docs/core-modules-and-themes/core-modules/jsonapi-module

    To use, specify:
      - `drupal_host`: the site, e.g. "https://www.bklynlibrary.org"
      - `jsonapi_resource`: the resource listing locations, e.g.
        "node/branch" or "taxonomy_term/library_location"

    Optionally, name the fields holding standard module data:
      - `address_field`: a Drupal Address module field, e.g. "field_address"
      - `geofield_field`: a Drupal Geofield field, e.g. "field_position"

    Each site chooses its own fields, so the entry's name, `ref` and page
    are set here and everything else is read from `entry["attributes"]` in
    `post_process_item`. `parse_address_field`, `parse_geofield` and
    `parse_office_hours` also help with these modules' fields elsewhere.

    Where locations need data from another resource, such as opening hours
    kept as separate content that refers back to each location, override
    `start()` to request it with `make_request()`, follow `next_page()` to
    collect every page, and then yield from `super().start()`.
    """

    dataset_attributes: dict = {"source": "api", "api": "drupal-jsonapi"}
    drupal_host: str
    jsonapi_resource: str
    address_field: str | None = None
    geofield_field: str | None = None
    page_size: int = 50  # The most the JSON:API module returns per page.

    def make_request(self, resource: str, **kwargs) -> JsonRequest:
        return JsonRequest(
            url="{}/jsonapi/{}?page%5Blimit%5D={}".format(self.drupal_host, resource, self.page_size), **kwargs
        )

    def next_page(self, response: TextResponse) -> str | None:
        if not (href := ((response.json().get("links") or {}).get("next") or {}).get("href")):
            return None
        # A site behind a proxy can build its links on the internal scheme or
        # host, e.g. "http://" for an "https://" site, costing a redirect.
        host = urlparse(self.drupal_host)
        return urlparse(href)._replace(scheme=host.scheme, netloc=host.netloc).geturl()

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(self.jsonapi_resource)

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature | Request]:
        for entry in response.json().get("data") or []:
            self.pre_process_data(entry)
            item = self.parse_entry(entry)
            yield from self.post_process_item(item, response, entry) or []

        if next_page := self.next_page(response):
            yield JsonRequest(url=next_page, callback=self.parse, cb_kwargs=kwargs)

    def parse_entry(self, entry: dict) -> Feature:
        attributes = entry.get("attributes") or {}
        item = Feature()
        item["ref"] = str(
            attributes.get("drupal_internal__nid") or attributes.get("drupal_internal__tid") or entry.get("id")
        )
        # Content has a "title" and taxonomy terms a "name".
        item["name"] = attributes.get("title") or attributes.get("name")
        if alias := (attributes.get("path") or {}).get("alias"):
            item["website"] = urljoin(self.drupal_host, alias)
        if self.address_field:
            parse_address_field(attributes.get(self.address_field), item)
        if self.geofield_field:
            parse_geofield(attributes.get(self.geofield_field), item)
        return item

    def pre_process_data(self, entry: dict, **kwargs) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: TextResponse, entry: dict, **kwargs) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
