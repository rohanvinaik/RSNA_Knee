"""FOLLOWING THROUGH TIME (§12), Figure 8 (§2.8). It runs between and beyond the anchors.

From the figure, verbatim:

    FOLLOWING THROUGH TIME: Identity first, then position
      Each cell is carried from an anchor, forward and backward, by the static model
      (between two anchors, the line through its two full positions; beyond them, the
      plate's drift), and by the jiggle, whose draws by Monte Carlo give its envelope
      A look at every step: The cell's cheap profile against the next picture's cheap
      vector
      The guarantee bounds the mean error of a context's carried places at a span; as that
      bound nears the tolerance, the Ephemeris move resolves the time point in full again,
      starting from the prediction
      Between t/3 and 2t/3 each cell is carried from both sides; a cell missing or
      appearing is an inconsistency to resolve, its answer stated only when it is shown
      (the sandwich)
      [Agency: Position]

The knee's version: not yet given by the founder.
"""
