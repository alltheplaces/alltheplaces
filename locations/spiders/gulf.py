import hashlib

import scrapy
from scrapy import FormRequest

from locations.items import GeojsonPointItem
from locations.spiders.costacoffee_gb import yes_or_no


class GulfSpider(scrapy.Spider):
    name = "gulf"
    item_attributes = {"brand": "Gulf Oil", "brand_wikidata": "Q5617505"}
    allowed_domains = ["gulfoil.com"]

    def start_requests(self):
        yield FormRequest(
            url="https://gulfoil.com/views/ajax?_wrapper_format=drupal_ajax",
            formdata={
                "field_geofield_proximity[value]": "90000",
                "units_of_measurements": "3959",
                "field_geofield_proximity[source_configuration][origin_address]": "lebanon,+ks",
                "view_name": "station_locator_search_block",
                "view_display_id": "block_2",
                "view_args": "",
                "view_path": "/node/21",
                "view_base_path": "",
                "view_dom_id": "9c7a59cb2eec96bcd2fd6049f3874991fabc562c27d69baf2cbb306cab83ae75",
                "pager_element": "0",
                "_drupal_ajax": "1",
                "ajax_page_state[theme]": "gulf_oil",
                "ajax_page_state[theme_token]": "",
                "ajax_page_state[libraries]": "classy/base,classy/messages,classy/node,copyprevention/copyprevention,core/normalize,google_analytics/google_analytics,gulf_oil/global-scripts,gulf_oil/global-styling,gulf_oil/station-locator,layout_bg/layout_bg_onecol,layout_discovery/onecol,system/base,views/views.ajax,views/views.module",
            },
            headers={"Accept": "application/json"},
        )

    def parse(self, response):
        page = response.meta.get("page", 0)
        json_result = response.json()
        html_result = json_result[-1]["data"]
        results = scrapy.Selector(text=html_result)

        for tbody in results.xpath("//tbody"):
            name = tbody.xpath("tr[1]/th[1]//text()").get()
            contact = (
                results.xpath("//tbody")[0].xpath("tr[2]/td[1]/p/text()").extract()
            )
            address = ", ".join([r.strip() for r in contact[:2]])
            phone = contact[2].replace("Phone Number: ", "")
            html_content = tbody.get()

            yield GeojsonPointItem(
                ref=hashlib.sha256((name + address).encode("utf_8")).hexdigest(),
                name=name,
                addr_full=address,
                phone=phone,
                extras={
                    "amenity": "fuel",
                    "fuel:diesel": yes_or_no("Diesel" in html_content),
                    "toilets": yes_or_no("Restrooms" in html_content),
                    "atm": yes_or_no("ATM" in html_content),
                    "shop": "convenience"
                    if "Convenience Store" in html_content
                    else "no",
                },
            )

        if results.xpath("//li[@class='pager__item pager__item--next']/a"):
            page += 1
            yield FormRequest(
                url="https://gulfoil.com/views/ajax?_wrapper_format=drupal_ajax",
                formdata={
                    "page": str(page),
                    "field_geofield_proximity[value]": "90000",
                    "units_of_measurements": "3959",
                    "field_geofield_proximity[source_configuration][origin_address]": "lebanon,+ks",
                    "view_name": "station_locator_search_block",
                    "view_display_id": "block_2",
                    "view_args": "",
                    "view_path": "/node/21",
                    "view_base_path": "",
                    "view_dom_id": "9c7a59cb2eec96bcd2fd6049f3874991fabc562c27d69baf2cbb306cab83ae75",
                    "pager_element": "0",
                    "_drupal_ajax": "1",
                    "ajax_page_state[theme]": "gulf_oil",
                    "ajax_page_state[theme_token]": "",
                    "ajax_page_state[libraries]": "classy/base,classy/messages,classy/node,copyprevention/copyprevention,core/normalize,google_analytics/google_analytics,gulf_oil/global-scripts,gulf_oil/global-styling,gulf_oil/station-locator,layout_bg/layout_bg_onecol,layout_discovery/onecol,system/base,views/views.ajax,views/views.module",
                },
                meta={"page": page},
                headers={"Accept": "application/json"},
            )
