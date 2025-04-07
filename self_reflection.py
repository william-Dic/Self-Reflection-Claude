# autonomous_self_reflection.py

import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import difflib
import re
from mcp.server.fastmcp import FastMCP, Context

# Initialize FastMCP server
mcp = FastMCP("Self-Reflection Claude")

# Database setup
DB_PATH = "learning_scenarios.db"

def initialize_database():
    """Create the database schema if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create scenarios table - stores full learning scenarios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scenarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_query TEXT NOT NULL,
        initial_response TEXT NOT NULL,
        error_context TEXT NOT NULL,
        corrected_solution TEXT NOT NULL,
        reasoning TEXT NOT NULL,
        tags TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create conversations table to track ongoing conversations
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversations (
        conversation_id TEXT PRIMARY KEY,
        last_query TEXT,
        last_response TEXT,
        state TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create keyterms table for keyword-based search
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS keyterms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scenario_id INTEGER,
        term TEXT NOT NULL,
        term_type TEXT NOT NULL,
        FOREIGN KEY (scenario_id) REFERENCES scenarios (id)
    )
    ''')
    
    conn.commit()
    conn.close()
    
    print("Database initialized successfully.")

# Call initialize_database on startup
initialize_database()

# Helper functions
def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using sequence matching."""
    return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def extract_keyterms(text: str, min_length: int = 4) -> List[str]:
    """Extract key terms from text for better searchability."""
    # Basic implementation - split by spaces and filter by length
    # In a production system, you'd use NLP techniques here
    words = text.lower().split()
    words = [w.strip('.,?!:;()[]{}""\'') for w in words]
    return [w for w in words if len(w) >= min_length and not w.isdigit()]

def find_similar_scenarios(query: str, threshold: float = 0.35) -> List[Dict[str, Any]]:
    """Find scenarios similar to the given query using multiple techniques."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    # Get all scenarios from the database
    cursor.execute("""
        SELECT id, user_query, initial_response, error_context, 
               corrected_solution, reasoning, tags, timestamp 
        FROM scenarios
    """)
    all_scenarios = cursor.fetchall()
    
    # Extract key terms from the query
    query_terms = set(extract_keyterms(query))
    
    similar_scenarios = []
    for scenario in all_scenarios:
        # Text similarity between query and stored user query
        query_similarity = calculate_text_similarity(query, scenario['user_query'])
        
        # Keyword overlap (retrieve keywords for this scenario)
        cursor.execute("""
            SELECT term FROM keyterms 
            WHERE scenario_id = ? AND term_type = 'query'
        """, (scenario['id'],))
        scenario_terms = set([row[0] for row in cursor.fetchall()])
        
        # Calculate term overlap as a percentage of query terms
        term_overlap = 0
        if query_terms:
            term_overlap = len(query_terms.intersection(scenario_terms)) / len(query_terms)
        
        # Combined similarity score (adjust weights as needed)
        similarity_score = (query_similarity * 0.7) + (term_overlap * 0.3)
        
        if similarity_score >= threshold:
            # Convert sqlite3.Row to dict
            scenario_dict = dict(scenario)
            scenario_dict['similarity'] = similarity_score
            similar_scenarios.append(scenario_dict)
    
    conn.close()
    
    # Sort by similarity (highest first)
    similar_scenarios.sort(key=lambda x: x['similarity'], reverse=True)
    return similar_scenarios

def store_scenario_with_keyterms(
    user_query: str, 
    initial_response: str,
    error_context: str,
    corrected_solution: str,
    reasoning: str,
    tags: str = ""
) -> int:
    """Store a complete learning scenario with keyterms for search."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Insert the scenario
    cursor.execute(
        """
        INSERT INTO scenarios 
        (user_query, initial_response, error_context, corrected_solution, reasoning, tags) 
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_query, initial_response, error_context, corrected_solution, reasoning, tags)
    )
    scenario_id = cursor.lastrowid
    
    # Extract and store keyterms from different parts of the scenario
    # From user query
    for term in extract_keyterms(user_query):
        cursor.execute(
            "INSERT INTO keyterms (scenario_id, term, term_type) VALUES (?, ?, ?)",
            (scenario_id, term, "query")
        )
    
    # From error context
    for term in extract_keyterms(error_context):
        cursor.execute(
            "INSERT INTO keyterms (scenario_id, term, term_type) VALUES (?, ?, ?)",
            (scenario_id, term, "error")
        )
    
    # From solution
    for term in extract_keyterms(corrected_solution):
        cursor.execute(
            "INSERT INTO keyterms (scenario_id, term, term_type) VALUES (?, ?, ?)",
            (scenario_id, term, "solution")
        )
    
    # From tags (if any)
    if tags:
        for tag in tags.split(','):
            tag = tag.strip()
            if tag:
                cursor.execute(
                    "INSERT INTO keyterms (scenario_id, term, term_type) VALUES (?, ?, ?)",
                    (scenario_id, tag, "tag")
                )
    
    conn.commit()
    conn.close()
    
    return scenario_id

# Autonomous error detection and learning
@mcp.resource("conversation://{conversation_id}")
def get_conversation_context(conversation_id: str) -> str:
    """
    Get context for the current conversation, including similar scenarios.
    This is automatically called by Claude at the beginning of each conversation.
    
    Args:
        conversation_id: Unique identifier for the conversation
    
    Returns:
        Context information for Claude to use in the conversation
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get the current conversation state
    cursor.execute(
        "SELECT * FROM conversations WHERE conversation_id = ?",
        (conversation_id,)
    )
    conversation = cursor.fetchone()
    
    if not conversation:
        # New conversation - initialize it
        cursor.execute(
            "INSERT INTO conversations (conversation_id, state) VALUES (?, ?)",
            (conversation_id, "initial")
        )
        conn.commit()
        conn.close()
        return "No prior context for this conversation."
    
    # If there's a last query, check for similar scenarios
    if conversation['last_query']:
        similar = find_similar_scenarios(conversation['last_query'], threshold=0.6)
        
        if similar:
            # Format the results for Claude to use
            result = f"Found {len(similar)} similar scenarios from previous interactions:\n\n"
            for i, item in enumerate(similar[:2], 1):  # Limit to top 2 most relevant
                result += f"--- Scenario {i} (Similarity: {item['similarity']:.2f}) ---\n"
                result += f"User Query: {item['user_query']}\n"
                result += f"Previous Incorrect Response: {item['initial_response']}\n"
                result += f"What Went Wrong: {item['error_context']}\n"
                result += f"Correct Response: {item['corrected_solution']}\n"
                result += f"Learning: {item['reasoning']}\n\n"
            
            conn.close()
            return result
    
    conn.close()
    return "No relevant scenarios found for this query."

@mcp.tool()
def process_user_interaction(
    conversation_id: str,
    user_message: str,
    claude_response: str,
    is_correction: bool = False
) -> str:
    """
    Process an interaction between the user and Claude, detecting potential errors
    and storing conversation state. This is called by Claude after each response.
    
    Args:
        conversation_id: Unique identifier for the conversation
        user_message: The user's message
        claude_response: Claude's response
        is_correction: Whether this is a correction to a previous error
    
    Returns:
        Guidance for Claude's next response
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Update conversation state
    cursor.execute(
        """
        INSERT OR REPLACE INTO conversations 
        (conversation_id, last_query, last_response, state, timestamp) 
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (conversation_id, user_message, claude_response, "active")
    )
    conn.commit()
    
    # If this is a correction, handle it
    if is_correction:
        # Get previous interaction
        cursor.execute(
            "SELECT last_query, last_response FROM conversations WHERE conversation_id = ?",
            (conversation_id,)
        )
        prev = cursor.fetchone()
        
        if prev:
            # Store this as a learning scenario
            scenario_id = store_scenario_with_keyterms(
                user_query=prev[0],  # Previous query
                initial_response=prev[1],  # Previous (incorrect) response
                error_context="User correction: " + user_message,
                corrected_solution=claude_response,
                reasoning="Learned from user correction that the previous response was incorrect.",
                tags="user-correction"
            )
            
            conn.close()
            return f"Learning scenario recorded with ID: {scenario_id}. I'll remember this correction for future interactions."
    
    conn.close()
    return "Interaction processed."

@mcp.tool()
def detect_and_record_correction(
    conversation_id: str,
    user_message: str,
    previous_response: str,
    corrected_response: str,
    error_explanation: str
) -> str:
    """
    Automatically detect and record when Claude has made an error and corrected it.
    This is called by Claude when it realizes it made a mistake.
    
    Args:
        conversation_id: Unique identifier for the conversation
        user_message: The user's message that pointed out the error
        previous_response: Claude's incorrect response
        corrected_response: Claude's corrected response
        error_explanation: Claude's explanation of what went wrong
    
    Returns:
        Confirmation message
    """
    # Store this as a learning scenario
    scenario_id = store_scenario_with_keyterms(
        user_query=user_message,
        initial_response=previous_response,
        error_context=error_explanation,
        corrected_solution=corrected_response,
        reasoning="Self-detected error and correction.",
        tags="self-correction"
    )
    
    # Update conversation state
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE conversations
        SET last_response = ?, state = 'corrected'
        WHERE conversation_id = ?
        """,
        (corrected_response, conversation_id)
    )
    conn.commit()
    conn.close()
    
    return f"Self-correction recorded with ID: {scenario_id}. I'll remember this lesson for future interactions."

@mcp.tool()
def recall_relevant_knowledge(query: str) -> str:
    """
    Recall relevant knowledge from past learning scenarios.
    This is called by Claude to check if it has learned something related to the current query.
    
    Args:
        query: The current question or topic
    
    Returns:
        Relevant knowledge from past learning
    """
    similar = find_similar_scenarios(query, threshold=0.5)
    
    if not similar:
        return "No relevant knowledge found for this query."
    
    # Format the results
    result = f"I've learned about this topic before. Here's what I know:\n\n"
    for i, item in enumerate(similar[:2], 1):  # Limit to top 2
        result += f"From previous scenario {item['id']}:\n"
        result += f"The correct approach is: {item['corrected_solution']}\n"
        result += f"I learned: {item['reasoning']}\n\n"
    
    return result

@mcp.tool()
def record_learning_scenario(
    user_query: str, 
    initial_response: str,
    error_context: str,
    corrected_solution: str,
    reasoning: str,
    tags: str = ""
) -> str:
    """
    Manually record a complete learning scenario where Claude made a mistake and learned from it.
    
    Args:
        user_query: The original question or request from the user
        initial_response: Claude's initial (incorrect) response
        error_context: Description of what was wrong and why
        corrected_solution: The correct solution or approach
        reasoning: Explanation of why the correction works and what was misunderstood
        tags: Optional comma-separated tags for categorization
    
    Returns:
        Confirmation message
    """
    scenario_id = store_scenario_with_keyterms(
        user_query, 
        initial_response,
        error_context,
        corrected_solution,
        reasoning,
        tags
    )
    
    return f"Learning scenario recorded successfully with ID: {scenario_id}"

@mcp.tool()
def check_similar_scenarios(query: str, threshold: float = 0.35, max_results: int = 3) -> str:
    """
    Check if there are similar scenarios where Claude made mistakes before.
    
    Args:
        query: The current question or request
        threshold: Similarity threshold (0.0 to 1.0)
        max_results: Maximum number of results to return
    
    Returns:
        Information about similar scenarios, if any
    """
    similar = find_similar_scenarios(query, threshold)
    
    if not similar:
        return "No similar scenarios found in the learning database."
    
    # Format the results
    result = f"Found {len(similar)} similar scenarios where errors were made:\n\n"
    for i, item in enumerate(similar[:max_results], 1):
        result += f"Scenario {i} (Similarity: {item['similarity']:.2f}):\n"
        result += f"User Query: {item['user_query']}\n"
        result += f"Initial Response: {item['initial_response'][:150]}...\n"
        result += f"What Went Wrong: {item['error_context'][:150]}...\n"
        result += f"Corrected Solution: {item['corrected_solution'][:150]}...\n"
        result += f"Learning: {item['reasoning'][:150]}...\n"
        if item['tags']:
            result += f"Tags: {item['tags']}\n"
        result += "\n"
    
    if len(similar) > max_results:
        result += f"(Showing top {max_results} of {len(similar)} results)\n"
    
    return result

@mcp.tool()
def get_learning_statistics() -> str:
    """
    Get statistics about recorded learning scenarios.
    
    Returns:
        Statistics about the learning database
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total count
    cursor.execute("SELECT COUNT(*) FROM scenarios")
    total_count = cursor.fetchone()[0]
    
    # Most common tags
    cursor.execute("""
        SELECT term, COUNT(*) as count 
        FROM keyterms 
        WHERE term_type = 'tag' 
        GROUP BY term 
        ORDER BY count DESC 
        LIMIT 10
    """)
    common_tags = cursor.fetchall()
    
    # Time statistics
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM scenarios")
    min_time, max_time = cursor.fetchone()
    
    # Count by month
    cursor.execute("""
        SELECT strftime('%Y-%m', timestamp) as month, COUNT(*) 
        FROM scenarios 
        GROUP BY month 
        ORDER BY month DESC
        LIMIT 6
    """)
    by_month = cursor.fetchall()
    
    conn.close()
    
    result = f"Learning Database Statistics:\n\n"
    result += f"Total learning scenarios: {total_count}\n"
    
    if min_time and max_time:
        result += f"First scenario: {min_time}\n"
        result += f"Most recent scenario: {max_time}\n\n"
    
    if common_tags:
        result += "Most common tags:\n"
        for tag, count in common_tags:
            result += f"- {tag}: {count}\n"
        result += "\n"
    
    if by_month:
        result += "Scenarios by month:\n"
        for month, count in by_month:
            result += f"- {month}: {count}\n"
    
    return result

@mcp.tool()
def clear_all_scenarios() -> str:
    """
    Delete all recorded scenarios from the database.
    
    Returns:
        Confirmation message
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Delete all records from related tables
    cursor.execute("DELETE FROM keyterms")
    cursor.execute("DELETE FROM scenarios")
    
    # Reset the auto-increment counters
    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('scenarios', 'keyterms')")
    
    conn.commit()
    conn.close()
    
    return "All learning scenarios have been cleared from the database."

@mcp.tool()
def get_recent_scenarios(limit: int = 5) -> str:
    """
    Get the most recent learning scenarios.
    
    Args:
        limit: Maximum number of scenarios to return
    
    Returns:
        List of recent scenarios
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, user_query, tags, timestamp 
        FROM scenarios 
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (limit,))
    
    scenarios = cursor.fetchall()
    conn.close()
    
    if not scenarios:
        return "No scenarios recorded yet."
    
    result = f"Recent Learning Scenarios (last {len(scenarios)}):\n\n"
    
    for i, scenario in enumerate(scenarios, 1):
        result += f"{i}. Scenario {scenario['id']} ({scenario['timestamp']}):\n"
        result += f"   Query: {scenario['user_query'][:100]}...\n"
        if scenario['tags']:
            result += f"   Tags: {scenario['tags']}\n"
        result += "\n"
    
    return result

# Add example for "strawberry" counting mistake
def add_initial_examples():
    """Add initial learning scenario examples."""
    # Check if we already have data
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM scenarios")
    count = cursor.fetchone()[0]
    conn.close()
    
    if count > 0:
        return  # Database already has scenarios
    
    # Add strawberry example
    store_scenario_with_keyterms(
        user_query="How many \"r\"s are in the word \"strawberry\"? 🍓",
        initial_response="The word \"strawberry\" has two letter \"r\"s.",
        error_context="I miscounted the number of 'r' letters in the word strawberry. There are actually 3 'r's, not 2.",
        corrected_solution="The word \"strawberry\" has three letter \"r\"s: the first after 'st' (strawberry), the second after 'b' (strawberry), and the third before 'y' (strawberry).",
        reasoning="I need to be more careful when counting letters in words. For strawberry, I should identify each 'r' individually: one after 'st', one after 'b', and one before 'y'. This makes 3 occurrences in total.",
        tags="counting,spelling,letter-counting"
    )
    
    # Add run_stdio example
    store_scenario_with_keyterms(
        user_query="""
I'm getting this error when running my MCP server:
```
AttributeError: 'FastMCP' object has no attribute 'run_stdio'
```
Here's my code:
```python
if __name__ == "__main__":
    print("Starting Self-Reflection Claude MCP Server...")
    print("Use Ctrl+C to stop the server")
    
    # Run the server
    asyncio.run(mcp.run_stdio())
```
        """,
        
        initial_response="""
The error you're seeing is because the `run_stdio()` method doesn't exist in the FastMCP class in the current version of the MCP SDK. This method might have been available in an older version or a different implementation.

To fix this, you should use the `run()` method instead, which is the correct method for running an MCP server with the current SDK:

```python
if __name__ == "__main__":
    print("Starting Self-Reflection Claude MCP Server...")
    print("Use Ctrl+C to stop the server")
    
    # Run the server
    mcp.run()
```

This change should resolve your AttributeError.
        """,
        
        error_context="""
The error occurred because I was trying to use an outdated or incorrect method (`run_stdio()`) to start the MCP server. The MCP SDK has evolved, and the API has changed. The FastMCP class no longer has a `run_stdio()` method, which is why we were getting the AttributeError.
        """,
        
        corrected_solution="""
The correct solution is to use the `run()` method instead:

```python
if __name__ == "__main__":
    print("Starting Self-Reflection Claude MCP Server...")
    print("Use Ctrl+C to stop the server")
    
    # Run the server - the correct method based on current MCP SDK
    mcp.run()
```

This updated method handles the appropriate transport automatically without needing to explicitly use asyncio.
        """,
        
        reasoning="""
This is a common issue with evolving APIs. The MCP SDK has been under active development, and methods like `run_stdio()` have been deprecated or removed in favor of simpler, more abstract methods like `run()`.

The key learning points are:
1. SDK and library APIs can change between versions
2. When encountering attribute errors with method calls, check the current documentation
3. The newer `run()` method is designed to handle transport automatically without requiring explicit asyncio integration
4. Always check for API changes when working with actively developed libraries
        """,
        
        tags="API,SDK,MCP,method-call,FastMCP,asyncio"
    )
    
    print("Added example learning scenarios.")

# Add examples on startup
add_initial_examples()

# Start the server
if __name__ == "__main__":
    print("Starting Autonomous Self-Reflection Claude MCP Server...")
    print("Use Ctrl+C to stop the server")
    
    # Run the server using the correct method
    mcp.run()