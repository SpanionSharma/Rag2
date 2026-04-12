def mock_lead_capture(name: str, email: str, platform: str):
    """
    Mock function to capture lead details.
    
    Args:
        name (str): The user's name.
        email (str): The user's email address.
        platform (str): The user's creator platform (YouTube, Instagram, etc.).
    """
    print(f"\n[API CALL] Lead captured successfully: {name}, {email}, {platform}")
    return f"Lead captured for {name} ({email}) on {platform}."
