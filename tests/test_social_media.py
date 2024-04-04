from locations.exporters.geojson import item_to_properties
from locations.items import Feature, SocialMedia, get_social_media, set_social_media


def test_assigning():
    item = Feature()

    for social_media in SocialMedia:
        set_social_media(item, social_media, social_media.value)

    for social_media in SocialMedia:
        assert get_social_media(item, social_media) == social_media.value

    props = item_to_properties(item)
    for social_media in SocialMedia:
        assert props.get("contact:{}".format(social_media.value)) == social_media.value


def test_field():
    # Check set_social_media and get_social_media works on ATP fields
    item = Feature()

    set_social_media(item, SocialMedia.FACEBOOK, "aaa")
    assert item["facebook"] == "aaa"

    item["facebook"] = "bbb"
    assert get_social_media(item, SocialMedia.FACEBOOK) == "bbb"


def test_not_field():
    # Check set_social_media and get_social_media work on extras
    item = Feature()

    set_social_media(item, "this-will-never-be-a-real-atp-field", "aaa")
    assert item["extras"]["contact:this-will-never-be-a-real-atp-field"] == "aaa"

    item["extras"]["contact:this-will-never-be-a-real-atp-field"] = "bbb"
    assert get_social_media(item, "this-will-never-be-a-real-atp-field") == "bbb"


def test_overriding():
    # While OSM may support multiple ; separated values, we don't.
    # Check that the value is overridden correctly
    item = Feature()

    set_social_media(item, SocialMedia.FACEBOOK, "aaa")
    assert item["facebook"] == "aaa"

    set_social_media(item, SocialMedia.FACEBOOK, "bbb")
    assert get_social_media(item, SocialMedia.FACEBOOK) == "bbb"
