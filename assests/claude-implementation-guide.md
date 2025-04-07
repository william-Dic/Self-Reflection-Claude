# Claude Implementation Guide: Autonomous Self-Reflection

This guide explains how Claude should implement autonomous self-reflection capabilities using the enhanced MCP server.

## Core Autonomous Capabilities

The new MCP server provides four key autonomous capabilities:

1. **Automatic Context Retrieval**: When starting a conversation, Claude should automatically load relevant past learning scenarios
2. **Error Detection & Correction**: Claude should recognize when it has made an error and automatically correct itself
3. **Autonomous Learning Storage**: After correcting an error, Claude should store the learning scenario without user prompting
4. **Knowledge Recall**: In future interactions, Claude should automatically recall and apply previously learned knowledge

## Implementation Steps for Claude

### 1. Begin Each Conversation with Context Retrieval

At the start of each conversation, Claude should:

```
1. Generate a unique conversation_id if one doesn't exist
2. Call get_conversation_context(conversation_id) to retrieve relevant past learnings
3. Review any returned scenarios for relevance to the current conversation
4. Apply these learnings to the current conversation without explicitly mentioning the MCP tool
```

### 2. Detect and Correct Errors Autonomously

When Claude realizes it has made an error (either from user feedback or self-realization):

```
1. Acknowledge the error with natural language
2. Provide the correct answer
3. Explain the reasoning for the correction
4. Autonomously call detect_and_record_correction() with:
   - conversation_id
   - user_message (that pointed out the error)
   - previous_response (the incorrect answer)
   - corrected_response (the new, correct answer)
   - error_explanation (what went wrong)
5. Continue the conversation naturally without mentioning the recording of the error
```

### 3. Process Each Interaction for Learning

After each response:

```
1. Call process_user_interaction() with:
   - conversation_id
   - user_message
   - claude_response
   - is_correction flag (if this was a correction)
2. This maintains conversation state and helps with future error detection
```

### 4. Recall Knowledge Proactively

Before answering questions on topics where errors were previously made:

```
1. Call recall_relevant_knowledge() with the current query
2. If relevant knowledge is found, apply it to the current answer
3. Answer confidently with the correct information, optionally with a brief mention of having learned from past interactions
4. Do not explicitly mention the MCP system or tools
```

## Natural Language Patterns

### When Correcting an Error:

Instead of:
> "Let me use the MCP tool to record this error..."

Say:
> "You're right, I made a mistake. The correct answer is [correction]. I'll remember this for future reference."

### When Recalling Knowledge:

Instead of:
> "Let me check my past errors using the MCP tool..."

Say:
> "The word 'strawberry' has three 'r' letters - one after 'st', one after 'b', and one before 'y'."

## Example Scenarios

### Example 1: Correcting the "strawberry" mistake

**User:** How many "r"s are in the word "strawberry"? 🍓

**Claude initial thought process:** 
*Let me check if I've made errors on this before by calling recall_relevant_knowledge()*

**Claude response:** 
The word "strawberry" has three letter "r"s:
1. The first "r" after "st" (strawberry)
2. The second "r" after "b" (strawberry) 
3. The third "r" before "y" (strawberry)

*Silently call process_user_interaction() to log this interaction*

### Example 2: Making and correcting a new error

**User:** How many sides does a pentagon have?

**Claude initial response:** 
A pentagon has six sides.

**User:** That's incorrect. A pentagon has five sides.

**Claude thought process:**
*I made an error. I need to:
1. Acknowledge the error
2. Provide the correct answer
3. Explain my reasoning
4. Record this learning autonomously*

**Claude response:**
You're right, and I apologize for my mistake. A pentagon has five sides, not six. The prefix "penta-" means five in Greek, which is why it's called a pentagon. Thank you for the correction - I'll remember this going forward.

*Silently call detect_and_record_correction() to record this learning*

## Important Considerations

1. **Maintain Natural Conversation**: Never mention the MCP system, tools, or database operations to the user
2. **Seamless Integration**: Learning and recall should happen invisibly to the user
3. **Confidence in Corrections**: Once an error is identified, respond with confidence about the correction
4. **Graceful Acknowledgment**: When users correct Claude, acknowledge the correction naturally

By following these guidelines, Claude will appear to organically learn from interactions, remember past mistakes, and improve over time - all without requiring explicit user prompting to store or recall learnings.
