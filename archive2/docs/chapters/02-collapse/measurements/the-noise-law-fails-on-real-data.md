# Stage 1 fails on real data, and why

2026-10-10. First run of the regime key over all 336 series of the 58, through Chapter 1's
`read_series`. Probe: `scratchpad/probe_regime_run.py`. Every series produced a key; none refused
for want of a stacked volume. The readings say the noise law as built does not work.

## What it measured

| word | result |
|---|---|
| **concurrence** | **`concur` 0%.** `dark_abstained` 50.6%, `disagree` 49.4% |
| coil count | `multi` 43.5%, **`implausible_ratio` 31.8%**, `unmeasurable` 18.8%, `single` 6.0% |
| quiet population | `readable` 81.2%, `background_masked` 18.8% |
| storage | unsigned 69.3%, signed-nonnegative 29.2%, signed-negative 1.5% |
| normalization | not flagged 69.6%, **`normalized` 30.4%** |

| reading | min | p25 | median | p75 | max |
|---|---|---|---|---|---|
| dark sigma (n=166) | 0.395 | 2.02 | 4.21 | 8.86 | 67.3 |
| bright sigma (n=336) | 0.332 | 11.6 | 18.6 | 31.2 | 344 |
| **bright / dark** | 0.33 | 3.17 | **5.48** | 10.3 | 64.5 |
| coils (n=166) | 1.00 | 1.42 | **1.86** | 2.37 | 7.53 |

**Not one series out of 336 has the two estimators concurring.** That is a failure of the stage, not
a finding about the corpus.

## Diagnosis 1: the quiet population is a TRUNCATED sample, so its moments are not the noise's

`quiet_population` takes the lowest `share` of a series' finite values **by value**. That is a
sample truncated from above, and the moment identity the coil count rests on —
E[M^4]/E[M^2]^2 = (L+1)/L — holds for a **whole** noncentral-chi distribution, not for its lower
tail.

Worked for the Rayleigh case. Near zero its density goes as f(x) ~ x, so on a truncation to [0, a]:

    E[M^k] = integral x^k * x dx / integral x dx = 2 a^k / (k + 2)
    E[M^2] = a^2 / 2,   E[M^4] = a^4 / 3
    ratio  = (a^4 / 3) / (a^4 / 4) = 4/3 ~ 1.333

which the identity reads as **L = 1 / (1.333 - 1) = 3**, when the truth is L = 1.

That predicts exactly what was measured: a median coil count of **1.86** — not an integer, not a
coil count, **a truncation artifact**. And it predicts the abstentions: where truncation pushes the
ratio outside (1, 2] the identity refuses, `coil_count` returns NaN, and `dark_sigma` abstains
because it will not read a sigma without a channel count. **31.8% implausible + 18.8% unmeasurable
= 50.6%, which is exactly the `dark_abstained` share.** The two numbers match to the decimal, so
the chain of cause is not in doubt.

## Diagnosis 2: the bright estimator measures anatomy, not noise

The bright sigma runs a median of **5.5x the dark one**, up to 64x. That is systematic, not noisy.

`bright_sigma` reads pseudo-residuals, a place minus the mean of four neighbours, scaled so that
**independent** neighbours give back one sigma. In a real knee the neighbours are not independent
samples of a constant: they sit on tissue with edges and texture. The residual therefore measures
**anatomical structure plus noise**, and a MAD over all bright residuals is dominated by the
structure.

The consultant's own prescription said the lag must exceed the measured noise correlation length.
It was never measured; a lag of 2 was passed. But the lag is not the whole fault — even at the
right lag the residual inside textured tissue carries real anatomy. What is wanted is a reading
that finds the **noise floor among local residuals**, not their central tendency.

## Why the tests did not catch it

The unit tests draw **whole** Rayleigh and noncentral-chi samples and recover sigma to within 5%.
They pass, and they are correct about what they test. They never present a **truncated** sample,
and never present **structured** data. So the suite tested the estimator on exactly the two
conditions under which it works, and the real corpus has neither.

This is the unprobed-implementation failure in its plainest form: the synthetic fixture lacked the
property that breaks the code, the suite went green, and stage 2 was built on top of it. The
advisor flagged before stage 2 that "the noise law has only seen synthetic draws" and that it
should be run over the 58 first. That was skipped.

## What is and is not damaged

- **Stage 2's transform is sound in itself.** Given a correct (sigma, L) it is exact, and its
  measured stabilization quality stands. It is being fed bad parameters, which is a different
  fault.
- **The codes are sound.** They named every failure correctly and abstained rather than inventing
  a reading. `dark_abstained` at 50.6% is the decision layer working: it refused to read a sigma
  without a channel count rather than assuming one.
- **The quiet/background split is sound.** 18.8% `background_masked` matches the earlier
  measurement of 62 of 336 series over 20% zeros.
- **`foreground_share` was separately broken** and is already fixed. It anchored on
  `max(quiet)` — the 20th percentile by construction — so it read 0.80 by construction, which the
  run confirms exactly (max 0.800, median 0.788). Codex named this trap in the same round it was
  written: "share above this series' upper tercile is approximately one-third by construction: it
  cannot measure density." It is now anchored on the noise law, at a declared number of noise units
  above the no-signal mean.

## What has to change

Not yet designed; this records the fault, not its repair. The two things that must be settled:

1. **The channel count cannot be read from a truncated sample.** Either it is read from a full
   noise population (which needs background that 18.8% of series do not have), or it is not
   estimated from moments at all and concurrence is what detects a wrong assumption, or a
   truncation-aware estimator is used. Each is a different contract.
2. **The bright estimator needs to find the noise floor among local residuals**, not their central
   tendency, or it will keep reading tissue.

Both are the founder's to rule on, with the measurements above beside them.
