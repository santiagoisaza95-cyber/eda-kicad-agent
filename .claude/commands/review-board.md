# /review-board {name}

## Description
Orchestrates the 3-agent adversarial review pipeline for a given board.

## Workflow
1. Invoke the **Design Reviewer** agent to evaluate the board. The reviewer writes to `review/{name}_review.md`.
2. Invoke the **Design Defender** agent to read `review/{name}_review.md` and write its defense to `review/{name}_defense.md`.
3. Invoke the **Design Referee** agent to read both the review and defense, and write the final verdict to `review/{name}_verdict.md`.
4. Present the final action items from the verdict directly to the user.