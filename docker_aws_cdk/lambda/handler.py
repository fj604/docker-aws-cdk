import os
import json

def handler(event, context):
    logout_url = os.getenv('LOGOUT_URL')
    if not logout_url:
        raise Exception('LOGOUT_URL environment variable is not set')
    
    print(f"Received event: {json.dumps(event, indent=2)}")
    print(f"Clearing ALB cookies and redirecting to logout URL {logout_url}")
    
    return {
        'isBase64Encoded': False,
        'statusCode': 302,
        'multiValueHeaders': {
            'Set-Cookie': [
                'AWSELBAuthSessionCookie=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=-1',
                'AWSELBAuthSessionCookie-0=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=-1',
                'AWSELBAuthSessionCookie-1=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=-1',
                'AWSELBAuthSessionCookie-2=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=-1',
                'AWSELBAuthSessionCookie-3=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=-1'
            ],
            'Location': [logout_url]
        }
    }
