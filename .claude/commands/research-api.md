# /research-api {topic}

## Description
Delegates research tasks to the `api-researcher` subagent.

## Workflow
1. Pass the `{topic}` to the `api-researcher` agent.
2. Remind the agent that its role is RESEARCH ONLY and it must output its findings to the `research/` directory.
3. Present a summary of the findings to the user.