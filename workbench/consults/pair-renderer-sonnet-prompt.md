Type one Python module body for workbench/render/pair_frames.py. Return the complete source in one
Python fence. You are a mechanical typist; do not alter any contract, choose bars, create tests or
propose design. Production stage and tests are owned by lead. No tools or data access required.

Imports argparse,json,hashlib.sha256,pathlib.Path,textwrap.fill, numpy as np, matplotlib.pyplot as
plt; knee.pictures.pairings as pictures; knee.relations.pairings.PairingReading. No other modules.

Functions settled:
1. saved_array(arrays, descriptors, name, dtype, ndim): raises ValueError for missing name/descriptor,
   mismatched descriptor shape/dtype/contentdigest or expected dtype/ndim. Digest is sha256 of
   array.dtype.str.encode()+str(array.shape).encode()+array.tobytes(). Returns supplied array.
2. saved_panels(run:Path,metadata:dict): loads run/metadata['artifact'] with np.load allow_pickle=False.
   Validates these arrays (name =>dtype/ndim): pairing_source_labels int32/1, pairing_far_labels
   int32/1, pairing_trace_codes uint8/1, pairing_outcome_codes uint8/1, pairing_positions_rc float64/3,
   pairing_contributor_labels int32/3, pairing_band_limits_mm float64/2. P=source.size; shapes must
   be (P,),(P,),(P,),(P,),(P,2,2),(P,2,4),(P,2), respectively. If b1_labels exists, validate int32/2,
   else use empty int32(0,0) only as missing background. Stage metadata metadata['pairings'] has
   code,why,scope,counts,outcome_names,side_order,corner_order,inactive_contributor,unread_contributor.
   Require stage metadata; never recompute counts. Build PairingReading positional fields in order:
   code,why,source_labels,far_labels,trace_codes,outcome_codes,positions_rc,contributor_labels,
   band_limits_mm,counts,scope. Pass through pictures.panels(reading). Return artifact,reading,labels.
3. draw_frame(axis,reading,labels,metadata): imshow nonempty labels with tab20, interpolation nearest.
   Use saved outcome_names and a fixed ten-color palette (you choose just colors, no semantics)
   to scatter near and far saved sites grouped by outcome_codes. Near marker o, far x. For display
   discard nonfinite coordinates only. Plot coordinates[:,1] as x,[:,0] as y; never derive any sites
   or boundaries. No joining lines. Legend uses named codes, includes only displayed groups.
   Title wraps series_uid and stage why/scope and all saved counts, explicitly says
   'flanking sample sites; indexed extents; complete interstices unresolved'. Missing/empty background
   still displays code and counts. Hide axes. No new measurements or claims.
4. main(): CLI positional run, required --study-uid and --out. Refuse out outside project data directory
   Path(__file__).resolve().parents[2]/'data'. Load run/receipt.json, records filtered study_uid, refuse
   no records. One vertical gallery panel per saved series (10x7*n inches, constrained layout).
   Use saved_panels then draw_frame. Save out/series.png dpi160 and out/manifest.json indent2 allow_nan=False.
   Manifest schema pairing-frames-v1, receipt_sha256,renderer_sha256,picture_module_sha256,
   study_uid,image='series.png', series list: series_uid,artifact,artifact_sha256,pairings metadata,
   arrays descriptors of validated pairing arrays and b1_labels if exists. Source digests from files.
   Print JSON with series and manifest paths. Standard if __name__ == '__main__':main().

All output private data/. Preserve every saved code and count; no anatomical naming, no thresholds,
no sampling radius, no downsampling, no segmentation, no interpolated labels, no inferred identities.
