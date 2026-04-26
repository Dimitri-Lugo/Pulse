import streamlit as st


# Caches the response for 5 minutes to avoid hitting the API on every rerun
@st.cache_data(ttl=300, show_spinner=False)
def get_diversification_advice(api_key: str, correlation_index: float, top_holdings: tuple) -> str:
    if not api_key:
        return "GROQ_API_KEY not set in .streamlit/secrets.toml."

    # Formats the holdings into a readable string for the prompt
    holdings_str = ", ".join(
        f"{ticker} ({alloc:.1f}%)" for ticker, alloc in top_holdings
    )

    # Builds the prompt — I chose to keep it short and specific so the model stays on topic
    prompt = (
        f"You are a concise portfolio risk advisor.\n\n"
        f"A user's portfolio has a 30-day weighted pairwise correlation index of "
        f"{correlation_index:.2f} (warning threshold: 0.70), indicating elevated "
        f"concentration risk.\n\n"
        f"Top holdings by allocation: {holdings_str}.\n\n"
        f"Provide exactly 2-3 specific, actionable diversification recommendations "
        f"in under 120 words total. Suggest which positions to reduce and which "
        f"asset classes or sectors to add to lower the correlation. "
        f"Be direct and specific. No generic disclaimers."
    )

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        # Returns something readable to the user instead of a raw stack trace
        err = str(e)
        if "429" in err or "rate" in err.lower():
            return "Daily request limit reached. Try again tomorrow or upgrade your Groq plan."
        if "401" in err or "invalid" in err.lower():
            return "Groq API key is invalid. Check GROQ_API_KEY in secrets.toml."
        return f"LLM error — {type(e).__name__}: {e}"
