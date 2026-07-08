from fastmcp import FastMCP
from database.db_connector import get_all_students

mcp = FastMCP("Tutor Server")

@mcp.tool
async def get_students_tool() -> list:
    """Get all students from the database"""
    return await get_all_students()

if __name__=="__main__":
    mcp.run()