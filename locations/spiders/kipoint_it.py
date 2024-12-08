import json
from urllib.parse import parse_qs, unquote, urlsplit

import chompjs
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_IT, DAYS_IT, DELIMITERS_IT, NAMED_DAY_RANGES_IT, NAMED_TIMES_IT, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


def get_query_param(link, query_param):
    parsed_link = urlsplit(unquote(link))
    queries = parse_qs(parsed_link.query)
    return queries.get(query_param, [])


def clean_strings(iterator):
    return list(filter(bool, map(str.lower, map(str.strip, iterator))))


class KipointITSpider(JSONBlobSpider):
    name = "kipoint_it"
    item_attributes = {
        "brand": "Kipoint",
        "brand_wikidata": "Q115309531",
    }
    start_urls = ["https://www.kipoint.it/punti-vendita"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.fetch_mymaps)

    def fetch_mymaps(self, response):
        if map_id := get_query_param(response.css("#container-map iframe::attr(src)").get(), "mid"):
            yield response.follow(f"https://www.google.com/maps/d/viewer?femb=1&mid={map_id[0]}", callback=self.parse)

    def extract_json(self, response):
        _pageData = response.xpath('//script[contains(text(), "var _pageData = ")]/text()').get()
        _pageData = _pageData.split("var _pageData = ")[-1].strip().strip(";")
        pdata = chompjs.parse_js_object(json.loads(_pageData))[1][6][0][12][0][13][0]
        places = []
        for s in pdata:
            place = {"ref": s[5][0][1][0], "coords": {"lat": s[1][0][0][0], "lon": s[1][0][0][1]}}
            for meta in s[5][3]:
                place[meta[0].lower()] = ";".join(meta[1])
            places.append(place)
        return places

    def post_process_item(self, item, response, location):
        apply_category(Categories.POST_DEPOT, item)
        yield Request(
            f'https://www.kipoint.it/it/pv/{item["ref"]}',
            cb_kwargs={"item": item},
            callback=self.parse_storepage,
            errback=self.storepage_advertised,
        )

    def storepage_advertised(self, failure):
        item = failure.request.cb_kwargs["item"]
        if item.get("website"):
            yield Request(
                item["website"], cb_kwargs={"item": item}, callback=self.parse_storepage, errback=self.keep_less_data
            )
        else:
            yield item

    def keep_less_data(self, failure):
        yield failure.request.cb_kwargs["item"]

    def parse_storepage(self, response, item):
        if orari := clean_strings(response.css(".orario .content *::text").getall()):
            oh = OpeningHours()
            orari = "; ".join(orari)
            oh.add_ranges_from_string(
                orari,
                days=DAYS_IT,
                named_day_ranges=NAMED_DAY_RANGES_IT,
                named_times=NAMED_TIMES_IT,
                closed=CLOSED_IT,
                delimiters=DELIMITERS_IT,
            )
            item["opening_hours"] = oh
        if piva := clean_strings(response.css(".piva .content *::text").getall()):
            item["extras"]["ref:vatin"] = f"IT{piva[0]}"
        if phone := clean_strings(response.css(".telefono .content *::text").getall()):
            item["phone"] = phone[0]
        if fax := clean_strings(response.css(".fax .content *::text").getall()):
            item["extras"]["contact:fax"] = fax[0]
        if addr_full := response.css(".dove-siamo .card *::text").get():
            item["addr_full"] = addr_full.strip()
        return item
