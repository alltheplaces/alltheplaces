from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class TrungNguyenCoffeeVNSpider(SuperStoreFinderSpider):
    name = "trung_nguyen_coffee_vn"
    item_attributes = {
        "brand_wikidata": "Q3541154",
        "brand": "Trung Nguyên",
    }
    allowed_domains = [
        "trungnguyenlegend.com",
    ]
