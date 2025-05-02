import requests

def get_access_token(tenant_id, client_id, client_secret, scope):
    """
    Get an OAuth access token from Microsoft identity platform
    
    Args:
        tenant_id (str): Your Azure AD tenant ID or name
        client_id (str): Your application (client) ID
        client_secret (str): Your client secret
        scope (str): The scope(s) you're requesting access to
    
    Returns:
        dict: The JSON response containing the access token if successful
    """
    
    # Endpoint URL with your tenant ID
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    # Request body
    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': scope
    }
    
    # Make the POST request
    response = requests.post(token_url, data=payload)
    
    # Check if the request was successful
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

# Example usage
if __name__ == "__main__":
    # Replace these with your actual values
    tenant_id = "your-tenant-id"  # e.g., "contoso.onmicrosoft.com" or GUID
    client_id = "your-client-id"   # Application (client) ID from Azure portal
    client_secret = "your-client-secret"  # Client secret from Azure portal
    scope = "https://ads.microsoft.com/msads.manage"  # Example scope for Microsoft Graph
    
    token_response = get_access_token(tenant_id, client_id, client_secret, scope)
    
    if token_response:
        print("Access token obtained successfully!")
        print(f"Token type: {token_response.get('token_type')}")
        print(f"Expires in: {token_response.get('expires_in')} seconds")
        
        # The actual access token (only printing first 15 chars for security)
        token = token_response.get('access_token')
        if token:
            print(f"Access token: {token[:15]}...")
