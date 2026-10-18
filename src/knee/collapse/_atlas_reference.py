"""Compact numerical derivative of selected SPL atlas reference planes.

Generated from the retained reference-selection-facts.json; modified reference
selection by this project, not the original atlas and not study-derived values.
All or portions of this licensed product (such portions are the "Software") have
been obtained under license from The Brigham and Women's Hospital, Inc. and are
subject to the terms and conditions in THIRD_PARTY_LICENSES/SPL_KNEE_ATLAS.txt.
Richolt J, Jakab M, Kikinis R. MRI-based Atlas of the Knee. 2015.
See docs/ANATOMICAL_MAP_REFERENCE.md for selection reasons, extent limits and provenance.
"""

from typing import TypedDict

Triple = tuple[float, float, float]


class AtlasPlane(TypedDict):
    orientation: str
    atlas_axis: str
    native_index: int
    coordinate_lps_mm: float
    section_area_mm2: float
    labels: tuple[int, ...]
    all_maximum_indices: tuple[int, ...]
    kind: str


class AtlasSite(TypedDict):
    point_mps_mm: Triple
    span_mm: Triple
    bounds_mps_mm: tuple[Triple, Triple]
    reason: str
    key_planes: tuple[AtlasPlane, ...]


ANTERIOR_CONTACTS_LPS_MM: dict[str, Triple] = {
    # Authoritative label boundary voxel centres, i282; measurements and neighbour
    # labels retained in anatomy-sources/reference-pictures/anterior-surface-measurements.json.
    "femur_at_patella": (7.34951521, -20.38450445, 21.0),  # j329, k80
    "patella_back_at_patella": (7.34951521, -25.65396818, 21.0),  # j348, k80
    "femur_above_patella_lower": (7.34951521, -19.27514366, 43.0),  # j325, k102
    "femur_above_patella_upper": (7.34951521, -18.99780347, 44.0),  # j324, k103
}


ATLAS_SOURCE = "SPL MRI-based Atlas of the Knee, Richolt/Jakab/Kikinis 2015; https://www.openanatomy.org/atlas-pages/atlas-spl-knee.html; seg.nrrd sha256 7b1eba4d06a24d8d769fe0342bf57042d6a6d3afb67da04f2749f62007670091"

ATLAS_SITES: dict[str, AtlasSite] = {
    "femur": {
        "point_mps_mm": (-18.44312307, -2.08005147, 9.0),
        "span_mm": (81.53801779, 65.17494619, 78.0),
        "bounds_mps_mm": (
            (-39.38230791, -28.28870005, -19.5),
            (42.15570988, 36.88624614, 58.5),
        ),
        "reason": "Condyles and enclosed marrow are clear in these three large sections.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 322,
                "coordinate_lps_mm": 18.44312307,
                "section_area_mm2": 2696.85607153,
                "labels": (95,),
                "all_maximum_indices": (322,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 263,
                "coordinate_lps_mm": -2.08005147,
                "section_area_mm2": 4114.61915644,
                "labels": (95,),
                "all_maximum_indices": (263,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 68,
                "coordinate_lps_mm": 9.0,
                "section_area_mm2": 3554.74617406,
                "labels": (95,),
                "all_maximum_indices": (68,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "tibia": {
        "point_mps_mm": (-23.989927, 9.29089659, -29.0),
        "span_mm": (80.9833374, 57.96410108, 46.0),
        "bounds_mps_mm": (
            (-49.36655499, -18.30445297, -58.5),
            (31.61678241, 39.65964811, -12.5),
        ),
        "reason": "Proximal tibial body and plateau are clear in these three large sections.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 342,
                "coordinate_lps_mm": 23.989927,
                "section_area_mm2": 1752.79004238,
                "labels": (96,),
                "all_maximum_indices": (342,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 222,
                "coordinate_lps_mm": 9.29089659,
                "section_area_mm2": 2563.17809678,
                "labels": (96,),
                "all_maximum_indices": (222,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 30,
                "coordinate_lps_mm": -29.0,
                "section_area_mm2": 3397.06512555,
                "labels": (96,),
                "all_maximum_indices": (30,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "fibula": {
        "point_mps_mm": (-42.29437998, 36.47023585, -41.0),
        "span_mm": (29.12072064, 27.456679459999997, 32.0),
        "bounds_mps_mm": (
            (-56.02271971, 21.07785494, -58.5),
            (-26.90199907, 48.5345344, -26.5),
        ),
        "reason": "The separate lateral fibular head is exposed in its three large sections.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 408,
                "coordinate_lps_mm": 42.29437998,
                "section_area_mm2": 582.96909321,
                "labels": (97,),
                "all_maximum_indices": (408,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 124,
                "coordinate_lps_mm": 36.47023585,
                "section_area_mm2": 620.96470014,
                "labels": (97,),
                "all_maximum_indices": (124,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 18,
                "coordinate_lps_mm": -41.0,
                "section_area_mm2": 563.95973057,
                "labels": (97,),
                "all_maximum_indices": (18,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "patella": {
        "point_mps_mm": (-7.34951521, -32.86481329, 21.0),
        "span_mm": (44.65177165, 22.46455592, 39.0),
        "bounds_mps_mm": (
            (-34.39018438, -47.70251381, 4.5),
            (10.26158727, -25.23795789, 43.5),
        ),
        "reason": "The anterior sesamoid is exposed whole in three reference sections; "
        "sagittal282 is an explicit author choice from two equally large planes, "
        "not an automatic tie resolution.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 282,
                "coordinate_lps_mm": 7.34951521,
                "section_area_mm2": 543.3094451,
                "labels": (98,),
                "all_maximum_indices": (277, 282),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 374,
                "coordinate_lps_mm": -32.86481329,
                "section_area_mm2": 1176.75445408,
                "labels": (98,),
                "all_maximum_indices": (374,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 80,
                "coordinate_lps_mm": 21.0,
                "section_area_mm2": 632.03179297,
                "labels": (98,),
                "all_maximum_indices": (80,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "hoffa_fat_pad": {
        "point_mps_mm": (-37.30225644, -18.44312307, -13.0),
        "span_mm": (77.65525505000001, 64.62026581, 56.0),
        "bounds_mps_mm": (
            (-46.59315303, -43.26507067, -39.5),
            (31.06210202, 21.35519514, 16.5),
        ),
        "reason": "The infrapatellar fat wedge behind the patellar tendon is exposed in "
        "its large reference sections.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 390,
                "coordinate_lps_mm": 37.30225644,
                "section_area_mm2": 797.07572497,
                "labels": (9,),
                "all_maximum_indices": (390,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 322,
                "coordinate_lps_mm": -18.44312307,
                "section_area_mm2": 1437.45423887,
                "labels": (9,),
                "all_maximum_indices": (322,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 46,
                "coordinate_lps_mm": -13.0,
                "section_area_mm2": 1390.13150717,
                "labels": (9,),
                "all_maximum_indices": (46,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "medial_meniscus": {
        "point_mps_mm": (25.37662799, 18.99780347, -21.0),
        "span_mm": (43.54241087, 42.98773047, 9.0),
        "bounds_mps_mm": (
            (-11.64828826, -17.74977258, -24.5),
            (31.89412261, 25.23795789, -15.5),
        ),
        "reason": "The medial wedge between condyle and plateau and its open axial C "
        "are exposed.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 164,
                "coordinate_lps_mm": -25.37662799,
                "section_area_mm2": 118.42426394,
                "labels": (82,),
                "all_maximum_indices": (164,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 187,
                "coordinate_lps_mm": 18.99780347,
                "section_area_mm2": 104.83459431,
                "labels": (82,),
                "all_maximum_indices": (187,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 38,
                "coordinate_lps_mm": -21.0,
                "section_area_mm2": 408.66312718,
                "labels": (82,),
                "all_maximum_indices": (38,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "lateral_meniscus": {
        "point_mps_mm": (-38.41161723, 29.25939074, -13.0),
        "span_mm": (41.323689290000004, 34.66752458, 11.0),
        "bounds_mps_mm": (
            (-44.37443145, -1.10936079, -16.5),
            (-3.05074216, 33.55816379, -5.5),
        ),
        "reason": "The lateral wedge and tight axial ring between condyle and "
        "plateau are exposed.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 394,
                "coordinate_lps_mm": 38.41161723,
                "section_area_mm2": 156.41987087,
                "labels": (81,),
                "all_maximum_indices": (394,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 150,
                "coordinate_lps_mm": 29.25939074,
                "section_area_mm2": 137.8380777,
                "labels": (81,),
                "all_maximum_indices": (150,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 46,
                "coordinate_lps_mm": -13.0,
                "section_area_mm2": 392.35659924,
                "labels": (81,),
                "all_maximum_indices": (46,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "meniscus": {
        "point_mps_mm": (-38.41161723, 21.21652504, -21.0),
        "span_mm": (76.26855406, 51.30793637, 19.0),
        "bounds_mps_mm": (
            (-44.37443145, -17.74977258, -24.5),
            (31.89412261, 33.55816379, -5.5),
        ),
        "reason": "Both labelled menisci combined; whole-section reference planes selected "
        "from their union, while sided objects retain their own planes.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 394,
                "coordinate_lps_mm": 38.41161723,
                "section_area_mm2": 156.41987087,
                "labels": (81, 82),
                "all_maximum_indices": (394,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 179,
                "coordinate_lps_mm": 21.21652504,
                "section_area_mm2": 150.04104635,
                "labels": (81, 82),
                "all_maximum_indices": (179,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 38,
                "coordinate_lps_mm": -21.0,
                "section_area_mm2": 408.66312718,
                "labels": (81, 82),
                "all_maximum_indices": (38,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "acl": {
        "point_mps_mm": (-4.02143285, 11.50961816, -13.0),
        "span_mm": (13.86700983, 28.843380439999997, 34.0),
        "bounds_mps_mm": (
            (-9.42956668, -5.26946373, -18.5),
            (4.43744315, 23.57391671, 15.5),
        ),
        "reason": "The notch ligament from anterior tibia toward lateral femoral condyle is "
        "exposed as a long sagittal band and native coronal/axial section.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 270,
                "coordinate_lps_mm": 4.02143285,
                "section_area_mm2": 267.9106299,
                "labels": (31,),
                "all_maximum_indices": (270,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 214,
                "coordinate_lps_mm": 11.50961816,
                "section_area_mm2": 126.18978944,
                "labels": (31,),
                "all_maximum_indices": (214,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 46,
                "coordinate_lps_mm": -13.0,
                "section_area_mm2": 96.53156872,
                "labels": (31,),
                "all_maximum_indices": (46,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "pcl": {
        "point_mps_mm": (2.08005147, 24.5446074, -6.0),
        "span_mm": (24.12859711, 33.28082359, 37.0),
        "bounds_mps_mm": (
            (-10.81626767, 0.55468039, -33.5),
            (13.31232944, 33.83550398, 3.5),
        ),
        "reason": "The curved posterior notch ligament is exposed in large native sections.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 248,
                "coordinate_lps_mm": -2.08005147,
                "section_area_mm2": 204.95440527,
                "labels": (32,),
                "all_maximum_indices": (248,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 167,
                "coordinate_lps_mm": 24.5446074,
                "section_area_mm2": 110.10405804,
                "labels": (32,),
                "all_maximum_indices": (167,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 53,
                "coordinate_lps_mm": -6.0,
                "section_area_mm2": 174.7567523,
                "labels": (32,),
                "all_maximum_indices": (53,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "mcl": {
        "point_mps_mm": (40.3529986, -2.35739167, -4.0),
        "span_mm": (24.960617689999996, 30.507421629999996, 56.0),
        "bounds_mps_mm": (
            (18.58179317, -11.64828826, -42.5),
            (43.54241086, 18.85913337, 13.5),
        ),
        "reason": "The medial band at the joint is exposed along its course and across its body.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 110,
                "coordinate_lps_mm": -40.3529986,
                "section_area_mm2": 351.94470946,
                "labels": (34,),
                "all_maximum_indices": (110,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 264,
                "coordinate_lps_mm": -2.35739167,
                "section_area_mm2": 225.75492002,
                "labels": (34,),
                "all_maximum_indices": (264,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 55,
                "coordinate_lps_mm": -4.0,
                "section_area_mm2": 129.22154219,
                "labels": (34,),
                "all_maximum_indices": (55,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "lcl": {
        "point_mps_mm": (-37.02491624, 25.37662799, 16.0),
        "span_mm": (28.84338045, 30.23008143, 63.0),
        "bounds_mps_mm": (
            (-55.46803932, 8.87488629, -39.5),
            (-26.62465887, 39.10496772, 23.5),
        ),
        "reason": "The lateral cord toward fibular head is exposed along its course and across "
        "its body.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 389,
                "coordinate_lps_mm": 37.02491624,
                "section_area_mm2": 160.57997382,
                "labels": (33,),
                "all_maximum_indices": (389,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 164,
                "coordinate_lps_mm": 25.37662799,
                "section_area_mm2": 171.67358168,
                "labels": (33,),
                "all_maximum_indices": (164,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 75,
                "coordinate_lps_mm": 16.0,
                "section_area_mm2": 100.68511829,
                "labels": (33,),
                "all_maximum_indices": (75,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "patellar_tendon": {
        "point_mps_mm": (-26.76332897, -32.86481329, 5.0),
        "span_mm": (37.71826674, 37.99560693, 75.0),
        "bounds_mps_mm": (
            (-37.44092654, -45.48379224, -55.5),
            (0.2773402, -7.48818531, 19.5),
        ),
        "reason": "The cord below the patella is exposed along the extensor course "
        "and across its body.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 352,
                "coordinate_lps_mm": 26.76332897,
                "section_area_mm2": 249.88351712,
                "labels": (35,),
                "all_maximum_indices": (352,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 374,
                "coordinate_lps_mm": -32.86481329,
                "section_area_mm2": 328.64813295,
                "labels": (35,),
                "all_maximum_indices": (374,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 64,
                "coordinate_lps_mm": 5.0,
                "section_area_mm2": 117.1454814,
                "labels": (35,),
                "all_maximum_indices": (64,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "femoral_cartilage": {
        "point_mps_mm": (-9.56823678, -23.43524661, -10.0),
        "span_mm": (77.93259524, 69.05770895, 42.0),
        "bounds_mps_mm": (
            (-38.27294713, -29.95274123, -21.5),
            (39.65964811, 39.10496772, 20.5),
        ),
        "reason": "The articular layer on the condyles is exposed in large native "
        "sections.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 290,
                "coordinate_lps_mm": 9.56823678,
                "section_area_mm2": 301.74613388,
                "labels": (83,),
                "all_maximum_indices": (290,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 340,
                "coordinate_lps_mm": -23.43524661,
                "section_area_mm2": 497.82565286,
                "labels": (83,),
                "all_maximum_indices": (340,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 49,
                "coordinate_lps_mm": -10.0,
                "section_area_mm2": 887.39817397,
                "labels": (83,),
                "all_maximum_indices": (49,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "tibial_cartilage": {
        "point_mps_mm": (-19.55248386, 22.88056622, -14.0),
        "span_mm": (77.93259524, 50.75325597, 16.0),
        "bounds_mps_mm": (
            (-45.76113244, -12.75764904, -27.5),
            (32.1714628, 37.99560693, -11.5),
        ),
        "reason": "The two tibial articular layers are combined, with three "
        "reference planes selected from their union.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 326,
                "coordinate_lps_mm": 19.55248386,
                "section_area_mm2": 177.49772581,
                "labels": (84, 85),
                "all_maximum_indices": (326,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 173,
                "coordinate_lps_mm": 22.88056622,
                "section_area_mm2": 233.52044552,
                "labels": (84, 85),
                "all_maximum_indices": (173,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 45,
                "coordinate_lps_mm": -14.0,
                "section_area_mm2": 799.78904507,
                "labels": (84, 85),
                "all_maximum_indices": (45,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "medial_gastrocnemius": {
        "point_mps_mm": (4.29877305, 38.41161723, 9.0),
        "span_mm": (42.98773047, 50.753255980000006, 77.0),
        "bounds_mps_mm": (
            (-10.53892747, 12.75764904, -58.5),
            (32.448803, 63.51090502, 18.5),
        ),
        "reason": "The medial calf head behind its condyle: longitudinal body "
        "sections and axial condylar level, avoiding the cropped "
        "distal calf maximum.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 240,
                "coordinate_lps_mm": -4.29877305,
                "section_area_mm2": 2100.01996849,
                "labels": (20,),
                "all_maximum_indices": (240,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 117,
                "coordinate_lps_mm": 38.41161723,
                "section_area_mm2": 2151.05056466,
                "labels": (20,),
                "all_maximum_indices": (117,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 68,
                "coordinate_lps_mm": 9.0,
                "section_area_mm2": 329.13034467,
                "labels": (20,),
                "all_maximum_indices": (1,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "lateral_gastrocnemius": {
        "point_mps_mm": (-21.21652504, 50.05990548, 9.0),
        "span_mm": (49.36655499, 30.78476182, 78.0),
        "bounds_mps_mm": (
            (-51.58527656, 32.7261432, -58.5),
            (-2.21872157, 63.51090502, 19.5),
        ),
        "reason": "The lateral calf head behind its condyle: longitudinal body "
        "sections and axial condylar level, avoiding the cropped "
        "distal calf maximum.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 332,
                "coordinate_lps_mm": 21.21652504,
                "section_area_mm2": 1182.57859821,
                "labels": (21,),
                "all_maximum_indices": (332,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 75,
                "coordinate_lps_mm": 50.05990548,
                "section_area_mm2": 1856.2379357,
                "labels": (21,),
                "all_maximum_indices": (75,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 68,
                "coordinate_lps_mm": 9.0,
                "section_area_mm2": 86.99378823,
                "labels": (21,),
                "all_maximum_indices": (1,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "sartorius": {
        "point_mps_mm": (45.62246234, 12.34163875, 9.0),
        "span_mm": (36.33156575, 34.66752457, 102.0),
        "bounds_mps_mm": (
            (16.91775199, -6.10148432, -43.5),
            (53.24931774, 28.56604025, 58.5),
        ),
        "reason": "The medial muscle sheet: longitudinal body sections and axial condylar "
        "level, avoiding a thigh-coverage maximum.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 91,
                "coordinate_lps_mm": -45.62246234,
                "section_area_mm2": 1400.56799272,
                "labels": (19,),
                "all_maximum_indices": (91,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 211,
                "coordinate_lps_mm": 12.34163875,
                "section_area_mm2": 749.92789155,
                "labels": (19,),
                "all_maximum_indices": (211,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 68,
                "coordinate_lps_mm": 9.0,
                "section_area_mm2": 105.45400854,
                "labels": (19,),
                "all_maximum_indices": (114,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "biceps_femoris_tendon": {
        "point_mps_mm": (-47.00916332, 37.30225644, -28.0),
        "span_mm": (28.56604025, 24.1285971, 103.0),
        "bounds_mps_mm": (
            (-57.1320805, 24.1285971, -44.5),
            (-28.56604025, 48.2571942, 58.5),
        ),
        "reason": "The lateral tendon towards the fibular head is exposed along "
        "its course and across its body.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 425,
                "coordinate_lps_mm": 47.00916332,
                "section_area_mm2": 245.16873378,
                "labels": (42,),
                "all_maximum_indices": (425,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 121,
                "coordinate_lps_mm": 37.30225644,
                "section_area_mm2": 303.41017506,
                "labels": (42,),
                "all_maximum_indices": (121,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 31,
                "coordinate_lps_mm": -28.0,
                "section_area_mm2": 118.45308034,
                "labels": (42,),
                "all_maximum_indices": (31,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "iliotibial_band": {
        "point_mps_mm": (-40.907679, 6.51749462, 36.0),
        "span_mm": (7.765525509999996, 30.23008143, 29.0),
        "bounds_mps_mm": (
            (-44.09709126, -11.37094806, 29.5),
            (-36.33156575, 18.85913337, 58.5),
        ),
        "reason": "The atlas-labelled iliotibial tract is exposed longitudinally and "
        "across its body; this label covers a proximal portion, so exact "
        "distal insertion is not claimed.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 403,
                "coordinate_lps_mm": 40.907679,
                "section_area_mm2": 594.34004127,
                "labels": (43,),
                "all_maximum_indices": (403,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 232,
                "coordinate_lps_mm": 6.51749462,
                "section_area_mm2": 101.78385214,
                "labels": (43,),
                "all_maximum_indices": (232,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 95,
                "coordinate_lps_mm": 36.0,
                "section_area_mm2": 81.99414522,
                "labels": (43,),
                "all_maximum_indices": (95,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "popliteus_tendon": {
        "point_mps_mm": (-36.74757605, 38.13427703, -1.0),
        "span_mm": (27.17933926, 29.12072064, 40.0),
        "bounds_mps_mm": (
            (-42.71039027, 11.37094806, -33.5),
            (-15.53105101, 40.4916687, 6.5),
        ),
        "reason": "The tendon at the lateral femoral sulcus is exposed in its "
        "reference sections.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 388,
                "coordinate_lps_mm": 36.74757605,
                "section_area_mm2": 157.52923166,
                "labels": (44,),
                "all_maximum_indices": (388,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 118,
                "coordinate_lps_mm": 38.13427703,
                "section_area_mm2": 122.02968649,
                "labels": (44,),
                "all_maximum_indices": (118,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 58,
                "coordinate_lps_mm": -1.0,
                "section_area_mm2": 73.30245816,
                "labels": (44,),
                "all_maximum_indices": (58,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "semitendinosus": {
        "point_mps_mm": (28.42737015, 42.57172017, -29.0),
        "span_mm": (24.960617700000004, 45.20645204, 117.0),
        "bounds_mps_mm": (
            (7.7655255, 1.66404118, -58.5),
            (32.7261432, 46.87049322, 58.5),
        ),
        "reason": "The separate medial hamstring tendon: longitudinal body sections "
        "and axial proximal tibial level, rather than the thigh maximum.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 153,
                "coordinate_lps_mm": -28.42737015,
                "section_area_mm2": 223.53619844,
                "labels": (47,),
                "all_maximum_indices": (153,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 102,
                "coordinate_lps_mm": 42.57172017,
                "section_area_mm2": 355.82747221,
                "labels": (47,),
                "all_maximum_indices": (102,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 30,
                "coordinate_lps_mm": -29.0,
                "section_area_mm2": 16.61419828,
                "labels": (47,),
                "all_maximum_indices": (94,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "gracilis": {
        "point_mps_mm": (41.18501919, 23.989927, 2.0),
        "span_mm": (26.62465887, 26.90199907, 104.0),
        "bounds_mps_mm": ((18.02711278, 0.0, -45.5), (44.65177165, 26.90199907, 58.5)),
        "reason": "The thin medial tendon is exposed in its longitudinal sections and axial "
        "body.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 107,
                "coordinate_lps_mm": -41.18501919,
                "section_area_mm2": 201.62632291,
                "labels": (48,),
                "all_maximum_indices": (107,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 169,
                "coordinate_lps_mm": 23.989927,
                "section_area_mm2": 114.26416099,
                "labels": (48,),
                "all_maximum_indices": (169,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 61,
                "coordinate_lps_mm": 2.0,
                "section_area_mm2": 12.30681354,
                "labels": (48,),
                "all_maximum_indices": (61,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "popliteal_artery": {
        "point_mps_mm": (-5.13079364, 40.07565841, 9.0),
        "span_mm": (26.62465887, 36.05422556, 117.0),
        "bounds_mps_mm": (
            (-24.1285971, 8.87488629, -58.5),
            (2.49606177, 44.92911185, 58.5),
        ),
        "reason": "The artery behind the notch: longitudinal course and a common "
        "axial condylar level with the vein, rather than a remote lumen "
        "maximum.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 274,
                "coordinate_lps_mm": 5.13079364,
                "section_area_mm2": 405.4713674,
                "labels": (71,),
                "all_maximum_indices": (274,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 111,
                "coordinate_lps_mm": 40.07565841,
                "section_area_mm2": 350.83534867,
                "labels": (71,),
                "all_maximum_indices": (111,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 68,
                "coordinate_lps_mm": 9.0,
                "section_area_mm2": 55.45757852,
                "labels": (71,),
                "all_maximum_indices": (74,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
    "popliteal_vein": {
        "point_mps_mm": (-12.89631914, 44.51310155, 9.0),
        "span_mm": (27.17933926, 39.936988310000004, 117.0),
        "bounds_mps_mm": (
            (-29.67540103, 12.75764904, -58.5),
            (-2.49606177, 52.69463735, 58.5),
        ),
        "reason": "The vein behind the artery: longitudinal course and a common axial "
        "condylar level with the artery; sagittal302 is an explicit author "
        "choice from two equally large planes.",
        "key_planes": (
            {
                "orientation": "sagittal",
                "atlas_axis": "i",
                "native_index": 302,
                "coordinate_lps_mm": 12.89631914,
                "section_area_mm2": 454.0059018,
                "labels": (72,),
                "all_maximum_indices": (299, 302),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "coronal",
                "atlas_axis": "j",
                "native_index": 95,
                "coordinate_lps_mm": 44.51310155,
                "section_area_mm2": 231.02438375,
                "labels": (72,),
                "all_maximum_indices": (95,),
                "kind": "selected_atlas_reference",
            },
            {
                "orientation": "axial",
                "atlas_axis": "k",
                "native_index": 68,
                "coordinate_lps_mm": 9.0,
                "section_area_mm2": 25.84430844,
                "labels": (72,),
                "all_maximum_indices": (100,),
                "kind": "selected_atlas_reference",
            },
        ),
    },
}
