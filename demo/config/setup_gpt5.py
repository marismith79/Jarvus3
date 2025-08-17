#!/usr/bin/env python3
"""
Setup script for GPT-5 API configuration.
This script helps users set up their GPT-5 API key and test the connection.
"""

import os
import sys
import asyncio
import aiohttp
from getpass import getpass

def check_api_key():
    """Check if GPT-5 API key is already set"""
    api_key = os.getenv('GPT5_API_KEY')
    if api_key and api_key != 'demo_key':
        print("✅ GPT-5 API key is already configured")
        return api_key
    else:
        print("❌ GPT-5 API key not found or using demo key")
        return None

def get_api_key_from_user():
    """Get API key from user input"""
    print("\n🔑 GPT-5 API Key Setup")
    print("=" * 40)
    print("To use the enhanced insurance analysis with real GPT-5 search mode,")
    print("you need to provide your GPT-5 API key.")
    print()
    print("You can get your API key from:")
    print("https://platform.openai.com/api-keys")
    print()
    
    api_key = getpass("Enter your GPT-5 API key (input will be hidden): ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return None
    
    return api_key

def test_api_connection(api_key):
    """Test the GPT-5 API connection"""
    print("\n🧪 Testing GPT-5 API Connection")
    print("=" * 40)
    
    async def test_connection():
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Simple test payload
        payload = {
            "model": "gpt-5o",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello, this is a test message. Please respond with 'API connection successful' if you can read this."
                }
            ],
            "max_tokens": 50,
            "temperature": 0.1
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                        print(f"✅ API connection successful!")
                        print(f"   Response: {content}")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ API connection failed with status {response.status}")
                        print(f"   Error: {error_text}")
                        return False
                        
        except Exception as e:
            print(f"❌ API connection failed: {e}")
            return False
    
    return asyncio.run(test_connection())

def save_api_key_to_env_file(api_key):
    """Save API key to .env file"""
    env_file = ".env"
    
    try:
        # Read existing .env file if it exists
        env_content = ""
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                env_content = f.read()
        
        # Check if GPT5_API_KEY already exists
        if "GPT5_API_KEY" in env_content:
            # Replace existing key
            lines = env_content.split('\n')
            new_lines = []
            for line in lines:
                if line.startswith("GPT5_API_KEY="):
                    new_lines.append(f"GPT5_API_KEY={api_key}")
                else:
                    new_lines.append(line)
            env_content = '\n'.join(new_lines)
        else:
            # Add new key
            if env_content and not env_content.endswith('\n'):
                env_content += '\n'
            env_content += f"GPT5_API_KEY={api_key}\n"
        
        # Write to .env file
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✅ API key saved to {env_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving API key to {env_file}: {e}")
        return False

def set_environment_variable(api_key):
    """Set environment variable for current session"""
    os.environ['GPT5_API_KEY'] = api_key
    print("✅ API key set for current session")

def test_enhanced_insurance_analysis():
    """Test the enhanced insurance analysis with the API key"""
    print("\n🧪 Testing Enhanced Insurance Analysis")
    print("=" * 40)
    
    try:
        from demo.insurance_analysis import enhanced_insurance_analyzer
        
        async def run_test():
            # Simple test case
            result = await enhanced_insurance_analyzer.analyze_insurance_coverage_and_requirements(
                cpt_code="81162",
                insurance_provider="Original Medicare",
                service_type="genetic testing",
                patient_context={
                    "has_genetic_counseling": True,
                    "has_family_history": True
                }
            )
            
            print(f"✅ Enhanced insurance analysis test successful!")
            print(f"   Coverage Status: {result.coverage_status}")
            print(f"   Confidence Score: {result.confidence_score:.2f}")
            print(f"   Requirements Found: {len(result.requirements)}")
            print(f"   Search Sources: {len(result.search_sources)}")
            
            return True
            
        return asyncio.run(run_test())
        
    except Exception as e:
        print(f"❌ Enhanced insurance analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main setup function"""
    print("🚀 GPT-5 Enhanced Insurance Analysis Setup")
    print("=" * 50)
    
    # Check if API key is already set
    existing_key = check_api_key()
    
    if existing_key:
        print(f"   Using existing API key: {existing_key[:8]}...")
        api_key = existing_key
    else:
        # Get API key from user
        api_key = get_api_key_from_user()
        if not api_key:
            print("\n❌ Setup cancelled. No API key provided.")
            print("   The system will use fallback methods without GPT-5 functionality.")
            return False
    
    # Test API connection
    if not test_api_connection(api_key):
        print("\n❌ API connection test failed.")
        print("   Please check your API key and try again.")
        return False
    
    # Save API key to .env file
    if save_api_key_to_env_file(api_key):
        print("   API key will be automatically loaded in future sessions")
    
    # Set for current session
    set_environment_variable(api_key)
    
    # Test enhanced insurance analysis
    if test_enhanced_insurance_analysis():
        print("\n🎉 Setup completed successfully!")
        print("   The enhanced insurance analysis is now ready to use with real GPT-5 search mode.")
    else:
        print("\n⚠️  Setup completed with warnings.")
        print("   API key is configured, but enhanced analysis test failed.")
        print("   The system will use fallback methods.")
    
    print("\n📝 Next Steps:")
    print("   1. Run the test script: python test_enhanced_insurance.py")
    print("   2. Start the application: python app.py")
    print("   3. Use the enhanced insurance analysis in your workflow")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
