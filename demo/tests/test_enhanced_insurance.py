#!/usr/bin/env python3
"""
Test script for enhanced insurance analysis functionality.
This demonstrates the merged step 1 and 2 that combines coverage determination 
and insurance requirements extraction using real GPT-5 search mode.
"""

import asyncio
import json
import os
from demo.insurance_analysis import enhanced_insurance_analyzer

async def test_enhanced_insurance_analysis():
    """Test the enhanced insurance analysis functionality"""
    
    print("🧪 Testing Enhanced Insurance Analysis with Real GPT-5")
    print("=" * 60)
    
    # Check if GPT-5 API key is available
    api_key = os.getenv('GPT5_API_KEY')
    if not api_key or api_key == 'demo_key':
        print("⚠️  Warning: GPT5_API_KEY not set or using demo key")
        print("   The system will use fallback methods for testing")
        print("   Set GPT5_API_KEY environment variable for full functionality")
        print()
    
    # Test cases with different insurance providers and CPT codes
    test_cases = [
        {
            "cpt_code": "81162",
            "insurance_provider": "Original Medicare",
            "service_type": "genetic testing",
            "patient_context": {
                "has_genetic_counseling": True,
                "has_family_history": True,
                "has_clinical_indication": True,
                "provider_credentials_valid": True,
                "patient_state": "CA"  # California - Jurisdiction P
            },
            "patient_address": "123 Main St, Los Angeles, CA"  # Test address extraction
        },
        {
            "cpt_code": "81455",
            "insurance_provider": "Original Medicare",
            "service_type": "genetic testing",
            "patient_context": {
                "has_genetic_counseling": True,
                "has_family_history": True,
                "has_clinical_indication": True,
                "provider_credentials_valid": True,
                "patient_state": "NY"  # New York - Jurisdiction K
            },
            "patient_address": "456 Oak Ave, New York, NY"  # Test address extraction
        },
        {
            "cpt_code": "81479",
            "insurance_provider": "Humana Medicare Advantage",
            "service_type": "genetic testing",
            "patient_context": {
                "has_genetic_counseling": False,
                "has_family_history": True,
                "has_clinical_indication": True,
                "provider_credentials_valid": True,
                "patient_state": "TX"  # Texas - Jurisdiction R
            },
            "patient_address": "789 Pine St, Houston, TX"  # Test address extraction
        },
        {
            "cpt_code": "81292",
            "insurance_provider": "Original Medicare",
            "service_type": "genetic testing",
            "patient_context": {
                "has_genetic_counseling": True,
                "has_family_history": False,
                "has_clinical_indication": True,
                "provider_credentials_valid": True,
                "patient_state": "FL"  # Florida - Jurisdiction L
            },
            "patient_address": "321 Elm St, Miami, FL"  # Test address extraction
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['insurance_provider']} - CPT {test_case['cpt_code']}")
        print("-" * 50)
        
        try:
            print(f"🔍 Searching for medical policy documents...")
            
            # Run the enhanced analysis
            result = await enhanced_insurance_analyzer.analyze_insurance_coverage_and_requirements(
                cpt_code=test_case["cpt_code"],
                insurance_provider=test_case["insurance_provider"],
                service_type=test_case["service_type"],
                patient_context=test_case["patient_context"],
                patient_address=test_case.get("patient_address")
            )
            
            # Display results
            print(f"✅ Coverage Status: {result.coverage_status}")
            print(f"📊 Confidence Score: {result.confidence_score:.2f}")
            print(f"📄 Coverage Details: {result.coverage_details}")
            
            print(f"\n🔍 Search Sources Found: {len(result.search_sources)}")
            for source in result.search_sources[:3]:  # Show top 3 sources
                print(f"  • {source.get('title', 'Unknown')} ({source.get('relevance', 0)}% relevant)")
                print(f"    URL: {source.get('url', 'N/A')}")
            
            print(f"\n📋 Requirements Extracted: {len(result.requirements)}")
            for req in result.requirements:
                print(f"  • {req.requirement_type}")
                print(f"    Evidence: {req.evidence_basis}")
                print(f"    Documentation: {', '.join(req.documentation_needed)}")
                print(f"    Clinical Criteria: {', '.join(req.clinical_criteria)}")
            
            print(f"\n👤 Patient Criteria Match:")
            for criteria, met in result.patient_criteria_match.items():
                status = "✅" if met else "❌"
                print(f"  {status} {criteria}: {'Met' if met else 'Not Met'}")
            
            print(f"\n💡 Recommendations:")
            for rec in result.recommendations:
                print(f"  • {rec}")
            
            # Display MAC jurisdiction information for Medicare cases
            if result.mac_jurisdiction:
                print(f"\n🏛️  MAC Jurisdiction: {result.mac_jurisdiction}")
                print(f"   NCD Applicable: {result.ncd_applicable}")
                print(f"   LCD Applicable: {result.lcd_applicable}")
                
        except Exception as e:
            print(f"❌ Error in test case {i}: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 60)

async def test_mac_jurisdiction_functionality():
    """Test MAC jurisdiction functionality specifically"""
    
    print("\n🏛️ Testing MAC Jurisdiction Functionality")
    print("=" * 50)
    
    # Test different states and their MAC jurisdictions
    test_states = [
        ("CA", "California"),
        ("NY", "New York"),
        ("TX", "Texas"),
        ("FL", "Florida"),
        ("IL", "Illinois"),
        ("PA", "Pennsylvania")
    ]
    
    for state_code, state_name in test_states:
        print(f"\n📍 Testing {state_name} ({state_code})")
        
        try:
            # Get MAC jurisdiction
            mac_jurisdiction = enhanced_insurance_analyzer.get_mac_jurisdiction(state_code)
            
            if mac_jurisdiction:
                print(f"  ✅ MAC Jurisdiction Found:")
                print(f"     Name: {mac_jurisdiction['name']}")
                print(f"     ID: {mac_jurisdiction['jurisdiction_id']}")
                print(f"     Website: {mac_jurisdiction['website']}")
                print(f"     Description: {mac_jurisdiction['description']}")
                print(f"     States: {', '.join(mac_jurisdiction['states'])}")
            else:
                print(f"  ❌ No MAC jurisdiction found for {state_code}")
                
        except Exception as e:
            print(f"  ❌ Error testing {state_code}: {e}")
    
    print("\n" + "=" * 50)

async def test_address_extraction():
    """Test address extraction functionality"""
    
    print("\n🏠 Testing Address Extraction Functionality")
    print("=" * 50)
    
    # Test different address formats
    test_addresses = [
        ("189 Elm St, New York, NY", "NY"),
        ("314 Elm St, New York, NY", "NY"),
        ("981 Elm St, Ann Arbor, MI", "MI"),
        ("765 Elm St, New Haven, CT", "CT"),
        ("553 Elm St, New York, NY", "NY"),
        ("505 Elm St, Ann Arbor, MI", "MI"),
        ("441 Elm St, Ann Arbor, MI", "MI"),
        ("297 Elm St, New Haven, CT", "CT"),
        ("408 Elm St, New Haven, CT", "CT"),
        ("920 Elm St, New Haven, CT", "CT"),
        ("123 Main St, Los Angeles, CA", "CA"),
        ("456 Oak Ave, New York, NY", "NY"),
        ("789 Pine St, Houston, TX", "TX"),
        ("321 Elm St, Miami, FL", "FL"),
        ("", None),  # Empty address
        ("Invalid Address", None),  # Invalid format
        ("123 Main St, Los Angeles, California", "CA"),  # Full state name
        ("456 Oak Ave, New York, New York", "NY"),  # Full state name
    ]
    
    for address, expected_state in test_addresses:
        try:
            extracted_state = enhanced_insurance_analyzer.extract_patient_state_from_address(address)
            status = "✅" if extracted_state == expected_state else "❌"
            print(f"{status} Address: '{address}' -> State: {extracted_state} (Expected: {expected_state})")
        except Exception as e:
            print(f"❌ Error extracting state from '{address}': {e}")
    
    print("\n" + "=" * 50)

async def test_gpt5_search_functionality():
    """Test the GPT-5 search functionality specifically"""
    
    print("\n🔍 Testing GPT-5 Search Functionality")
    print("=" * 50)
    
    # Test different search scenarios
    search_scenarios = [
        ("81162", "Original Medicare", "genetic testing"),
        ("81455", "Original Medicare", "genetic testing"),
        ("81292", "Original Medicare", "genetic testing"),
        ("81479", "Humana Medicare Advantage", "genetic testing")
    ]
    
    for cpt_code, provider, service_type in search_scenarios:
        print(f"\n🔎 Searching for: {provider} - {cpt_code} - {service_type}")
        
        try:
            search_results = await enhanced_insurance_analyzer._search_medical_policies_with_gpt5(
                cpt_code, provider, service_type
            )
            
            print(f"📄 Found {len(search_results)} search results:")
            for i, result in enumerate(search_results[:3], 1):  # Show top 3
                print(f"  {i}. {result.get('title', 'Unknown')}")
                print(f"     URL: {result.get('url', 'N/A')}")
                print(f"     Relevance: {result.get('relevance', 0)}%")
                print(f"     Type: {result.get('type', 'Unknown')}")
                print(f"     Source: {result.get('source', 'Unknown')}")
                print()
                
        except Exception as e:
            print(f"❌ Error in search: {e}")
            import traceback
            traceback.print_exc()

async def test_document_parsing():
    """Test the document parsing functionality"""
    
    print("\n📄 Testing Document Parsing with GPT-5")
    print("=" * 50)
    
    # Mock search results
    mock_search_results = [
        {
            "title": "Medicare Coverage Database - Genetic Testing",
            "url": "https://www.cms.gov/medicare-coverage-database/details/ncd-details.aspx?NCDId=90.2",
            "snippet": "Medicare covers genetic testing when specific criteria are met.",
            "relevance": 95,
            "type": "policy_document",
            "source": "CMS"
        }
    ]
    
    try:
        # Test document extraction
        documents = await enhanced_insurance_analyzer._extract_policy_documents_with_gpt5(mock_search_results)
        
        print(f"📋 Extracted {len(documents)} policy documents:")
        for doc in documents:
            print(f"  • Title: {doc.get('title', 'Unknown')}")
            print(f"    Source: {doc.get('source', 'Unknown')}")
            print(f"    Requirements: {len(doc.get('requirements', []))}")
            print(f"    Clinical Criteria: {len(doc.get('clinical_criteria', []))}")
            print(f"    Coverage Status: {doc.get('coverage_status', 'Unknown')}")
            print()
            
    except Exception as e:
        print(f"❌ Error in document parsing: {e}")
        import traceback
        traceback.print_exc()

async def test_api_integration():
    """Test the API integration functionality"""
    
    print("\n🌐 Testing API Integration")
    print("=" * 50)
    
    try:
        # Test the API endpoint simulation
        from app import app
        import json
        
        # Create a test client
        with app.test_client() as client:
            # Test the analyze-insurance endpoint
            response = client.post('/api/prior-auths/1/analyze-insurance')
            
            if response.status_code == 200:
                data = json.loads(response.data)
                print("✅ API endpoint working correctly")
                print(f"   Analysis completed: {data.get('message', 'Unknown')}")
                print(f"   Coverage status: {data.get('analysis', {}).get('coverage_status', 'Unknown')}")
                print(f"   Requirements found: {len(data.get('analysis', {}).get('requirements', []))}")
            else:
                print(f"❌ API endpoint failed with status {response.status_code}")
                print(f"   Response: {response.data.decode()}")
                
    except Exception as e:
        print(f"❌ Error in API integration test: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function"""
    print("🚀 Enhanced Insurance Analysis Test Suite")
    print("This demonstrates the merged Step 1 & 2 functionality with Real GPT-5")
    print("=" * 70)
    
    # Check environment
    api_key = os.getenv('GPT5_API_KEY')
    if api_key and api_key != 'demo_key':
        print("✅ GPT-5 API key detected - Full functionality available")
    else:
        print("⚠️  GPT-5 API key not detected - Using fallback methods")
        print("   Set GPT5_API_KEY environment variable for full functionality")
    
    print()
    
    # Run all tests
    await test_enhanced_insurance_analysis()
    await test_mac_jurisdiction_functionality()
    await test_address_extraction()
    await test_gpt5_search_functionality()
    await test_document_parsing()
    
    # Only test API integration if we're in the right context
    try:
        await test_api_integration()
    except Exception as e:
        print(f"⚠️  API integration test skipped: {e}")
    
    print("\n✅ All tests completed!")
    print("\n📝 Summary:")
    print("• Combined coverage determination and requirements extraction")
    print("• Real GPT-5 search mode for medical policy documents")
    print("• Patient criteria matching against insurance requirements")
    print("• Automated recommendations based on analysis results")
    print("• Fallback methods when GPT-5 is not available")
    
    print("\n🔧 Next Steps:")
    print("• Set GPT5_API_KEY environment variable for full functionality")
    print("• Test with real insurance provider data")
    print("• Integrate with actual EHR systems")
    print("• Deploy to production environment")

if __name__ == "__main__":
    asyncio.run(main())
