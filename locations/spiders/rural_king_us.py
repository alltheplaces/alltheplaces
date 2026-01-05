from json import loads
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature


class RuralKingUSSpider(Spider):
    """
    Rural King spider that visits each store page to collect service information
    and other details. This spider identifies services like RKGuns, propane,
    pickup, and ship-to-store that vary by location.

    This spider uses a single API request to efficiently retrieve all store data
    rather than making multiple geographic queries.
    """

    name = "rural_king_us"
    item_attributes = {"brand": "Rural King", "brand_wikidata": "Q7380525"}
    allowed_domains = ["ruralking.com"]

    async def start(self) -> AsyncIterator[Request]:
        # Check if a specific URL was passed for testing
        if hasattr(self, "url") and self.url:
            yield Request(self.url, callback=self.parse_api)
        else:
            # Use a single API request to get all stores at once
            # This uses origin point (0,0) with a large radius to cover the entire US
            # and maxItems=1000 to ensure all stores are returned
            all_stores_url = "https://www.ruralking.com/wcs/resources/store/10151/storelocator/latitude/0/longitude/0?maxItems=1000&radius=2500&siteLevelStoreSearch=false"
            yield Request(all_stores_url, callback=self.parse_api)

    def parse_api(self, response):
        data = loads(response.text)
        stores = data.get("PhysicalStore", [])

        if not stores:
            self.logger.info(f"No stores found in API response from {response.url}")
            return

        self.logger.info(f"Found {len(stores)} stores in API response from {response.url}")

        for store in stores:
            # Create the store page URL from the city and state
            city_slug = store.get("city", "").lower().replace(" ", "-")
            state_code = store.get("stateOrProvinceName", "").lower()
            store_page_url = f"https://www.ruralking.com/{city_slug}-{state_code}"

            yield Request(
                url=store_page_url,
                callback=self.parse_store_page,
                meta={"store_data": store},
                errback=self.errback_store_page,
            )

    def errback_store_page(self, failure):
        """Handle errors when fetching store pages"""
        store = failure.request.meta.get("store_data")
        if store:
            # If we can't access the store page, still return the basic store data
            self.logger.warning(
                f"Failed to fetch store page for {store.get('city')}, {store.get('stateOrProvinceName')}. Using basic data."
            )
            return self.create_store_item(store, services=[])

    def parse_store_page(self, response):
        """Parse individual store page to extract services"""
        store = response.meta.get("store_data")

        # Extract services from the page
        services = []
        service_elements = response.css(".storelocatorServiceOffer-offer__label::text").getall()
        for service in service_elements:
            services.append(service.strip())

        self.logger.info(
            f"Store #{store.get('storeName')} in {store.get('city')}, {store.get('stateOrProvinceName')} services: {services}"
        )

        # Create and return the store item with services - pass the actual page URL
        return self.create_store_item(store, services, response.url)

    def create_store_item(self, store, services, website_url=None):
        """Create a Feature item for a store with the specified services and website URL"""
        # If we have the actual store page URL, use it; otherwise fall back to constructed URL
        website = (
            website_url if website_url else f"https://www.ruralking.com/storelocator/store/{store.get('uniqueID')}"
        )

        properties = {
            "ref": store.get("uniqueID"),
            "name": "Rural King",
            "addr_full": " ".join(store.get("addressLine", [])),
            "city": store.get("city"),
            "state": store.get("stateOrProvinceName"),
            "postcode": store.get("postalCode", "").strip(),
            "country": store.get("country"),
            "phone": store.get("telephone1", "").strip(),
            "website": website,
            "lat": float(store.get("latitude")),
            "lon": float(store.get("longitude")),
        }

        # Extract email if available
        for attribute in store.get("Attribute", []):
            if attribute.get("name") == "Email":
                properties["email"] = attribute.get("value")
                break

        # Get store image if available
        for description in store.get("Description", []):
            if "thumbnail" in description:
                properties["image"] = description.get("thumbnail")
                break

        # Add hours
        hours = self.parse_hours(store)
        if hours:
            properties["opening_hours"] = hours

        # Create the feature
        item = Feature(**properties)

        # Apply shop category - Rural King is an agrarian/farm supply store
        apply_category(Categories.SHOP_AGRARIAN, item)

        # Add store services based on what we found on the store page
        extras = item.get("extras", {})

        # Apply services only if they actually exist for this store
        if "Bulk Propane Tanks Filled & Sold Here" in services:
            apply_yes_no(Fuel.PROPANE, item, True)

        if "RKGuns" in services:
            extras["shop"] = "weapons"

        if "In-Store Pickup" in services:
            extras["pickup"] = "yes"

        if "Ship to Store" in services:
            extras["delivery:store"] = "yes"

        # Store the raw services list for reference
        extras["store_services"] = services

        item["extras"] = extras

        return item

    def parse_hours(self, store):
        oh = OpeningHours()

        days = {"Mon": "Mo", "Tue": "Tu", "Wed": "We", "Thu": "Th", "Fri": "Fr", "Sat": "Sa", "Sun": "Su"}

        for attribute in store.get("Attribute", []):
            day_name = attribute.get("displayName")
            if day_name in days and attribute.get("name", "").startswith("Hours_"):
                hours_value = attribute.get("value")
                if hours_value and hours_value.strip():
                    try:
                        open_time, close_time = hours_value.split(" - ")
                        oh.add_range(
                            day=days[day_name], open_time=open_time, close_time=close_time, time_format="%I:%M%p"
                        )
                    except Exception as e:
                        self.logger.warning(f"Error parsing hours {hours_value} for {day_name}: {e}")

        return oh.as_opening_hours()
