import argparse
import time
from agent import BasicAgent

def test_agent_with_question(question, task_id=None):
    """
    Test the BasicAgent with a single question.
    
    Args:
        question (str): The question to test
        task_id (str, optional): A task ID for tracking. Defaults to a timestamp.
    
    Returns:
        str: The agent's response
    """
    if task_id is None:
        task_id = f"test_{int(time.time())}"
    
    print(f"\n{'='*80}")
    print(f"TESTING AGENT WITH QUESTION: {question}")
    print(f"TASK ID: {task_id}")
    print(f"{'='*80}\n")
    
    # Initialize the agent
    agent = BasicAgent()
    
    # Time the execution
    start_time = time.time()
    
    # Run the agent
    try:
        response = agent(question, task_id)
        execution_time = time.time() - start_time
        
        print(f"\n{'='*80}")
        print(f"AGENT RESPONSE:")
        print(f"{'-'*80}")
        print(response)
        print(f"{'-'*80}")
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"{'='*80}\n")
        
        return response
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"ERROR DURING EXECUTION: {str(e)}")
        print(f"{'='*80}\n")
        return f"Error: {str(e)}"

def main():
    test_agent_with_question(
        "Review the chess position provided in the image. It is black's turn. Provide the correct next move for black which guarantees a win. Please provide your response in algebraic notation.",
        "cca530fc-4052-43b2-b130-b30968d8aa44")
#     question = """Examine the video at https://www.youtube.com/watch?v=1htKBjuUWec.
#
# What does Teal'c say in response to the question ""Isn't that hot?"""
#     test_agent_with_question(question, "9d191bce-651d-4746-be2d-7ef8ecadb9c2")


if __name__ == "__main__":
    main()