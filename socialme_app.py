#!/usr/bin/env python3
"""
socialme_app.py - Main Flask application for SocialMe MVP.
Implements segmented, ensemble-based article generation with iterative expansion.
"""

import os
import requests
from flask import Flask, request, render_template, redirect, url_for, jsonify, session

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yoursecret'

# In-memory storage for sources
SOURCES = []

# Guiding questions (for onboarding and conversation)
QUESTIONS = [
    "What is the main topic of your article?",
    "Who is your target audience?",
    "What tone do you want for your article?",
    "What key points should be included?",
    "Any specific style preferences?",
    "How long should the article be?",
    "Any additional information you'd like to add?"
]

def call_claude_api(prompt):
    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        return "Error: API key not set."
    url = "https://api.anthropic.com/v1/complete"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    payload = {
        "model": "claude-2.1",
        "prompt": prompt,
        "max_tokens_to_sample": 8000,
        "temperature": 0.7,
        "stop_sequences": ["\\n\\nHuman:"],
        "stream": False
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data.get("completion", "No completion text found.")
    except Exception as e:
        return f"Error calling Claude API: {e}"

def build_prompt_segment(segment_type, topic, onboarding):
    base = "\n\nHuman: You are an AI writing assistant specialized in producing top-tier Substack articles. "
    if segment_type == "intro":
        prompt = base + f"Write an engaging introduction about {topic} that hooks the reader, sets the tone, and outlines the article. "
    elif segment_type == "body":
        prompt = base + f"Write the main body of an article about {topic} that is detailed, includes examples, data, and actionable insights. "
        prompt += "Ensure the tone is funny, professional, and a bit controversial (ask questions and challenge assumptions). "
    elif segment_type == "conclusion":
        prompt = base + f"Write a conclusion for an article about {topic} that summarizes key points, provides a clear call-to-action, and ends with the exact phrase 'final draft'. "
    else:
        prompt = base + f"Write an article about {topic}."
    if onboarding:
        prompt += f" User's sources: {onboarding.get('sources', '')}. "
        prompt += f"Writing sample: {onboarding.get('writing_sample', '')}. "
        prompt += f"Frequency/Topics: {onboarding.get('freq_topics', '')}."
    return prompt

def ensemble_generate(prompt, target_words):
    # Generate two candidate outputs and choose the one with word count closest to target_words.
    candidate1 = call_claude_api(prompt)
    candidate2 = call_claude_api(prompt)
    count1 = len(candidate1.split())
    count2 = len(candidate2.split())
    diff1 = abs(count1 - target_words)
    diff2 = abs(count2 - target_words)
    if diff1 <= diff2:
        chosen = candidate1
        chosen_count = count1
    else:
        chosen = candidate2
        chosen_count = count2
    return chosen, chosen_count

def generate_segment(segment_type, topic, onboarding, target_word_count, max_iterations=3):
    iteration = 0
    prompt = build_prompt_segment(segment_type, topic, onboarding)
    candidate, wc = ensemble_generate(prompt, target_word_count)
    while wc < target_word_count and iteration < max_iterations:
        revision_prompt = prompt + f"\n\nPlease expand this {segment_type} to reach approximately {target_word_count} words while retaining the same detail and tone.\n\nAssistant:"
        print(f"Revision prompt for {segment_type} (iteration {iteration+1}):")
        print(revision_prompt)
        candidate = call_claude_api(revision_prompt)
        wc = len(candidate.split())
        print(f"{segment_type.capitalize()} word count after iteration {iteration+1}: {wc}")
        iteration += 1
    return candidate, wc

@app.before_request
def init_conversation():
    if 'conversation' not in session:
        session['conversation'] = {'step': 0, 'answers': []}

@app.route('/')
def home():
    session['conversation'] = {'step': 0, 'answers': []}
    initial_msg = "Welcome! " + QUESTIONS[0]
    return render_template('socialme_index.html', sources=SOURCES, initial_agent=initial_msg)

@app.route('/generate_article', methods=['POST'])
def generate_article():
    data = request.get_json()
    topic = data.get('topic', '')
    onboarding = session.get('onboarding', {})
    
    # Define target word counts for segments
    target_intro = 600
    target_body = 2800
    target_conclusion = 600
    
    print("Generating introduction...")
    intro, intro_wc = generate_segment("intro", topic, onboarding, target_intro)
    
    print("Generating body...")
    body, body_wc = generate_segment("body", topic, onboarding, target_body)
    
    print("Generating conclusion...")
    conclusion, conclusion_wc = generate_segment("conclusion", topic, onboarding, target_conclusion)
    
    article = intro + "\n\n" + body + "\n\n" + conclusion
    total_wc = len(article.split())
    print("Total article word count:", total_wc)
    
    # If total word count is outside range, issue a final revision prompt for overall article.
    if total_wc < 3500 or total_wc > 4500:
        revision_prompt = (
            "\n\nHuman: The combined article is " + str(total_wc) +
            " words, which is outside the desired range of 3500 to 4500 words. "
            "Please generate a revised article of approximately 4000 words while retaining all content, detail, and style."
            "\n\nAssistant:"
        )
        print("Final revision prompt:")
        print(revision_prompt)
        article = call_claude_api(revision_prompt)
        total_wc = len(article.split())
        print("Revised overall article word count:", total_wc)
    
    # Format the article for HTML output
    paragraphs = article.strip().split("\n\n")
    formatted_article = "".join(f"<p>{p}</p>" for p in paragraphs if p.strip())
    return jsonify({"article": formatted_article})

@app.route('/store_onboarding', methods=['POST'])
def store_onboarding():
    sources = request.form.get('sources', '')
    writing_sample = request.form.get('writing_sample', '')
    freq_topics = request.form.get('freq_topics', '')
    session['onboarding'] = {
        'sources': sources,
        'writing_sample': writing_sample,
        'freq_topics': freq_topics
    }
    print("Stored onboarding data:", session['onboarding'])
    return redirect(url_for('home', _external=True))

@app.route('/add_source', methods=['POST'])
def add_source():
    link = request.form.get('link')
    if link:
        SOURCES.append(link)
    return redirect(url_for('home'))

@app.route('/upload_source', methods=['POST'])
def upload_source():
    uploaded_file = request.files.get('file')
    if uploaded_file and uploaded_file.filename:
        SOURCES.append(uploaded_file.filename)
    return redirect(url_for('home'))

@app.route('/reset', methods=['GET'])
def reset():
    session.pop('conversation', None)
    return redirect(url_for('home'))

@app.route('/onboarding')
def onboarding():
    return render_template('socialme_onboarding.html')

@app.route('/diagnose_generate', methods=['POST'])
def diagnose_generate():
    data = request.get_json()
    topic = data.get('topic', '')
    onboarding = session.get('onboarding', {})
    prompt = build_prompt_segment("intro", topic, onboarding)
    raw_response = call_claude_api(prompt)
    return jsonify({"prompt": prompt, "raw_response": raw_response})

if __name__ == '__main__':
    print("Starting SocialMe app on port 5001...")
    app.run(debug=True, host='0.0.0.0', port=5001)
