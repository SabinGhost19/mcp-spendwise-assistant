# Implementare directă, fără import din mcp-server
import pandas as pd
from typing import Dict, Any

class MCPServer:
    def __init__(self):
        self.data_path = "/data/transactions.csv"
        self.df = None
        self._load_data()
    
    def _load_data(self):
        try:
            self.df = pd.read_csv(self.data_path)
            self.df['date'] = pd.to_datetime(self.df['date'])
        except:
            self.df = pd.DataFrame(columns=['date', 'description', 'amount', 'category'])
    
    def reload_data(self):
        self._load_data()
    
    def get_transactions_by_category(self, category: str, start_date=None, end_date=None):
        filtered = self.df[self.df['category'] == category].copy()
        if start_date:
            filtered = filtered[filtered['date'] >= pd.to_datetime(start_date)]
        if end_date:
            filtered = filtered[filtered['date'] <= pd.to_datetime(end_date)]
        transactions = filtered.copy()
        transactions['date'] = transactions['date'].astype(str)
        return {"category": category, "count": len(transactions), "total": float(transactions['amount'].sum()), "transactions": transactions.to_dict('records')}
    
    def get_spending_summary(self, start_date=None, end_date=None):
        filtered = self.df.copy()
        if start_date:
            filtered = filtered[filtered['date'] >= pd.to_datetime(start_date)]
        if end_date:
            filtered = filtered[filtered['date'] <= pd.to_datetime(end_date)]
        summary = filtered.groupby('category')['amount'].agg(['sum', 'count']).reset_index()
        summary.columns = ['category', 'total', 'count']
        return {"total": float(filtered['amount'].sum()), "by_category": summary.to_dict('records')}
    
    def get_monthly_trends(self, months=6):
        df = self.df.copy()
        df['month'] = df['date'].dt.to_period('M').astype(str)
        monthly = df.groupby(['month', 'category'])['amount'].sum().reset_index()
        return {"trends": monthly.to_dict('records')}

mcp_server = MCPServer()

class MCPClient:
    def __init__(self):
        self.server = mcp_server
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.server.reload_data()
            if tool_name == "get_transactions_by_category":
                return self.server.get_transactions_by_category(**arguments)
            elif tool_name == "get_spending_summary":
                return self.server.get_spending_summary(**arguments)
            elif tool_name == "get_monthly_trends":
                return self.server.get_monthly_trends(**arguments)
            return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}