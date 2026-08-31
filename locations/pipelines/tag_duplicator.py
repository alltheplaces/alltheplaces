from locations.items import Feature


class TagDuplicatorPipeline:
    def process_item(self, item: Feature):
        if not item.get_tag("healthcare"):
            if amenity := item.get_tag("amenity"):
                if amenity in {"clinic", "dentist", "hospital", "pharmacy"}:
                    item.set_tag("healthcare", amenity)
                elif amenity == "doctors":
                    item.set_tag("healthcare", "doctor")
        return item
