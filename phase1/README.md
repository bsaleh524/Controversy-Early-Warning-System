Phase 1: Single Scandel streamlit test app (The MVP)

Goal: Prove the core "Scandal-O-Meter" logic works on one past, known event. This is the entire deliverable for your initial YouTube video.

Goal: Prove the core "Scandal-O-Meter" logic works on one past, known event. This is the entire deliverable for your initial YouTube video.

    Data (The "One-Time" Scrape):

        DON'T build a 24/7 pipeline.

        Pick 1 creator (Hasan) and 1 scandal (shock collar).

        Use a tool (like a YouTube comment scraper) to manually download all comments from the 2 weeks around that event.

        Storage: Save it as a simple CSV file (timestamp, comment_text, likes).

    Model (The "Simple" Way):

        DON'T fine-tune a model yet.

        Write a Python script that loops through your CSV. For each comment, use the OpenAI API (or Claude) with a simple prompt: Classify the sentiment of this comment as 'Positive', 'Negative', or 'Neutral', and extract the main topic if 'Negative'. Return JSON.

    Application (The "Chart"):

        DON'T build a website.

        Take your new CSV (now with sentiment and topic).

        Use Streamlit (a perfect tool to learn) or even just matplotlib to plot two charts:

            Negative Comment Volume (per hour).

            Top Negative Topics (per day).

    Deliverable: A single Streamlit page or a .png chart that proves your system would have detected a spike in "Negative" sentiment and the topic "shock collar" 48 hours before it hit the news. This is your entire project.

1. Scrape comments from r/livestreamfails during week of controversy, as it relates to Hasan.
