import scrapy


from scrapy import Spider

from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import DAYS_BY_FREQUENCY, OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from scrapy.http import HtmlResponse

# Similar to many other wordpress based spiders, supply an allowed domain or start_urls
# Explicity specify days


class MapsMarkerProSpider(Spider):
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
    days = None

    def start_requests(self):
        payload = "action=mmp_map_markers&type=map"
        if len(self.start_urls) == 0 and hasattr(self, "allowed_domains"):
            for domain in self.allowed_domains:
                url = "https://{domain}/wp-admin/admin-ajax.php"
                yield scrapy.Request(url=url, headers=self.headers, method="POST", body=payload, callback=self.parse)
        elif len(self.start_urls) != 0:
            for url in self.start_urls:
                yield scrapy.Request(url=url, headers=self.headers, method="POST", body=payload, callback=self.parse)

    def parse(self, response, **kwargs):
        # Response is a GeoJSON object
        ids = []
        for location in response.json()["data"]["features"]:
            ids.append(location["properties"]["id"])

        payload = "action=mmp_marker_popups&id=" + ",".join(ids) + "&lang="
        yield scrapy.Request(
            url=response.url,
            headers=self.headers,
            method="POST",
            body=payload,
            callback=self.parse_popups,
            cb_kwargs=dict(features=response.json()["data"]["features"]),
        )

    def parse_popups(self, response, features, **kwargs):
        for location in features:
            item = DictParser.parse(location["properties"])
            item["lat"], item["lon"] = location["geometry"]["coordinates"]

            for popup in response.json()["data"]:
                if popup["id"] == location["properties"]["id"]:
                    html_fragment = HtmlResponse(url="#", body=popup["popup"], encoding="utf-8")
                    item = self.parse_popup_html(item, location, html_fragment)

            yield from self.parse_item(item, location)

    def parse_popup_html(self, item: Feature, location: dict, html_fragment: HtmlResponse):
        item["opening_hours"] = OpeningHours()
        for hours in html_fragment.xpath("//div[contains(@class, 'real-opening-hours')]/ul/li/text()").getall():
            item["opening_hours"].add_ranges_from_string(hours, days=self.days)

        item["website"] = html_fragment.xpath("//a/@href").get()
        return item

    def parse_item(self, item: Feature, location: dict, **kwargs):
        yield item
