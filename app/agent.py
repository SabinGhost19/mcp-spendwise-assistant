import os
from openai import OpenAI
import json
from typing import List, Dict
from mcp_client import MCPClient

class FinanceAgent:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "sk-your-openai-api-key-here":
            raise ValueError("⚠️  Setează OPENAI_API_KEY în .env!")
        
        self.client = OpenAI(api_key=api_key)
        self.mcp_client = MCPClient()
        self.model = "gpt-4-turbo-preview"
        self.conversation_history = []
        
        self.system_prompt = """Ești un asistent financiar în limba română. Ajuți utilizatorii să înțeleagă cheltuielile lor.

Categorii: Food, Transport, Entertainment, Shopping, Bills, Other

Răspunde natural, folosește emoji-uri, oferă insights. Format: răspuns direct, apoi detalii, apoi sfat.

Exemplu:
"Ai cheltuit 450 RON pe Food 🍔
Din 23 tranzacții, cele mai mari: Kaufland 145 RON, Restaurant 120 RON
💡 Media de 20 RON/zi e OK!"
"""
    
    def _get_tools(self) -> List[Dict]:
        return [
            {"type": "function", "function": {"name": "get_transactions_by_category", "description": "Filtrează după categorie", "parameters": {"type": "object", "properties": {"category": {"type": "string", "enum": ["Food", "Transport", "Entertainment", "Shopping", "Bills", "Other"]}, "start_date": {"type": "string"}, "end_date": {"type": "string"}}, "required": ["category"]}}},
            {"type": "function", "function": {"name": "get_spending_summary", "description": "Totaluri pe categorii", "parameters": {"type": "object", "properties": {"start_date": {"type": "string"}, "end_date": {"type": "string"}}}}},
            {"type": "function", "function": {"name": "get_monthly_trends", "description": "Tendințe lunare", "parameters": {"type": "object", "properties": {"months": {"type": "integer", "default": 6}}}}}
        ]
    
    def chat(self, user_message: str) -> str:
        self.conversation_history.append({"role": "user", "content": user_message})
        messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history
        
        response = self.client.chat.completions.create(model=self.model, messages=messages, tools=self._get_tools(), tool_choice="auto")
        message = response.choices[0].message
        
        if message.tool_calls:
            self.conversation_history.append({"role": "assistant", "content": message.content, "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in message.tool_calls]})
            
            for tc in message.tool_calls:
                result = self.mcp_client.call_tool(tc.function.name, json.loads(tc.function.arguments))
                self.conversation_history.append({"role": "tool", "content": json.dumps(result, ensure_ascii=False), "tool_call_id": tc.id})
            
            final = self.client.chat.completions.create(model=self.model, messages=[{"role": "system", "content": self.system_prompt}] + self.conversation_history)
            final_message = final.choices[0].message.content
        else:
            final_message = message.content
        
        self.conversation_history.append({"role": "assistant", "content": final_message})
        return final_message
    
    def reset(self):
        self.conversation_history = []
