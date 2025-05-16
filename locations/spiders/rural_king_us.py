import json

import scrapy

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature


class RuralKingServiceCollectorSpider(scrapy.Spider):
    """
    This spider is a modified version of the Rural King spider that collects service information
    from each store's detail page. It's designed for data research purposes to identify all
    possible service options across Rural King locations.

    The regular spider should continue to use the more efficient approach without visiting each
    store page, while applying service tags based on the findings from this research.
    """

    name = "rural_king_service_collector"
    item_attributes = {
        "brand": "Rural King",
        "brand_wikidata": "Q7380525",
    }
    allowed_domains = ["ruralking.com"]
    download_delay = 1.5  # Be nice to their servers

    # Use predetermined points in states with Rural King locations
    # These are geographic centers of states where Rural King operates
    start_urls = [
        # Indiana (Indianapolis)
        "https://www.ruralking.com/wcs/resources/store/10151/storelocator/latitude/39.7684/longitude/-86.1581?radius=250&radiusUOM=SMI&siteLevelStoreSearch=false",
        # Limited to just a few areas for research purposes to avoid too much load
        # Ohio (Columbus)
        "https://www.ruralking.com/wcs/resources/store/10151/storelocator/latitude/39.9612/longitude/-82.9988?radius=250&radiusUOM=SMI&siteLevelStoreSearch=false",
        # Florida (Tallahassee)
        "https://www.ruralking.com/wcs/resources/store/10151/storelocator/latitude/30.4383/longitude/-84.2807?radius=250&radiusUOM=SMI&siteLevelStoreSearch=false",
    ]

    def parse(self, response):
        try:
            data = json.loads(response.text)
            stores = data.get("PhysicalStore", [])

            if not stores:
                self.logger.info(f"No stores found in API response from {response.url}")
                return

            self.logger.info(f"Found {len(stores)} stores in API response from {response.url}")

            # Limit to 10 stores per region for research purposes
            for store in stores[:10]:
                # Convert the UniqueID to slug format (e.g. "hanover-pa")
                city_slug = store.get("city", "").lower().replace(" ", "-")
                state_code = store.get("stateOrProvinceName", "").lower()
                store_page_url = f"https://www.ruralking.com/{city_slug}-{state_code}"

                yield scrapy.Request(url=store_page_url, callback=self.parse_store_page, meta={"store_data": store})

        except Exception as e:
            self.logger.error(f"Error parsing API response: {e}")

    def parse_store_page(self, response):
        store = response.meta.get("store_data")

        # Extract all services from the store page
        services = []
        service_elements = response.css(".storelocatorServiceOffer-offer__label::text").getall()
        for service in service_elements:
            services.append(service.strip())

        # Log all services we found to analyze later
        self.logger.info(
            f"Store #{store.get('storeName')} in {store.get('city')}, {store.get('stateOrProvinceName')} services: {services}"
        )

        try:
            properties = {
                "ref": store.get("uniqueID"),
                "name": f"Rural King #{store.get('storeName')}",
                "addr_full": " ".join(store.get("addressLine", [])),
                "city": store.get("city"),
                "state": store.get("stateOrProvinceName"),
                "postcode": store.get("postalCode", "").strip(),
                "country": store.get("country"),
                "phone": store.get("telephone1", "").strip(),
                "website": response.url,
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

            # Apply shop category
            apply_category(Categories.SHOP_AGRARIAN, item)

            # Add services
            extras = item.get("extras", {})
            extras["store_services"] = services
            item["extras"] = extras

            return item

        except Exception as e:
            self.logger.error(f"Error parsing store data: {str(e)}")
            return None

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


class RuralKingUSSpider(scrapy.Spider):
    name = "rural_king_us"
    item_attributes = {
        "brand": "Rural King",
        "brand_wikidata": "Q7380525",
    }
    allowed_domains = ["ruralking.com"]
    download_delay = 1.0  # Be nice to their servers

    def start_requests(self):
        # Check if a specific URL was passed for testing
        if hasattr(self, "url") and self.url:
            yield scrapy.Request(self.url, callback=self.parse_api)
        else:
            # Use searchable points to query for stores
            # This approach allows for complete coverage across the US
            # and accommodates future expansion to new regions

            with open("./locations/searchable_points/us_centroids_50mile_radius.csv") as points_file:
                next(points_file)  # Skip the header
                for point in points_file:
                    _, lat, lon = point.strip().split(",")

                    # Use a 100-mile radius to ensure good coverage while reducing API requests
                    search_url = f"https://www.ruralking.com/wcs/resources/store/10151/storelocator/latitude/{lat}/longitude/{lon}?radius=100&radiusUOM=SMI&siteLevelStoreSearch=false"
                    yield scrapy.Request(search_url, callback=self.parse_api)

    def parse_api(self, response):
        try:
            data = json.loads(response.text)
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

                yield scrapy.Request(
                    url=store_page_url,
                    callback=self.parse_store_page,
                    meta={"store_data": store},
                    errback=self.errback_store_page,
                )
        except Exception as e:
            self.logger.error(f"Error parsing API response: {e}")

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
        try:
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
                extras["shop"] = "guns"

            if "In-Store Pickup" in services:
                extras["pickup"] = "yes"

            if "Ship to Store" in services:
                extras["delivery:store"] = "yes"

            # Store the raw services list for reference
            extras["store_services"] = services

            item["extras"] = extras

            return item
        except Exception as e:
            self.logger.error(f"Error creating store item: {str(e)}")
            return None

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
