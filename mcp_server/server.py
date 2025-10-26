import pandas as pd
from typing import Dict, Any, Optional

class TransactionMCPServer:
    def __init__(self, data_path: str = "/data/transactions.csv"):
        self.data_path = data_path
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
    
    def get_transactions_by_category(self, category: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        filtered = self.df[self.df['category'] == category].copy()
        if start_date:
            filtered = filtered[filtered['date'] >= pd.to_datetime(start_date)]
        if end_date:
            filtered = filtered[filtered['date'] <= pd.to_datetime(end_date)]
        return {"category": category, "count": len(filtered), "total": float(filtered['amount'].sum()), "transactions": filtered.to_dict('records')}
    
    def get_spending_summary(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        filtered = self.df.copy()
        if start_date:
            filtered = filtered[filtered['date'] >= pd.to_datetime(start_date)]
        if end_date:
            filtered = filtered[filtered['date'] <= pd.to_datetime(end_date)]
        summary = filtered.groupby('category')['amount'].agg(['sum', 'count']).reset_index()
        summary.columns = ['category', 'total', 'count']
        return {"total": float(filtered['amount'].sum()), "by_category": summary.to_dict('records')}
    
    def get_monthly_trends(self, months: int = 6) -> Dict[str, Any]:
        df = self.df.copy()
        df['month'] = df['date'].dt.to_period('M').astype(str)
        monthly = df.groupby(['month', 'category'])['amount'].sum().reset_index()
        return {"trends": monthly.to_dict('records')}

mcp_server = TransactionMCPServer()
