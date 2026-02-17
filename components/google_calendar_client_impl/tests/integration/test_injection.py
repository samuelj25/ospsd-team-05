import calendar_client_api

def test_dependency_injection_works():
    """
    Verify that importing the implementation package automatically 
    registers it with the API.
    """
    # 1. Import the implementation package (this triggers the register() call)
    import google_calendar_client_impl

    # 2. Ask the API for a client
    client = calendar_client_api.get_client()

    # 3. Verify we got the Google version, not a generic one
    assert type(client).__name__ == "GoogleCalendarClient"