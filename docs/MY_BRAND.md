## My brand

Every business wants to be found. Nobody is trying to hide.
A common complaint from brand owners towards map and application
suppliers is that their brand data is poorly presented
(in particular positions wrong by many metres) or missing entirely.
The smaller a brand the less likely mapping companies will
take an interest in *getting it right*. This is a
shame as most brands invest a great deal of energy in getting
it right on *their own website*.

What if there was a way to take the effort invested in
your website and in a lightweight manner provide it to others
as you would wish it to be shown on digital maps? Change your data
and watch it filter through into other maps and applications!
There is now a frictionless way to do this. Simply [add a small piece
of software](../README.md#contributing-code) to this project that talks to your website or brand
marketing partner ([we interface to many of these](../locations/storefinders/README.md)). Failing that, publish your store locations as https://schema.org/LocalBusiness data.

### How much effort?

Take a look around [this project](../locations/spiders). What you will see is that the average
brand spider is only 20 odd lines of simple code. No infrastructure is required.
Making the small effort to do this is saying to the wider community that this
is the place to pick up my location data presented in a standard format alongside
other brands.

### Is my open data correct?

The gold standard in _open_ mapping data is
[OpenStreetMap (OSM)](https://www.openstreetmap.org/).
Part of your digital brand presence, although you may not know it, are your
[Wikidata](../docs/WIKIDATA.md#wikidata) and possibly
[name suggestion index](../docs/WIKIDATA.md#name-suggestion-index-nsi) entries.
Publishing your location data as part of the _All The Places_ project gives you
and others more of a chance to spot and correct any mistakes
with your information in these datasets.

### Take ownership

For the most part a single brand has a single spider. A spider is a simple piece
of code but who should maintain it? If not the brand itself, then who?
We use a simple convention to claim _"ownership"_ by [adding a contact email
to the spider code itself](https://github.com/alltheplaces/alltheplaces/blob/master/locations/spiders/tomtom.py#L7).
The `contacts` field serves a dual purpose, both as a beacon
of responsibility and a place for potential queries to be sent.
