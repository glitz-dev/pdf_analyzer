from transformers import pipeline

def summarize_text(text, max_length=150, min_length=50):
    """Generate a summary of the text using a transformer model."""
    try:
        # Use lighter T5 model for faster summarization
        summarizer = pipeline("summarization", model="t5-small")
        # Split text into smaller chunks for speed
        chunk_size = 500  # Reduced for faster processing
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        summaries = []
        for chunk in chunks[:2]:  # Limit to 2 chunks for speed
            summary = summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=False)
            summaries.append(summary[0]['summary_text'])
        result = ' '.join(summaries)
        print(f"Generated summary: {result}")
        return result, "Summarization completed"
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return "Summary could not be generated.", f"Error: {str(e)}"