# autonomous_client.py

import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
import sys
import uuid

async def main():
    # Path to the server script
    if len(sys.argv) < 2:
        print("Usage: python autonomous_client.py /path/to/autonomous_self_reflection.py")
        return
    
    server_script_path = sys.argv[1]
    
    # Connect to the server
    server_params = StdioServerParameters(
        command="python",
        args=[server_script_path]
    )
    
    async with stdio_client(server_params) as session:
        print("Connected to Autonomous Self-Reflection Claude MCP Server")
        
        # Display server info
        info = await session.get_info()
        print(f"Server name: {info.name}")
        print(f"Version: {info.version}")
        
        # Get available tools
        tools = await session.list_tools()
        print("\nAvailable tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
        
        # Get available resources
        resources = await session.list_resources()
        print("\nAvailable resources:")
        for resource in resources:
            print(f"- {resource.uri}: {resource.description}")
        
        # Interactive mode - let user choose what to do
        while True:
            print("\n--- Autonomous Self-Reflection Client Menu ---")
            print("1. Simulate conversation with error detection")
            print("2. Check for similar scenarios")
            print("3. View recent scenarios")
            print("4. Get learning statistics")
            print("5. Record learning scenario manually")
            print("6. Test knowledge recall")
            print("7. Clear all scenarios")
            print("8. Exit")
            
            choice = input("\nEnter your choice (1-8): ")
            
            if choice == '1':
                # Simulate conversation with error detection
                print("\n--- Simulating Conversation ---")
                conversation_id = str(uuid.uuid4())
                print(f"Conversation ID: {conversation_id}")
                
                # Get context for this conversation
                try:
                    context = await session.get_resource(f"conversation://{conversation_id}")
                    print(f"Context: {context}")
                except Exception as e:
                    print(f"Error getting context: {e}")
                
                # User message
                user_message = input("\nEnter user message (e.g., 'How many r's are in strawberry?'):\n")
                
                # Claude's initial (potentially incorrect) response
                initial_response = input("\nEnter Claude's initial response:\n")
                
                # Process initial interaction
                await session.invoke_tool(
                    "process_user_interaction",
                    {
                        "conversation_id": conversation_id,
                        "user_message": user_message,
                        "claude_response": initial_response,
                        "is_correction": False
                    }
                )
                
                # User correction
                user_correction = input("\nEnter user correction (if any, or press Enter to skip):\n")
                
                if user_correction.strip():
                    # Claude's corrected response
                    corrected_response = input("\nEnter Claude's corrected response:\n")
                    error_explanation = input("\nEnter error explanation:\n")
                    
                    # Record correction
                    result = await session.invoke_tool(
                        "detect_and_record_correction",
                        {
                            "conversation_id": conversation_id,
                            "user_message": user_correction,
                            "previous_response": initial_response,
                            "corrected_response": corrected_response,
                            "error_explanation": error_explanation
                        }
                    )
                    print(f"\nCorrection recorded: {result}")
                    
                    # Process corrected interaction
                    await session.invoke_tool(
                        "process_user_interaction",
                        {
                            "conversation_id": conversation_id,
                            "user_message": user_correction,
                            "claude_response": corrected_response,
                            "is_correction": True
                        }
                    )
                
                print("\nConversation simulation completed.")
                
            elif choice == '2':
                # Check for similar scenarios
                query = input("Enter the query to check for similar scenarios:\n")
                threshold = float(input("Enter similarity threshold (0.0-1.0, default 0.35): ") or 0.35)
                max_results = int(input("Enter maximum number of results (default 3): ") or 3)
                
                result = await session.invoke_tool(
                    "check_similar_scenarios",
                    {
                        "query": query,
                        "threshold": threshold,
                        "max_results": max_results
                    }
                )
                print(f"Similar scenarios: \n{result}")
                
            elif choice == '3':
                # View recent scenarios
                limit = int(input("Enter number of recent scenarios to view (default 5): ") or 5)
                
                result = await session.invoke_tool(
                    "get_recent_scenarios",
                    {
                        "limit": limit
                    }
                )
                print(result)
                
            elif choice == '4':
                # Get learning statistics
                result = await session.invoke_tool("get_learning_statistics", {})
                print(result)
                
            elif choice == '5':
                # Record learning scenario manually
                user_query = input("Enter the original user query:\n")
                initial_response = input("Enter Claude's initial response:\n")
                error_context = input("Enter the error context (what went wrong):\n")
                corrected_solution = input("Enter the corrected solution:\n")
                reasoning = input("Enter the reasoning/learning:\n")
                tags = input("Enter tags (comma-separated):\n")
                
                result = await session.invoke_tool(
                    "record_learning_scenario",
                    {
                        "user_query": user_query,
                        "initial_response": initial_response,
                        "error_context": error_context,
                        "corrected_solution": corrected_solution,
                        "reasoning": reasoning,
                        "tags": tags
                    }
                )
                print(f"Result: {result}")
                
            elif choice == '6':
                # Test knowledge recall
                query = input("Enter query to test knowledge recall:\n")
                
                result = await session.invoke_tool(
                    "recall_relevant_knowledge",
                    {
                        "query": query
                    }
                )
                print(f"Recalled knowledge: \n{result}")
                
            elif choice == '7':
                # Clear all scenarios
                confirm = input("Are you sure you want to clear ALL scenarios? (yes/no): ")
                if confirm.lower() == 'yes':
                    result = await session.invoke_tool("clear_all_scenarios", {})
                    print(result)
                else:
                    print("Operation cancelled.")
                
            elif choice == '8':
                # Exit
                print("Exiting client. Goodbye!")
                break
                
            else:
                print("Invalid choice. Please enter a number between 1 and 8.")

if __name__ == "__main__":
    asyncio.run(main())