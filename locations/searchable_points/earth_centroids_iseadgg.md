# earth\_centroids\_iseadgg\_[0-9]+km\_radius.(meta|csv)

## Summary

In plain English, the .csv files contain a minimal list of centroids
that allow the Earth's surface area to be completely searched within
a minimal number of radius searches, for various radiuses. It is not
possible to conduct this search comprehensively without also
overlapping the radius searches slightly, resulting in the
possibility of the same location being returned in two radius
searches. These centroid lists minimise overlap and minimise the
number of duplicate locations returned.

[DGGRID software](https://github.com/sahrk/DGGRID) was used to
generate the .csv files from each corresponding .meta file. The
.meta files are tuned for various radius search sizes, aiming to
ensure that a minimal number of searches are required.

## Avoiding errors

There is a lot of complex geodesy and mathematics behind a radius
search of the Earth's surface, and APIs are generally not
documented to explain the exact approach they use for radius
searches. APIs are also often implemented without much knowledge or
care for geodesy and mathematics, and it's often easier to implement
inefficient or inexact location search APIs. The APIs may not have
been tested with remote sparsely populated locations on Earth where
implementation errors are most likely to occur.

For these reasons, it is strongly advised that you don't pick a
300km radius centroid list for an API that also claims to use a
300km search radius, without first checking whether a (for example)
250km radius centroid list would return more locations. Or, if
there is another official figure for number of locations expected
to be returned by a full search of the Earth, this number is
compared for accuracy. Precisions used for calculations, rounding
errors, geodetic datum differences and other similar matters could
introduce minor errors that could result in some small parts of the
Earth's surface not being searched by the API because the chosen
radius of centroid list leaves too little room for error (too little
overlap between each radius search).

Also inspect locations along the
[prime meridian](https://en.wikipedia.org/wiki/Prime_meridian),
along the
[180th meridian](https://en.wikipedia.org/wiki/180th_meridian) and
[closest to poles](https://en.wikipedia.org/wiki/List_of_northernmost_settlements)
to ensure that the API is not clipping radius searches around these
locations where implementation areas are more likely to occur.

## How to generate new .csv files for different radiuses

1. Complete the [build instructions for DGGRID](https://github.com/sahrk/DGGRID/blob/master/INSTALL.md).
2. Find in the DGGRID manual (PDF document within the
   [DGGRID repository](https://github.com/sahrk/DGGRID)) Appendix D
   _Statistics for Some Preset ISEA DGGs_ a maximum internode
   spacing that is closest but slightly smaller than double the
   desired search radius. You want to leave some room for error
   (some additional overlap of radius searches) to accommodate the
   type of API errors mentioned in the _Avoiding errors_ section
   above. For example, if you intend the search radius to be 500km,
   try and find a maximum intenode spacing that is about 475km.
3. Copy an existing .meta file and change parameters such as
   _dggs\_type_, _dggs\_num\_aperture\_4\_res_ and _dggs\_res\_spec_
   to correspond with the selected row from Appendix D where you
   found a suitable maximum internode spacing. Change the output
   filename.
4. Execute `dggrid {earth_centroids_iseadgg_123km_radius.meta}`.
   This will output a new file
   _earth\_centroids\_iseadgg\_123km\_radius.txt_ that contains a
   list of searchable points.
5. Edit _earth\_centroids\_iseadgg\_123km\_radius.txt_ to insert a
   new header row of `id,longitude,latitude` and to remove the last
   line of the file that contains the word `END`. Change the file
   extensions to _.csv_.
6. (optional check but good practice to apply) Open the final
   searchable points _earth\_centroids\_iseadgg\_123km\_radius.csv_
   in [QGIS](https://qgis.org/en/site/) as a delimited text vector
   layer, using an EPSG:4326 (WGS84) geodetic datum. Use the vector
   analysis tool _Distance matrix_ in _Linear (N*k×3)_ mode with
   k=6 to create a table of distances between each searchable point
   and the 6 nearest points. Sort the table by distance and you
   should see values ranging from approximately the minimum
   internode spacing from Appendix D of the DGGRID manual through
   to the maximum internode spacing, followed by a large gap, and
   then distances much higher than the maximum internode spacing.
   These larger distances after the big gap can be ignored because
   icosahedral discrete global grids contain mostly hexagonal cells,
   but also necessarily contain some pentagonal cells (where each
   cell only has 5 nearest neighbours not 6). The largest distance
   in the table before reaching the gap and ignored distance values
   should be less (by an amount that is some reasonable error margin
   (refer to the _Avoiding errors_ section of this document) than
   double the desired search radius.

The DGGRID manual Appendix D does not contain tables of internode
spacings for all parameters of icosahedral discrete global grid that
the software can generate. You can generate a number of outputs from
DGGRID where maximum internode spacings are not documented in the
manual, and use QGIS with the process summarised above to check
each candidate output to find one which has a suitable maximum
internode spacing.
