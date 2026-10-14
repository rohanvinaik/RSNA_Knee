# The six contracts of phase C, as the lead wrote them (2026-10-13, before the Codex check)

Written before the consult was opened. The contracts are the packets of stages 5 to 9
(`src/knee/objects/{dome,tile_dome,selection,laterality,strip}.py`,
`src/knee/relations/{facing,interstice,spans}.py`), each a module docstring, its codes, its pure
decisions with their intent tests, its record and the docstrings of the bodies six parallel
builders are filling. What each says, in plain words, and where the lead is least sure.

1. **The dome at the squint.** An obstacle is a tile the lens cleared or left undecided, or a
   tile dark on both acquisitions (`below_below`), or, with no pair, a tile whose median lies at
   or below the split. The interior is the rest of the kept tiles; the height is the distance to
   the nearest obstacle or the frame; peaks by prominence (one tile, 8 mm); territories by
   watershed. Least sure: whether the undecided ring at the skin should be an obstacle. The
   founder keeps those tiles in play; an object that reaches the skin (the small anterior one)
   would lose its outer tiles to the ring.
2. **The selection.** Facts from the tile centres in the scanner's millimetres: count, centre,
   superior, anterior, left-right, superior extent, anterior face, touches the leg's border,
   ringed. Coronal and sagittal: the two largest territories are the big pair, the more superior
   first; sagittal: a territory smaller than the superior one, with its centre in front of the
   superior one's centre and its height between the inferior one's top and the superior one's
   middle, is the small anterior object; coronal: a small ringed territory below the inferior
   one's top and beside it is the witness, whose side gives the sign; axial: the largest and the
   largest in front of it. Least sure: "in front of the superior one's centre" as the test for
   the anterior object, and the candidate floor of four tiles.
3. **The strip.** The native edge is read only at the midpoints of an object's tile boundary,
   with the existing profile and band machinery, plus the partner's bands and the strip's digits
   against the object's own pixels. The outline (the three pulls) waits for its own contract.
4. **The facing pairs.** Two selected objects face when gap tiles (obstacles) touch both; a
   bar of one gap tile.
5. **The interstice.** The extent is the gap tiles plus the tiles between the two objects'
   faces along the line joining their centres; each wall is the strip's digit sequence from the
   band outward (plate, layer, fill); the fill is the commonest read pair over the extent; the
   contents are the four-connected bodies of `below_below` tiles inside the extent, central or
   peripheral by their offset from the axis, medial or lateral by the sign. Least sure: contents
   at tile scale (8 mm) where a meniscus is a few millimetres thick.
6. **Spans and envelope.** A span is a `below_below` body outside every interstice touching
   both big objects; the envelope is the connected body of the fat-dark series' own `above` tiles
   touching an interstice, with its posterior pouch and neck.

And from the depth trace (`the-funnel-depth-trace-cell-20261013.md`): the tie rule (the middle,
where the cell build takes the earliest or keeps all) and the floor of eight slices are the
lead's and are for him.
