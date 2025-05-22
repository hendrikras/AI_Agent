def reverse_word(word):
    """Reverse the characters in a word or text."""
    if not word or not isinstance(word, str):
        return "Please provide a valid text string to reverse."

    reversed_word = word[::-1]
    return f"The reversed text is: {reversed_word}"