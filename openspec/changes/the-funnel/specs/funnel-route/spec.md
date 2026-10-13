## ADDED Requirements

### Requirement: Every operation after the first lens computes only inside what the earlier operations left
The system SHALL compute each operation after the first lens only over the tiles, slices and
objects that the operations before it left: no operation SHALL read a tile the first lens declared
background, no operation below the depth collapse SHALL read a slice in full that no lens chose,
and no native-resolution operation SHALL read outside an object's strip or, when a predicate asks,
outside that object's extent. The record of what was excluded SHALL be kept with its reason.

#### Scenario: A tile is declared background
- **WHEN** the first lens declares a tile background on a series
- **THEN** no later operation on that series reads the tile, the ledger records no read of it,
  and the tile's median and the decision's reason stay in the saved record

#### Scenario: A tile is undecided
- **WHEN** the first lens cannot declare a tile background or leg
- **THEN** the tile is named undecided and handed on with the leg tiles, and the exclusion that
  background carries is not applied to it

### Requirement: Only the two acquisitions of one orientation are laid over each other
The system SHALL line up a fat-bright and a fat-dark series of the same plane by the position of
their tile centres in the scanner's millimetres, and SHALL NOT lay a series of one plane over a
series of another plane or carry an object from one plane to another by position. Each plane
SHALL resolve its own objects by its own selection rule.

#### Scenario: A pair exists for a plane
- **WHEN** a plane has one fat-bright and one fat-dark series
- **THEN** every leg tile of the fat-dark series records the fat-bright tile nearest in
  millimetres with the distance and a match code, and the conjunction of their digits is read

#### Scenario: A plane has one series
- **WHEN** a plane has a single series
- **THEN** its tiles record no partner, its conjunction is unmatched everywhere, and its objects are
  selected by that plane's own rule

### Requirement: Depth collapses to the slices the lenses choose
The system SHALL compute cheap readings over every slice of a series from the squint alone, SHALL
let each reading stand at the one slice where it peaks, and SHALL read in full only the chosen
slices. A reading with too few valid slices or no peak SHALL abstain with a named code.

#### Scenario: Four readings choose two slices
- **WHEN** the four readings peak at two distinct slices
- **THEN** both slices are read in full, each lens's choice is recorded, and no other slice is
  read by any operation below the collapse

#### Scenario: Readings tie
- **WHEN** a reading has an exact tie across a run of slices
- **THEN** the middle slice of the run is chosen and the code says it was a tie

### Requirement: Objects are selected by structural facts and carry no anatomy
The system SHALL select objects from the tile dome's territories by facts it computed (tile
count, position along the header's axes, enclosure by a dark ring, rank), SHALL name them by
structural role codes, and SHALL NOT write an anatomical word into any record, code name or
picture. The laterality sign SHALL come from the small ringed territory's side, or abstain.

#### Scenario: Two big territories on a coronal slice
- **WHEN** a coronal chosen slice holds two territories larger than the rest
- **THEN** the superior one by the header's axis is the superior big object and the inferior one
  the inferior big object, with their facts recorded

#### Scenario: No laterality witness
- **WHEN** no small ringed territory inferior to the inferior big object is found
- **THEN** the side is abstained with a named code and every side-dependent record abstains with it

### Requirement: The expensive work runs along the edge, in a strip
The system SHALL cast native-resolution profiles only at the midpoints of an object's tile
boundary, within a strip of declared width, and SHALL draw the object's boundary from the dark
bands those profiles bracket, pulled taut under the thesis's three pulls with a leeway from the
flicker. Where a pair exists the partner's bands SHALL be transported to the same points and kept
beside the object's own, never merged.

#### Scenario: A profile leaves the plane
- **WHEN** a profile's samples fall outside the plane
- **THEN** the point is coded frame-clipped and no boundary is drawn from it

### Requirement: Relations and later rounds are located by what is already resolved
The system SHALL construct an interstice only between two selected objects that face across gap
tiles, SHALL read its walls, fill and contents inside its extent, SHALL make each content a
round-2 object located by its interstice, and SHALL find spans and the envelope only among the
leg tiles that the earlier rounds left. The residual SHALL be every tile no round claimed.

#### Scenario: A wall cannot be read
- **WHEN** a facing pair's profile on one side brackets no dark band
- **THEN** the wall is coded unreadable and the gap is not recorded as a number

### Requirement: Nothing is removed from the tree
The system SHALL keep every whole-field lens that exists callable and drawable from a saved run,
off the default route, behind an explicit request flag.

#### Scenario: The whole-field forms are requested
- **WHEN** a run is requested with the whole-field flag
- **THEN** the whole-field readings are computed and drawn beside the funnel's, and the receipt
  names both
