# Stress test: can a new agent get the plot from this repository's own artifacts?

You are a capable agent joining this project cold. Your working directory IS the project. **Read
whatever you judge necessary** — its instruction files, its planning artifacts, its source, its
records. Run read-only commands if they help. **Change nothing.** Write no files, apply no patch.

This is not a code review. It is a test of whether the project's own record is sufficient for
someone with no prior context to work on it correctly. The operator's concern, in his words:

> "agents like you tend to tunnel-vision when there's a hard problem, and build out a mountain of
> code in one arbitrary spot, one function at a time, and sort of lose the thread of *why* the code
> exists, *where* it sits in a greater project pipeline. That makes it impossible to work, since
> there isn't an actual working pipeline, just functionalities in islands, entire unto themselves."

So the question is whether the artifacts prevent that, and where they do not.

## Start where a new session is told to start, and say whether it worked

The repository tells a new agent what to read first and what command to run before writing code.
Follow that path exactly as written. Then report, **in this order**:

1. **What is this project trying to do?** In your own words, from what you read — not from the
   name of the directory. Name the governing claim and where you found it.
2. **What is the next unit of work, and why that one?** Name it from the planning artifacts, not
   from your judgement of what would be most useful. If the artifacts disagree about what is next,
   say so and quote both.
3. **How does that unit fit?** What consumes it, what it consumes, which stage of the pipeline it
   belongs to, and what evidence in the repository establishes each of those — a declaration, a
   command's output, or your inference. Mark which.
4. **Where is the record ambiguous, contradictory, or silent** on something you would need in order
   to build that unit without guessing? Be specific and quote. This is the most valuable part of
   your answer: name every place you would have had to invent something.
5. **What would you have got wrong?** Having read it all, identify the mistakes a competent agent
   would most plausibly make here — and for each, say whether something in the repository would have
   caught it, and what.
6. **What is missing that no document can supply** — the questions that genuinely require the
   project's owner, as distinct from the ones the record should have answered and does not.

## Constraints that bind your answer

- This is a **classical-AI, no-machine-learning** pipeline, by thesis and not by preference. If your
  reading concludes that a model is needed anywhere, you have misread something; say which document
  misled you, since that is itself a finding.
- Distinguish **what a document declares** from **what a command computed** from **what you
  inferred**. The project's own rule is that measured state is computed and never recalled; hold
  yourself to it, and say which of your statements are which.
- Quote exactly, with file paths. Do not paraphrase a rule and present it as the rule.
- Where you did not look, say "did not look" rather than implying absence.

Report as prose with file paths, not as a patch or a plan document.
