Phase 3: The "GenAI System" (The Agent)

Goal: Make the system "smart" and proactive using agentic design.

    Introduce LangChain: Refactor your FastAPI backend. Instead of a simple endpoint, it now runs a LangChain Agent.

    Tools & Memory:

        Give the agent your fine-tuned model as a Tool (classify_sentiment).

        Give it your VectorDB (pgvector) as another Tool (find_similar_scandals).

        Give it a Redis database (another great tool to learn) for Memory (check_alert_history).

    The "Smart" Logic:

        Your agent now runs this logic:

            "New comments detected."

            "Use classify_sentiment tool." -> Result: 150 Negative comments, topic: 'new sponsor'.

            "Use check_alert_history tool." -> Result: No recent alerts for 'new sponsor'.

            "Use find_similar_scandals tool." -> Result: This is 85% similar to the 2024 'Sponsor-pocalypse' event.

            "DECISION: This is a novel and high-risk event. Send alert to user."

    Deliverable: A system that doesn't just show a dashboard, but can actively send you a Discord or email alert with a summary of the new, brewing scandal.