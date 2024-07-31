import re

import scrapy

from locations.items import Feature
from locations.searchable_points import open_searchable_points

BRAND_MAPPING = {
    "KFC": "KFC",
    "KB": "KFC-Taco Bell",
    "KL": "KFC-Long John Silvers",
    "KA": "KFC-A&W",
}


class KbpFoodsSpider(scrapy.Spider):
    name = "kbp_foods"
    allowed_domains = ["kbp-foods.com"]
    item_attributes = {"brand": "KBP Foods"}
    download_delay = 0.3
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        # Fetch brand data first
        brand_url = "https://kbp-foods.com/wp-admin/admin-ajax.php"

        payload = "action=get_all_locations&brand="

        headers = {
            "authority": "kbp-foods.com",
            "pragma": "no-cache",
            "cache-control": "no-cache",
            "sec-ch-ua": '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
            "accept": "application/json, text/javascript, */*; q=0.01",
            "x-requested-with": "XMLHttpRequest",
            "sec-ch-ua-mobile": "?0",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://kbp-foods.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://kbp-foods.com/company-history/",
            "accept-language": "en-US,en;q=0.9",
        }

        yield scrapy.http.Request(brand_url, self.parse, method="POST", headers=headers, body=payload)

    def parse(self, response):
        brand_data = response.json()

        url = "https://kbp-foods.com/wp-json/facetwp/v1/refresh"

        with open_searchable_points("us_centroids_100mile_radius.csv") as points:
            next(points)  # Ignore the header
            for point in points:
                row = point.split(",")
                lat = row[1].strip()
                lon = row[2].strip()

                # Skip points West of Texas or outside the contiguous US
                if float(lon) < -104.0 or float(lon) > -66.0:
                    continue

                if float(lat) > 48.0 or float(lat) < 25.0:
                    continue

                payload = f"action=facetwp_refresh&data%5Bfacets%5D=%7B%22proximity%22%3A%5B%22{lat}%22%2C%22{lon}%22%2C%22250%22%2C%22placeholder%22%5D%2C%22map%22%3A%5B%5D%7D&data%5Bfrozen_facets%5D%5Bproximity%5D=hard&data%5Bfrozen_facets%5D%5Bmap%5D=hard&data%5Bhttp_params%5D%5Bget%5D%5Bfwp_proximity%5D={lat}%252C{lon}%252C250%252Cplaceholder&data%5Bhttp_params%5D%5Buri%5D=locations&data%5Bhttp_params%5D%5Burl_vars%5D%5Bproximity%5D%5B%5D={lat}&data%5Bhttp_params%5D%5Burl_vars%5D%5Bproximity%5D%5B%5D={lon}&data%5Bhttp_params%5D%5Burl_vars%5D%5Bproximity%5D%5B%5D=250&data%5Bhttp_params%5D%5Burl_vars%5D%5Bproximity%5D%5B%5D=placeholder&data%5Btemplate%5D=locations&data%5Bextras%5D%5Bsort%5D=default&data%5Bsoft_refresh%5D=0&data%5Bis_bfcache%5D=1&data%5Bfirst_load%5D=0&data%5Bpaged%5D=1"

                headers = {
                    "authority": "kbp-foods.com",
                    "sec-ch-ua": '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
                    "accept": "text/plain, */*; q=0.01",
                    "x-requested-with": "XMLHttpRequest",
                    "sec-ch-ua-mobile": "?0",
                    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36",
                    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "origin": "https://kbp-foods.com",
                    "sec-fetch-site": "same-origin",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-dest": "empty",
                    "referer": f"https://kbp-foods.com/locations/?fwp_proximity={lat}%2C{lon}%2C250%2Cplaceholder",
                    "accept-language": "en-US,en;q=0.9",
                }

                yield scrapy.http.Request(
                    url,
                    callback=self.parse_location,
                    method="POST",
                    body=payload,
                    headers=headers,
                    meta=brand_data,
                )

    def parse_location(self, response):
        result = response.json()
        meta_brand = response.meta["locations"]

        locations = result["settings"].get("map", {}).get("locations", [])

        if len(locations) > 1:  # Gather the location data - always returns "Your location" as first result
            for location in locations[1:]:  # Skip "Your location"
                content = location["content"]
                ref, addr_full = re.search(
                    r"\<h2\>(.*)\<\/h2>.*\<div class\=\"fwpl-item\"\>(.*?)\<\/div\>",
                    content,
                    flags=re.DOTALL,
                ).groups()

                store_brand = [x for x in meta_brand if x["title"] == ref][0]  # Match the store id to the brand data

                properties = {
                    "ref": ref,
                    "addr_full": addr_full,
                    "lat": location["position"]["lat"],
                    "lon": location["position"]["lng"],
                    "extras": {"store_brands": BRAND_MAPPING[store_brand["brand"]]},
                }

                yield Feature(**properties)
        else:  # If no locations in this area
            pass
