# 🍜 Mukbang Virality Analysis  
*A delicious dive into why food videos go viral on YouTube*

Ever wondered why some mukbang videos get millions of views while others get ignored? Is it the spicy noodles? The ASMR slurping? The soothing voiceover? 😮‍💨 In this project, I explore the world of mukbang content and use data science to uncover what makes these eating videos irresistible.

---

## 🔍 Project Goals

- Scrape mukbang video metadata from YouTube using `yt-dlp`
- Analyze features like **duration**, **views**, **likes**, **comment count**, and more
- Use **zero-shot learning** and NLP to auto-classify:
  - 🎙️ Talking vs. ASMR
  - 🥢 Cuisine type (e.g., Korean, seafood, Western)
- Investigate **upload timing**, **content format**, and **engagement patterns**
- Make the whole thing cute, fun, and insightful ✨

---

## 🗂️ Folder Structure
Mukbang Analysis/
├── data/ ← Cleaned mukbang dataset
├── notebooks/ ← Jupyter notebooks for EDA & modeling
├── output/ ← Visualizations & summaries
├── mukbang_scraper.py ← Python script to scrape YouTube videos
└── README.md ← You're here!


---

## 🧪 Tools & Libraries

| Task | Stack |
|------|-------|
| Web scraping | `yt-dlp` |
| Data cleaning & EDA | `pandas`, `matplotlib`, `seaborn` |
| NLP & classification | `transformers`, `sklearn`, `zero-shot` |
| Notebook environment | Jupyter via Anaconda |
| ML coming soon | XGBoost or DistilBERT |

---

## 📊 Sample Insights (so far)

- ASMR-tagged videos tend to have higher **likes-per-minute** 📈
- Videos uploaded on **weekends** spike in engagement
- Certain cuisines (like spicy noodles 🌶️) cluster into their own engagement patterns

> _Note: This is based on a pilot dataset of 20 videos. Scaling up next!_

---

## 🌱 What’s Next

- [ ] Expand to 200+ mukbang videos with varied cuisine types
- [ ] Train a classifier to predict video virality
- [ ] Build a dashboard for mukbang analytics (maybe Streamlit?)
- [ ] Add visual heatmaps and ASMR audio feature analysis 🎧
- [ ] Publish a blog post or Medium story on findings!

---

## 🧠 Why This Project Matters

This isn’t just about food — it’s about:
- 🧵 Content virality
- 🎯 Human behavior online
- 🛠️ Applying machine learning in creative and social spaces

Whether you're into YouTube culture or curious about how data meets pop food trends, this project is a tasty example of data science in the wild.

---

## 💌 Let’s Connect!

If you want to nerd out about mukbangs, data science, or internet culture, feel free to reach out:

- 📬 [your-email@example.com]
- 🧠 [LinkedIn or portfolio link]

Thanks for stopping by 🍥💖

---