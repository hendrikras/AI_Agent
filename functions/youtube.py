from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled

# Create a wrapper function for the YouTube loader with debugging
def youtube_info(url):
    """Extract transcript information from a YouTube video URL."""
    print(f"Processing YouTube URL: {url}")

    try:
        # Extract video ID from different URL formats
        video_id = None
        if "youtube.com/watch?v=" in url:
            video_id = url.split("youtube.com/watch?v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        else:
            return "Please provide a valid YouTube URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID or https://youtu.be/VIDEO_ID)"

        print(f"Extracted video ID: {video_id}")

        # Try to fetch transcript using YouTubeTranscriptApi
        try:
            # First try with default language
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            print(f"Successfully retrieved transcript with {len(transcript)} segments")
        except (NoTranscriptFound, TranscriptsDisabled) as e:
            # If no transcript in default language, try to list available languages
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                available_transcripts = list(transcript_list)
                
                if available_transcripts:
                    # Get the first available transcript
                    first_transcript = transcript_list.find_transcript(available_transcripts[0].language_code)
                    transcript = first_transcript.fetch()
                    print(f"Used alternative language transcript: {first_transcript.language_code}")
                else:
                    return f"No transcripts available for this video (ID: {video_id}). The video might not have captions enabled."
            except Exception as inner_e:
                return f"No transcripts available for this video (ID: {video_id}). Error: {str(inner_e)}"
        
        # Extract the text from the transcript
        transcript_text = " ".join([item['text'] for item in transcript])
        
        # Truncate if too long (over 10000 characters)
        if len(transcript_text) > 10000:
            transcript_text = transcript_text[:10000] + "... [transcript truncated due to length]"
            
        return transcript_text
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error: {str(e)}")
        print(error_trace)
        
        # Provide a more user-friendly error message
        if "no element found" in str(e):
            return f"Could not retrieve transcript for video ID: {video_id}. The video might not have captions or they might be disabled."
        else:
            return f"Error retrieving transcript for video ID: {video_id}. Error: {str(e)}"