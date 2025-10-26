import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import random
from agent import FinanceAgent
from ml_model import TransactionCategorizer

st.set_page_config(page_title="💰 Finance Assistant", page_icon="💰", layout="wide")

if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'df' not in st.session_state:
    st.session_state.df = None
if 'model' not in st.session_state:
    st.session_state.model = None

def load_data():
    try:
        df = pd.read_csv('/data/transactions.csv')
        df['date'] = pd.to_datetime(df['date'])
        return df
    except:
        return None

def save_data(df):
    df.to_csv('/data/transactions.csv', index=False)

def generate_sample():
    merchants = {"Food": ["KAUFLAND", "LIDL", "MEGA IMAGE"], "Transport": ["OMV", "UBER", "BOLT"], "Entertainment": ["NETFLIX", "CINEMA"], "Shopping": ["ZARA", "EMAG"], "Bills": ["VODAFONE", "ORANGE"]}
    prices = {"Food": (10, 200), "Transport": (15, 250), "Entertainment": (20, 150), "Shopping": (50, 1500), "Bills": (30, 150)}
    data = []
    start = datetime.now() - timedelta(days=90)
    for _ in range(150):
        cat = random.choice(list(merchants.keys()))
        data.append({"date": (start + timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%d"), "description": random.choice(merchants[cat]), "amount": round(random.uniform(*prices[cat]), 2), "category": cat})
    return pd.DataFrame(data).sort_values('date')

with st.sidebar:
    st.title("⚙️ Config")
    
    if st.button("🎲 Date Test", use_container_width=True):
        df = generate_sample()
        save_data(df)
        st.session_state.df = load_data()
        st.success("✅ Date generate!")
        st.rerun()
    
    uploaded = st.file_uploader("CSV", type=['csv'])
    if uploaded:
        df = pd.read_csv(uploaded)
        save_data(df)
        st.session_state.df = load_data()
        st.success("✅ Încărcat!")
        st.rerun()
    
    if st.session_state.df is None:
        st.session_state.df = load_data()
    
    if st.session_state.df is not None:
        st.metric("📊 Tranzacții", len(st.session_state.df))
        st.metric("💰 Total", f"{st.session_state.df['amount'].sum():.0f} RON")
    
    st.divider()
    st.subheader("🤖 ML Model")
    
    if st.button("🎓 Antrenează", use_container_width=True):
        if st.session_state.df is not None:
            with st.spinner("Antrenez..."):
                model = TransactionCategorizer(n_categories=5)
                result = model.train(st.session_state.df)
                if result["success"]:
                    model.save('/data/model.pkl')
                    st.session_state.model = model
                    st.success(f"✅ {result['message']}")
                else:
                    st.error(result["message"])
    
    if st.button("📂 Încarcă Model", use_container_width=True):
        try:
            st.session_state.model = TransactionCategorizer.load('/data/model.pkl')
            st.success("✅ Model încărcat!")
        except:
            st.error("Model inexistent!")
    
    st.divider()
    
    if st.button("🚀 Start Agent", use_container_width=True):
        try:
            st.session_state.agent = FinanceAgent()
            st.success("✅ Agent ready!")
        except ValueError as e:
            st.error(str(e))
    
    if st.button("🔄 Reset Chat", use_container_width=True):
        st.session_state.messages = []
        if st.session_state.agent:
            st.session_state.agent.reset()
        st.rerun()

tab1, tab2 = st.tabs(["💬 Chat", "📊 Analytics"])

with tab1:
    st.title("💰 Personal Finance Assistant")
    
    if st.session_state.agent is None:
        st.info("👈 Inițializează agent-ul!")
    else:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        if prompt := st.chat_input("Ex: Cât am cheltuit pe mâncare?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("..."):
                    try:
                        response = st.session_state.agent.chat(prompt)
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    except Exception as e:
                        st.error(f"Eroare: {e}")

with tab2:
    st.title("📊 Analytics")
    
    if st.session_state.df is not None:
        df = st.session_state.df
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Total", f"{df['amount'].sum():.0f} RON")
        with col2:
            st.metric("📊 Nr", len(df))
        with col3:
            st.metric("📈 Medie", f"{df['amount'].mean():.0f} RON")
        with col4:
            st.metric("💸 Max", f"{df['amount'].max():.0f} RON")
        
        cat_totals = df.groupby('category')['amount'].sum().reset_index()
        fig = px.pie(cat_totals, values='amount', names='category', title='Categorii', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df.sort_values('date', ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("📁 Încarcă date!")

st.markdown("---")
st.markdown("<div style='text-align: center'>💰 Finance Assistant | AI Days 2025</div>", unsafe_allow_html=True)
