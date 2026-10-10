# Founder teachings, 2026-10-10

Verbatim from the founder's prompt at 2026-10-10T09:42:36Z, preserved from the pre-compact
snapshot. The black/speck teachings are also recorded in `src/knee/collapse/__init__.py`.

## Black and speck (also in collapse docstring)

> "Black" isn't a color. It's the structural elements of the problem space that can be resolved
> out, because they never contain information or data that is itself informative for positive
> resolution of the categorization we care about. In the cell microscopy build, it was literally
> the "black" space of the microscopy movie. The literal pixel count was non-zero, but that space
> NEVER contained actual cells. That isn't the same as "junk", it's important to have positive
> assignment of what that space is. Rigorous characterization of the structural elements that are
> the equivalent of "black"--parts of the data that *aren't* what you care about-- inherently
> helps resolve the parts you *do* care about more cleanly. So in this project, "black" is the
> space of the data we are given that does not actually ever relate in any way to the 12 possible
> categories, and the context that is needed to resolve them. Note here that we actually have
> SUPER obvious resolution of the image. Unlike cells, knee images have a GINORMOUS normalization
> flag--the giant fucking black-ish line that is the connection point between the tibia and femur.
> It's why the "KneeDiff" idea spoke to ideas of aligning different images to a defined
> normalization, a "platonic" version of a knee. Cell microscopy is images of a whole bunch of
> small objects randomly thrown about a plate. Knee imaging is HIGHLY structured; doctors tell
> people to place their knee in the machine and DON'T MOVE while imaging; the images are VERY
> regular, and we should be taking advantage of that. It's about discovering structure and noting
> where we actually can have "surprise" vs where the image is simply uninteresting or common
> across knees, and not waste compute and analysis on the parts that medicine LITERALLY already
> tries to normalize for diagnosis

> "Speck" refers to appropriate characterization of scale. Again, data is noisy and busy. What we
> need is appropriate characterization of scale. If an object is only resolvable as a multi-pixel
> profile over a certain span, then objects that are definitionally WAY below the minimum possible
> size (e.g. if a knee diagnosis can only appear within X cm from the tibia-femur conjunction
> site, then stuff that's too far from it, or too small to represent resolvable damage that is
> diagnosable, isn't what we need).

## Computer vision

> Computer vision, simply put, is the process by which computers perform reasoning operations on
> data that is visual in nature, and thus in which significance is visual/physical in nature.
> Literally the whole point of the thesis is an articulation of how one breaks down visual problem
> spaces so that the computer can reason off it, because computers *can't* build descriptions
> purely from what the picture shows.

## The `<object>` — "there is no noise" — information-theoretic shrimp

> The central point of the thesis is that computer vision isn't actually a hard problem. Computer
> vision can be conducted with rather simple compute operations, because by definition "vision" is
> itself a highly constrained domain space, and that decomposing a visual domain space
> structurally involves resolving the significance of every SINGLE element in the data. The "there
> is no noise" concept--not that noise doesn't exist, but that in a constrained domain space,
> confident resolution of "noise" or "not useful" elements is *itself* useful for resolving what
> *is* the data you want. The only thing that counts as "noise" is genuine entropy, pure random
> noise that is unrelated to anything that exists as a resolvable physical entity. Static, or
> solar radiation, or whatever. We're information-theoretic shrimp--scrounging at the bottom of
> the sea for any and all little pieces of information we can resolve above and beyond entropy
