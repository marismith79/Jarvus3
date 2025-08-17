#!/usr/bin/env python3
"""
Test script to verify that the configuration files are working correctly.
"""

import sys
import os

# Add the demo directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_mac_jurisdictions():
    """Test MAC jurisdictions configuration"""
    print("Testing MAC jurisdictions configuration...")
    
    try:
        from config.mac_jurisdictions import MAC_JURISDICTIONS, STATE_MAPPING
        
        # Test MAC jurisdictions
        assert len(MAC_JURISDICTIONS) > 0, "MAC_JURISDICTIONS should not be empty"
        print(f"✅ Found {len(MAC_JURISDICTIONS)} MAC jurisdictions")
        
        # Test state mapping
        assert len(STATE_MAPPING) > 0, "STATE_MAPPING should not be empty"
        print(f"✅ Found {len(STATE_MAPPING)} state mappings")
        
        # Test specific jurisdiction
        jurisdiction_a = MAC_JURISDICTIONS.get("jurisdiction_a")
        assert jurisdiction_a is not None, "jurisdiction_a should exist"
        assert "name" in jurisdiction_a, "jurisdiction_a should have a name"
        assert "states" in jurisdiction_a, "jurisdiction_a should have states"
        print(f"✅ jurisdiction_a: {jurisdiction_a['name']} with {len(jurisdiction_a['states'])} states")
        
        # Test state mapping
        assert STATE_MAPPING.get("california") == "CA", "California should map to CA"
        print("✅ State mapping working correctly")
        
    except Exception as e:
        print(f"❌ Error testing MAC jurisdictions: {e}")
        return False
    
    return True

def test_gpt_prompts():
    """Test GPT prompts configuration"""
    print("\nTesting GPT prompts configuration...")
    
    try:
        from config.gpt_prompts import (
            create_medicare_search_prompt,
            create_medicare_document_analysis_prompt,
            create_medicare_analysis_prompt,
            create_parsing_agent_prompt,
            create_criteria_matching_prompt,
            create_recommendations_prompt
        )
        
        # Test search prompt
        search_prompt = create_medicare_search_prompt("test query")
        assert len(search_prompt) > 0, "Search prompt should not be empty"
        assert "test query" in search_prompt, "Search prompt should contain the query"
        print("✅ Search prompt working")
        
        # Test document analysis prompt
        doc_prompt = create_medicare_document_analysis_prompt({
            "title": "Test Document",
            "url": "http://test.com",
            "type": "ncd",
            "snippet": "Test snippet"
        })
        assert len(doc_prompt) > 0, "Document analysis prompt should not be empty"
        assert "Test Document" in doc_prompt, "Document analysis prompt should contain document title"
        print("✅ Document analysis prompt working")
        
        # Test other prompts
        analysis_prompt = create_medicare_analysis_prompt("12345", "Test Insurance", [], {}, {})
        assert len(analysis_prompt) > 0, "Analysis prompt should not be empty"
        print("✅ Analysis prompt working")
        
        parsing_prompt = create_parsing_agent_prompt([], {}, "12345", "Test Insurance")
        assert len(parsing_prompt) > 0, "Parsing agent prompt should not be empty"
        print("✅ Parsing agent prompt working")
        
        criteria_prompt = create_criteria_matching_prompt("Test requirements", {})
        assert len(criteria_prompt) > 0, "Criteria matching prompt should not be empty"
        print("✅ Criteria matching prompt working")
        
        recommendations_prompt = create_recommendations_prompt({}, {}, {})
        assert len(recommendations_prompt) > 0, "Recommendations prompt should not be empty"
        print("✅ Recommendations prompt working")
        
    except Exception as e:
        print(f"❌ Error testing GPT prompts: {e}")
        return False
    
    return True

def test_defaults():
    """Test defaults configuration"""
    print("\nTesting defaults configuration...")
    
    try:
        from config.defaults import (
            DEFAULT_REQUIREMENTS,
            DEFAULT_CLINICAL_CRITERIA,
            DEFAULT_RECOMMENDATIONS,
            DEFAULT_DOCUMENT_INFO,
            DEFAULT_PARSING_RESULT,
            get_default_coverage_analysis,
            get_default_criteria_match
        )
        
        # Test default requirements
        assert len(DEFAULT_REQUIREMENTS) > 0, "DEFAULT_REQUIREMENTS should not be empty"
        print(f"✅ Found {len(DEFAULT_REQUIREMENTS)} default requirements")
        
        # Test default clinical criteria
        assert len(DEFAULT_CLINICAL_CRITERIA) > 0, "DEFAULT_CLINICAL_CRITERIA should not be empty"
        print(f"✅ Found {len(DEFAULT_CLINICAL_CRITERIA)} default clinical criteria")
        
        # Test default recommendations
        assert len(DEFAULT_RECOMMENDATIONS) > 0, "DEFAULT_RECOMMENDATIONS should not be empty"
        print(f"✅ Found {len(DEFAULT_RECOMMENDATIONS)} default recommendations")
        
        # Test default document info
        assert "title" in DEFAULT_DOCUMENT_INFO, "DEFAULT_DOCUMENT_INFO should have title"
        assert "requirements" in DEFAULT_DOCUMENT_INFO, "DEFAULT_DOCUMENT_INFO should have requirements"
        print("✅ Default document info working")
        
        # Test default parsing result
        assert "critical_requirements" in DEFAULT_PARSING_RESULT, "DEFAULT_PARSING_RESULT should have critical_requirements"
        assert "request_validation" in DEFAULT_PARSING_RESULT, "DEFAULT_PARSING_RESULT should have request_validation"
        print("✅ Default parsing result working")
        
        # Test default coverage analysis function
        coverage_analysis = get_default_coverage_analysis("12345", "Test Insurance")
        assert coverage_analysis["cpt_code"] == "12345", "Coverage analysis should have correct CPT code"
        assert coverage_analysis["insurance_provider"] == "Test Insurance", "Coverage analysis should have correct provider"
        print("✅ Default coverage analysis function working")
        
        # Test default criteria match function
        from dataclasses import dataclass
        
        @dataclass
        class MockRequirement:
            requirement_type: str
        
        requirements = [MockRequirement("Genetic counselor consultation required")]
        patient_context = {"has_genetic_counseling": True}
        criteria_match = get_default_criteria_match(requirements, patient_context)
        assert "Genetic counselor consultation required" in criteria_match, "Criteria match should contain requirement"
        print("✅ Default criteria match function working")
        
    except Exception as e:
        print(f"❌ Error testing defaults: {e}")
        return False
    
    return True

def test_enhanced_insurance_analysis():
    """Test that the main file can import the configuration"""
    print("\nTesting enhanced insurance analysis with configuration...")
    
    try:
        from demo.insurance_analysis import EnhancedInsuranceAnalysis
        
        # Create an instance
        analyzer = EnhancedInsuranceAnalysis()
        
        # Test that MAC jurisdictions are loaded
        assert len(analyzer.mac_jurisdictions) > 0, "MAC jurisdictions should be loaded"
        print(f"✅ EnhancedInsuranceAnalysis loaded {len(analyzer.mac_jurisdictions)} MAC jurisdictions")
        
        # Test MAC jurisdiction lookup
        jurisdiction = analyzer.get_mac_jurisdiction("CA")
        assert jurisdiction is not None, "Should find jurisdiction for CA"
        print(f"✅ Found jurisdiction for CA: {jurisdiction['name']}")
        
        # Test state extraction
        state = analyzer.extract_patient_state_from_address("123 Main St, New York, NY")
        assert state == "NY", "Should extract NY from address"
        print(f"✅ Extracted state from address: {state}")
        
    except Exception as e:
        print(f"❌ Error testing enhanced insurance analysis: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🧪 Testing Configuration Files")
    print("=" * 50)
    
    tests = [
        test_mac_jurisdictions,
        test_gpt_prompts,
        test_defaults,
        test_enhanced_insurance_analysis
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Configuration is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
