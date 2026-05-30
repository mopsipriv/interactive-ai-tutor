import asyncio
from agents.graph import app

async def start_test():
    print("Start of testing of LangGraph\n")
    
    #searching for user mops
    test_input = {"student_id": 1}
    
    print("Graph started to work")
    result = await app.ainvoke(test_input)
    print("Graph ended working\n")
    

    print("Answer from langGraph")
    print(result["final_text"])

if __name__ == "__main__":
    asyncio.run(start_test())