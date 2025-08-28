import json
from typing import Dict, Any
from ..state import AgentState
from ..prompts.final_synthesis_prompt import get_final_synthesis_prompt
from ..llm_client import get_llm_client

def format_database_results(observations: list) -> str:
    """
    Format database results into beautiful tables for better visualization
    """
    formatted_results = []
    
    for obs in observations:
        if not obs.data or not isinstance(obs.data, dict):
            continue
            
        # PostgreSQL: Handle list_tables results
        if obs.tool == "sql.list_tables" and "tables" in obs.data:
            tables = obs.data.get("tables", [])
            if tables:
                formatted_results.append("## 📋 Danh sách các bảng trong PostgreSQL")
                formatted_results.append("")
                formatted_results.append("| Schema | Tên bảng |")
                formatted_results.append("|--------|----------|")
                for table in tables:
                    schema = table.get("schema", "public")
                    table_name = table.get("table", "")
                    formatted_results.append(f"| {schema} | {table_name} |")
                formatted_results.append("")
                formatted_results.append(f"**Tổng cộng:** {len(tables)} bảng")
                formatted_results.append("")
        
        # PostgreSQL: Handle custom_query results
        elif obs.tool == "sql.custom_query" and "rows" in obs.data:
            rows = obs.data.get("rows", [])
            if rows:
                formatted_results.append("## 📊 Kết quả truy vấn PostgreSQL")
                formatted_results.append("")
                
                # Get column names from first row
                if rows:
                    columns = list(rows[0].keys())
                    formatted_results.append("| " + " | ".join(columns) + " |")
                    formatted_results.append("|" + "|".join(["---"] * len(columns)) + "|")
                    
                    for row in rows:
                        row_values = [str(row.get(col, "")) for col in columns]
                        formatted_results.append("| " + " | ".join(row_values) + " |")
                    
                    formatted_results.append("")
                    formatted_results.append(f"**Tổng số dòng:** {len(rows)}")
                    formatted_results.append("")
        
        # PostgreSQL: Handle describe_table results
        elif obs.tool == "sql.describe_table" and "rows" in obs.data:
            rows = obs.data.get("rows", [])
            if rows:
                formatted_results.append("## 🏗️ Cấu trúc bảng PostgreSQL")
                formatted_results.append("")
                formatted_results.append("| Tên cột | Kiểu dữ liệu | Nullable |")
                formatted_results.append("|----------|--------------|----------|")
                for row in rows:
                    col_name = row.get("column_name", "")
                    data_type = row.get("data_type", "")
                    nullable = row.get("is_nullable", "")
                    formatted_results.append(f"| {col_name} | {data_type} | {nullable} |")
                formatted_results.append("")
        
        # Milvus: Handle list_collections results
        elif obs.tool == "milvus.list_collections" and "collections" in obs.data:
            collections = obs.data.get("collections", [])
            if collections:
                formatted_results.append("## 🗂️ Danh sách các collection trong Milvus")
                formatted_results.append("")
                formatted_results.append("| Tên Collection | Số lượng Vector | Index Type |")
                formatted_results.append("|----------------|-----------------|------------|")
                for collection in collections:
                    # Handle both dict and string collection names
                    if isinstance(collection, dict):
                        name = collection.get("name", "")
                        vector_count = collection.get("vector_count", "N/A")
                        index_type = collection.get("index_type", "N/A")
                    else:
                        name = str(collection)
                        vector_count = "N/A"
                        index_type = "N/A"
                    formatted_results.append(f"| {name} | {vector_count} | {index_type} |")
                formatted_results.append("")
                formatted_results.append(f"**Tổng cộng:** {len(collections)} collection")
                formatted_results.append("")
        
        # Milvus: Handle describe_index results
        elif obs.tool == "milvus.describe_index" and "index_info" in obs.data:
            index_info = obs.data.get("index_info", {})
            if index_info:
                formatted_results.append("## 🔍 Thông tin Index Milvus")
                formatted_results.append("")
                formatted_results.append("| Thuộc tính | Giá trị |")
                formatted_results.append("|-------------|---------|")
                for key, value in index_info.items():
                    formatted_results.append(f"| {key} | {value} |")
                formatted_results.append("")
        
        # Neo4j: Handle kg.query results
        elif obs.tool == "kg.query" and "results" in obs.data:
            results = obs.data.get("results", [])
            if results:
                formatted_results.append("## 🕸️ Kết quả truy vấn Neo4j Graph")
                formatted_results.append("")
                formatted_results.append("| Node/Relationship | Thuộc tính |")
                formatted_results.append("|-------------------|-------------|")
                for result in results:
                    node_type = result.get("type", "Node")
                    properties = result.get("properties", {})
                    props_str = ", ".join([f"{k}: {v}" for k, v in properties.items()])
                    formatted_results.append(f"| {node_type} | {props_str} |")
                formatted_results.append("")
                formatted_results.append(f"**Tổng số kết quả:** {len(results)}")
                formatted_results.append("")
    
    return "\n".join(formatted_results)

def synthesize_final_answer(state: AgentState) -> dict:
    print("--- Node: FINAL SYNTHESIS ---")
    
    # If router already provided a final answer, return it directly
    if state.final_answer:
        return {"final_answer": state.final_answer}
    
    # Check if we have the required components for complex synthesis
    if not state.task:
        return {"final_answer": "Error: Task not available for final synthesis."}
    if not state.plan:
        return {"final_answer": "Error: Plan not available for final synthesis."}
    
    # Add memory context if available
    memory_context = ""
    if state.memory_context:
        memory_context = f"\n\n{state.memory_context}"
    
    # Handle acceptance - it might be a string or dict
    acceptance = state.task.acceptance
    if isinstance(acceptance, str):
        acceptance = {"deliverable_format": "markdown", "success_condition": acceptance}
    elif not isinstance(acceptance, dict):
        acceptance = {"deliverable_format": "markdown", "success_condition": str(acceptance)}
    
    plan = state.plan # Assuming state.plan is the final plan object
    observations = state.observations # Assuming state.observations is a list of Observation objects
    format_hints = {} # Placeholder for format hints

    prompt = get_final_synthesis_prompt(acceptance, plan.dict(), [obs.dict() for obs in observations], format_hints)
    
    # Add memory context to prompt if available
    if memory_context:
        prompt += f"\n\n**Memory Context:**{memory_context}"

    # Determine expected output format
    deliverable_format = acceptance.get("deliverable_format", "markdown")

    try:
        response_str = get_llm_client().invoke_chat(prompt)
        
        # Debug: Print response type and content
        print(f"Response type: {type(response_str)}")
        print(f"Response content: {response_str[:200]}...")

        if deliverable_format == "markdown":
            # Check if we have database results to format
            database_formatted = format_database_results(observations)
            if database_formatted:
                # Combine LLM response with formatted database results
                final_answer = response_str + "\n\n" + database_formatted
            else:
                final_answer = response_str
        else: # json or custom
            # Implement retry logic for JSON output
            for attempt in range(3): # Max 3 attempts
                try:
                    final_answer = json.loads(response_str)
                    break # Exit loop if successful
                except json.JSONDecodeError as e:
                    print(f"Final Synthesis JSON output failed (attempt {attempt + 1}): {e}")
                    if attempt < 2: # If not last attempt, try to fix JSON
                        print("Attempting to fix JSON by re-prompting LLM.")
                        # Re-prompt with instruction to fix JSON
                        prompt = f"{response_str}\n\nBạn đã trả JSON sai schema, hãy giữ nguyên nội dung nhưng sửa thành JSON hợp lệ theo schema đã cho. ONLY JSON."
                    else:
                        print("Max retries reached for Final Synthesis JSON. Returning error.")
                        return {"errors": state.errors + [f"Final Synthesis JSON output failed after multiple retries: {e}"]}
            else: # This else block executes if the loop completes without a break
                final_answer = response_str # Fallback if JSON parsing consistently fails

        return {"final_answer": final_answer}

    except Exception as e:
        print(f"An unexpected error occurred during Final Synthesis: {e}")
        return {"errors": state.errors + [f"Unexpected error in Final Synthesis: {e}"]}
