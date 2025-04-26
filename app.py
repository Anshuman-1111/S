import streamlit as st
import openai
import requests
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="AI Shopping Chat", page_icon="🛒")
st.title("🛒 AI Shopping Chat Assistant")

# --- API KEYS ---
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else st.text_input("Enter your OpenAI API Key", type="password")
SERPAPI_KEY = st.secrets["SERPAPI_KEY"] if "SERPAPI_KEY" in st.secrets else st.text_input("Enter your SerpAPI Key", type="password")

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": "You are a helpful AI shopping assistant. For any shopping query, answer conversationally and also show 3 relevant products from Flipkart and Amazon with their links, prices, and short descriptions."}
    ]

# --- FUNCTIONS ---
def search_products(query):
    """Search Flipkart and Amazon for products using SerpAPI."""
    results = []
    for site in ["flipkart.com", "amazon.in"]:
        params = {
            "engine": "google",
            "q": f"site:{site} {query}",
            "api_key": SERPAPI_KEY,
            "num": 3
        }
        resp = requests.get("https://serpapi.com/search", params=params)
        data = resp.json()
        if "organic_results" in data:
            for item in data["organic_results"][:3]:
                results.append({
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet"),
                    "source": site,
                })
    return results

def get_ai_response(user_query, product_summaries):
    """Get AI response from OpenAI, referencing product summaries."""
    prompt = (
        "User asked: " + user_query + "\n"
        "Here are some relevant products from Flipkart and Amazon:\n"
    )
    for prod in product_summaries:
        prompt += f"- {prod['title']} ({prod['source']}): {prod['snippet']} [Link]({prod['link']})\n"
    prompt += "\nAnswer the user's query conversationally, and mention the above products if relevant."

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": st.session_state["messages"][0]["content"]},
            {"role": "user", "content": prompt}
        ],
        max_tokens=400,
        temperature=0.7,
    )
    return response.choices[0].message.content

# --- MAIN CHAT INTERFACE ---
st.markdown("Ask me anything about shopping! (e.g., 'Best phones under 20000', 'Good running shoes', etc.)")

if OPENAI_API_KEY and SERPAPI_KEY:
    openai.api_key = OPENAI_API_KEY

    user_input = st.text_input("You:", key="user_input")
    if st.button("Send") and user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})

        # Search for products
        with st.spinner("Searching for products..."):
            products = search_products(user_input)

        # Get AI response
        with st.spinner("Getting AI response..."):
            ai_response = get_ai_response(user_input, products)
            st.session_state["messages"].append({"role": "assistant", "content": ai_response})

        # Display chat
        for msg in st.session_state["messages"][1:]:
            if msg["role"] == "user":
                st.markdown(f"**You:** {msg['content']}")
            else:
                st.markdown(f"**AI:** {msg['content']}")

        # Show product cards
        st.markdown("### 🔎 Top Products")
        for prod in products:
            st.markdown(f"**[{prod['title']}]({prod['link']})**  \n_{prod['source']}_  \n{prod['snippet']}\n---")
else:
    st.warning("Please enter your OpenAI and SerpAPI keys to start.")

st.markdown("---\nMade with ❤️ using Streamlit, OpenAI, and SerpAPI.")
