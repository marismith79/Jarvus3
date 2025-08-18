import os
import json
import time
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import requests
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI

# Import configuration
from config.mac_jurisdictions import MAC_JURISDICTIONS, STATE_MAPPING
from config.gpt_prompts import (
    create_medicare_search_prompt,
    create_medicare_document_analysis_prompt,
    create_medicare_analysis_prompt,
    create_parsing_agent_prompt,
    create_criteria_matching_prompt,
    create_recommendations_prompt
)
from config.defaults import (
    DEFAULT_REQUIREMENTS,
    DEFAULT_CLINICAL_CRITERIA,
    DEFAULT_RECOMMENDATIONS,
    DEFAULT_DOCUMENT_INFO,
    DEFAULT_PARSING_RESULT,
    get_default_coverage_analysis,
    get_default_criteria_match
)

# Load environment variables from .env file
load_dotenv()

@dataclass
class InsuranceRequirement:
    """Data class for insurance requirements"""
    requirement_type: str
    description: str
    evidence_basis: str
    documentation_needed: List[str]
    clinical_criteria: List[str]
    source_document: str
    confidence_score: float

@dataclass
class CoverageAnalysis:
    """Data class for coverage analysis results"""
    cpt_code: str
    insurance_provider: str
    coverage_status: str
    coverage_details: str
    requirements: List[InsuranceRequirement]
    patient_criteria_match: Dict[str, bool]
    confidence_score: float
    search_sources: List[Dict]
    recommendations: List[str]
    mac_jurisdiction: Optional[str] = None
    ncd_applicable: bool = False
    lcd_applicable: bool = False

class EnhancedInsuranceAnalysis:
    """
    Enhanced insurance analysis that combines coverage determination and requirements extraction
    using GPT-5 search mode to pull real medical policy documents from the internet.
    """
    
    def __init__(self):
        # Support both GPT-4 and GPT-5 with environment variable selection
        self.gpt_model = os.getenv('GPT_MODEL', 'gpt-4o-mini-search-preview').lower()  # Default to GPT-4o-mini-search-preview
        self.api_key = os.getenv('OPENAI_API_KEY', os.getenv('GPT5_API_KEY'))
        self.client = OpenAI(api_key=self.api_key)
        self.search_cache = {}
        self.policy_cache = {}
        
        # Debug: Check if API key is loaded
        if self.api_key == 'demo_key':
            print("⚠️  WARNING: Using demo key. Please check your OPENAI_API_KEY environment variable.")
        else:
            print(f"✅ OpenAI API key loaded successfully (starts with: {self.api_key[:10]}...)")
        
        print(f"🤖 Using model: {self.gpt_model}")
        
        # Validate model selection
        if self.gpt_model not in ['gpt-4o', 'gpt-4o-mini-search-preview', 'gpt-5-nano']:
            print(f"⚠️  WARNING: Unknown model '{self.gpt_model}'. Defaulting to 'gpt-4o-mini-search-preview'")
            self.gpt_model = 'gpt-4o-mini-search-preview'
        
        # Medicare Administrative Contractors (MACs) and their jurisdictions
        self.mac_jurisdictions = MAC_JURISDICTIONS
        
    def get_mac_jurisdiction(self, patient_state: str) -> Optional[Dict]:
        """
        Get the MAC jurisdiction for a patient based on their state.
        
        Args:
            patient_state: Two-letter state code (e.g., "CA", "NY")
            
        Returns:
            MAC jurisdiction information or None if not found
        """
        patient_state = patient_state.upper()
        
        for jurisdiction_id, jurisdiction_info in self.mac_jurisdictions.items():
            if patient_state in jurisdiction_info["states"]:
                return {
                    "jurisdiction_id": jurisdiction_id,
                    "name": jurisdiction_info["name"],
                    "states": jurisdiction_info["states"],
                    "website": jurisdiction_info["website"],
                    "description": jurisdiction_info["description"]
                }
        
        return None
        
    def extract_patient_state_from_address(self, address: str) -> Optional[str]:
        """
        Extract patient state from address string.
        
        Args:
            address: Address string (e.g., "189 Elm St, New York, NY")
            
        Returns:
            Two-letter state code or None if not found
        """
        if not address:
            return None
        
        # Look for state pattern at the end of address
        # Common patterns: "City, ST" or "City, State"
        parts = address.split(',')
        if len(parts) >= 2:
            last_part = parts[-1].strip()
            
            # Check if it's a 2-letter state code
            if len(last_part) == 2 and last_part.isupper():
                return last_part
            
            # Check if it's a full state name
            state_lower = last_part.lower()
            if state_lower in STATE_MAPPING:
                return STATE_MAPPING[state_lower]
        
        return None
        
    # async def analyze_insurance_coverage_and_requirements(
    #     self, 
    #     cpt_code: str, 
    #     insurance_provider: str, 
    #     service_type: str,
    #     patient_context: Optional[Dict] = None,
    #     patient_address: Optional[str] = None
    # ) -> CoverageAnalysis:
    #     """
    #     Main method that combines coverage determination and requirements extraction.
        
    #     Args:
    #         cpt_code: CPT code for the service
    #         insurance_provider: Name of insurance provider
    #         service_type: Type of service (e.g., "genetic testing", "imaging")
    #         patient_context: Optional patient context for criteria matching
    #         patient_address: Optional patient address for state extraction
            
    #     Returns:
    #         CoverageAnalysis object with comprehensive results
    #     """
        
    #     # Determine MAC jurisdiction for Medicare patients
    #     mac_jurisdiction = None
    #     if any(medicare_term in insurance_provider.lower() 
    #            for medicare_term in ['medicare', 'original medicare', 'cms']):
            
    #         # Try to get state from patient context first
    #         patient_state = None
    #         if patient_context and patient_context.get('patient_state'):
    #             patient_state = patient_context.get('patient_state')
    #         elif patient_address:
    #             # Extract state from address if not in context
    #             patient_state = self.extract_patient_state_from_address(patient_address)
            
    #         if patient_state:
    #             mac_jurisdiction = self.get_mac_jurisdiction(patient_state)
        
    #     # Step 1: Search for medical policy documents using GPT-5 search mode
    #     print(f"🔍 Starting insurance analysis for CPT {cpt_code}, Provider: {insurance_provider}")
    #     if mac_jurisdiction:
    #         print(f"🏛️  MAC Jurisdiction: {mac_jurisdiction['name']} ({mac_jurisdiction['jurisdiction_id']})")
        
    #     search_results = await self._search_medical_policies_with_gpt5(
    #         cpt_code, insurance_provider, service_type, mac_jurisdiction
    #     )
        
    #     print(f"📊 Found {len(search_results)} search results")
        
    #     # Step 2: Extract and parse policy documents using GPT
    #     policy_documents = await self._extract_policy_documents_with_gpt(search_results)
        
    #     # Step 3: Analyze coverage and extract requirements using GPT
    #     coverage_info = await self._analyze_coverage_and_requirements_with_gpt(
    #         cpt_code, insurance_provider, policy_documents, patient_context, mac_jurisdiction
    #     )
        
    #     # Step 4: Check patient criteria against requirements
    #     patient_criteria_match = {}
    #     if patient_context:
    #         patient_criteria_match = await self._check_patient_criteria_with_gpt(
    #             coverage_info.requirements, patient_context
    #         )
        
    #     # Step 5: Generate recommendations using GPT
    #     recommendations = await self._generate_recommendations_with_gpt(
    #         coverage_info, patient_criteria_match, patient_context
    #     )
        
    #     return CoverageAnalysis(
    #         cpt_code=cpt_code,
    #         insurance_provider=insurance_provider,
    #         coverage_status=coverage_info.coverage_status,
    #         coverage_details=coverage_info.coverage_details,
    #         requirements=coverage_info.requirements,
    #         patient_criteria_match=patient_criteria_match,
    #         confidence_score=coverage_info.confidence_score,
    #         search_sources=search_results,
    #         recommendations=recommendations,
    #         mac_jurisdiction=mac_jurisdiction["name"] if mac_jurisdiction else None,
    #         ncd_applicable=coverage_info.ncd_applicable if hasattr(coverage_info, 'ncd_applicable') else False,
    #         lcd_applicable=coverage_info.lcd_applicable if hasattr(coverage_info, 'lcd_applicable') else False
    #     )
    
    async def _search_medical_policies_with_gpt5(
        self, 
        cpt_code: str, 
        insurance_provider: str, 
        service_type: str,
        mac_jurisdiction: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Use GPT-5 search mode to find relevant medical policy documents.
        Specifically targets Medicare NCDs, LCDs, and LCAs for Medicare providers.
        """
        
        # Create cache key including MAC jurisdiction
        mac_id = mac_jurisdiction["jurisdiction_id"] if mac_jurisdiction else "no_mac"
        cache_key = f"{insurance_provider}_{cpt_code}_{service_type}_{mac_id}"
        
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
        
        # Generate search queries optimized for Medicare documents
        search_queries = self._generate_medicare_search_queries(
            cpt_code, insurance_provider, service_type, mac_jurisdiction
        )
        
        all_search_results = []
        
        # Run searches in smaller batches to avoid overwhelming the API
        print(f"🚀 Starting GPT-5 searches for {len(search_queries)} queries...")
        
        # Take more queries since GPT-4o is faster
        important_queries = search_queries[:12]  # Increased from 5 to 12
        print(f"📝 Using top {len(important_queries)} queries for comprehensive search")
        
        # Create tasks for the important searches
        search_tasks = []
        for query in important_queries:
            task = self._gpt_search(None, query)  # session not needed for GPT API
            search_tasks.append(task)
        
        # Execute searches in parallel
        try:
            search_results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Process results, handling any exceptions
            for i, result in enumerate(search_results_list):
                if isinstance(result, Exception):
                    print(f"❌ Error searching for query '{important_queries[i]}': {result}")
                    continue
                elif result:
                    all_search_results.extend(result)
                    
        except Exception as e:
            print(f"❌ Error in parallel search execution: {e}")
            # Fallback to sequential search if parallel fails
            for query in important_queries:
                try:
                    search_results = await self._gpt_search(None, query)
                    all_search_results.extend(search_results)
                except Exception as e:
                    print(f"Error searching for query '{query}': {e}")
                    continue
        
        # Remove duplicates and sort by relevance
        unique_results = self._deduplicate_results(all_search_results)
        unique_results.sort(key=lambda x: x.get('relevance', 0), reverse=True)
        
        # Cache results
        self.search_cache[cache_key] = unique_results[:10]  # Keep top 10 results
        
        return self.search_cache[cache_key]
    
    def _generate_medicare_search_queries(
        self, 
        cpt_code: str, 
        insurance_provider: str, 
        service_type: str,
        mac_jurisdiction: Optional[Dict] = None
    ) -> List[str]:
        """
        Generate comprehensive search queries for all Medicare document types and supporting documents.
        """
        
        queries = []
        
        # Check if this is a Medicare provider
        is_medicare = any(medicare_term in insurance_provider.lower() 
                         for medicare_term in ['medicare', 'original medicare', 'cms'])
        
        if is_medicare:
            # Core Medicare Coverage Documents (NCDs, LCDs, LCAs)
            queries.extend([
                f"Medicare NCD {cpt_code} {service_type}",
                f"Medicare LCD {cpt_code} {service_type}",
                f"Medicare LCA {cpt_code} {service_type}",
                f"site:cms.gov Medicare Coverage Database {cpt_code}",
                f"site:cms.gov NCD {cpt_code} {service_type}",
                f"site:cms.gov LCD {cpt_code} {service_type}",
                f"site:cms.gov LCA {cpt_code} {service_type}"
            ])
            
            # Medicare Medical Necessity and Coverage Policies
            queries.extend([
                f"Medicare medical necessity {cpt_code} {service_type}",
                f"Medicare coverage policy {cpt_code} {service_type}",
                f"Medicare coverage determination {cpt_code} {service_type}",
                f"Medicare clinical policy {cpt_code} {service_type}",
                f"Medicare utilization management {cpt_code} {service_type}"
            ])
            
            # Medicare Administrative Documents
            queries.extend([
                f"Medicare Administrative Contractor MAC {cpt_code} {service_type}",
                f"Medicare contractor policy {cpt_code} {service_type}",
                f"Medicare local coverage determination {cpt_code} {service_type}",
                f"Medicare national coverage determination {cpt_code} {service_type}"
            ])
            
            # Medicare Advantage Specific Documents
            if "advantage" in insurance_provider.lower():
                queries.extend([
                    f"{insurance_provider} Medicare Advantage medical policy {cpt_code} {service_type}",
                    f"{insurance_provider} Medicare Advantage coverage determination {cpt_code}",
                    f"{insurance_provider} Medicare Advantage LCD NCD {service_type}",
                    f"{insurance_provider} Medicare Advantage clinical policy {cpt_code}",
                    f"{insurance_provider} Medicare Advantage prior authorization {cpt_code}",
                    f"{insurance_provider} Medicare Advantage medical necessity {cpt_code}"
                ])
            
            # MAC-Specific Queries (if jurisdiction is known)
            if mac_jurisdiction:
                mac_name = mac_jurisdiction["name"]
                mac_id = mac_jurisdiction["jurisdiction_id"]
                queries.extend([
                    f"{mac_name} Medicare {cpt_code} {service_type}",
                    f"{mac_name} LCD {cpt_code} {service_type}",
                    f"{mac_name} LCA {cpt_code} {service_type}",
                    f"site:{mac_jurisdiction.get('website', '')} {cpt_code} {service_type}",
                    f"MAC {mac_id} {cpt_code} {service_type}",
                    f"Medicare {mac_id} jurisdiction {cpt_code} {service_type}"
                ])
            
            # Supporting Clinical Documents
            queries.extend([
                f"Medicare clinical evidence {cpt_code} {service_type}",
                f"Medicare clinical studies {cpt_code} {service_type}",
                f"Medicare evidence-based coverage {cpt_code} {service_type}",
                f"Medicare clinical guidelines {cpt_code} {service_type}",
                f"Medicare technology assessment {cpt_code} {service_type}"
            ])
            
            # Regulatory and Compliance Documents
            queries.extend([
                f"Medicare regulatory requirements {cpt_code} {service_type}",
                f"Medicare compliance policy {cpt_code} {service_type}",
                f"Medicare billing requirements {cpt_code} {service_type}",
                f"Medicare coding guidelines {cpt_code} {service_type}",
                f"Medicare documentation requirements {cpt_code} {service_type}"
            ])
            
            # FDA and Clinical Trial Documents
            queries.extend([
                f"FDA approval {cpt_code} {service_type}",
                f"FDA clearance {cpt_code} {service_type}",
                f"clinical trial {cpt_code} {service_type}",
                f"FDA companion diagnostic {cpt_code} {service_type}",
                f"FDA breakthrough device {cpt_code} {service_type}"
            ])
            
            # Professional Society Guidelines
            queries.extend([
                f"NCCN guidelines {cpt_code} {service_type}",
                f"ASCO guidelines {cpt_code} {service_type}",
                f"professional society guidelines {cpt_code} {service_type}",
                f"clinical practice guidelines {cpt_code} {service_type}",
                f"evidence-based guidelines {cpt_code} {service_type}"
            ])
            
            # Cost and Utilization Documents
            queries.extend([
                f"Medicare cost analysis {cpt_code} {service_type}",
                f"Medicare utilization review {cpt_code} {service_type}",
                f"Medicare cost effectiveness {cpt_code} {service_type}",
                f"Medicare budget impact {cpt_code} {service_type}"
            ])
            
        else:
            # Non-Medicare Provider Comprehensive Queries
            queries.extend([
                f"{insurance_provider} medical policy {cpt_code} {service_type} coverage requirements",
                f"{insurance_provider} prior authorization requirements {cpt_code} {service_type}",
                f"{insurance_provider} coverage determination {service_type} policy document",
                f"{insurance_provider} medical necessity criteria {cpt_code} {service_type}",
                f"{insurance_provider} clinical policy {cpt_code} {service_type}",
                f"{insurance_provider} utilization management {cpt_code} {service_type}",
                f"{insurance_provider} evidence-based coverage {cpt_code} {service_type}",
                f"{insurance_provider} clinical guidelines {cpt_code} {service_type}",
                f"{insurance_provider} technology assessment {cpt_code} {service_type}",
                f"{insurance_provider} FDA approval {cpt_code} {service_type}",
                f"{insurance_provider} professional guidelines {cpt_code} {service_type}",
                f"{insurance_provider} cost effectiveness {cpt_code} {service_type}"
            ])
        
        return queries
    
    async def _gpt_search(self, session: Optional[aiohttp.ClientSession], query: str) -> List[Dict]:
        """
        Perform search using either GPT-4 or GPT-5 based on configuration.
        """
        
        # Debug: Check if we're using demo key
        if self.api_key == 'demo_key':
            print("⚠️  Using demo key - falling back to simulated results")
            return self._get_fallback_search_results(query)
        
        # Enhanced prompt for Medicare document search
        search_prompt = create_medicare_search_prompt(query)
        
        # Log the request details
        print(f"\n🔍 {self.gpt_model.upper()} SEARCH REQUEST:")
        print(f"   Query: {query}")
        print(f"   Model: {self.gpt_model}")
        print(f"   Temperature: 0.5")
        print(f"   User Message Length: {len(search_prompt)} characters")
        print(f"   User Message Preview: {search_prompt[:200]}...")
        
        try:
            print(f"\n📤 Sending request to OpenAI API...")
            
            import asyncio
            
            if self.gpt_model == 'gpt-5-nano':
                # Use GPT-5 API format
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.responses.create,
                        model="gpt-5-nano",
                        tools=[{"type": "web_search_preview"}],
                        input=search_prompt
                    ),
                    timeout=120.0  # GPT-5 needs more time
                )
                
                # Log the response details
                print(f"\n📥 {self.gpt_model.upper()} SEARCH RESPONSE:")
                print(f"   Model Used: {response.model}")
                print(f"   Response Content Length: {len(response.output_text)} characters")
                print(f"   Response Content Preview: {response.output_text[:300]}...")
                
                print(f"✅ {self.gpt_model} search successful for: {query}")
                
                # Extract search results from GPT-5 response
                search_results = self._parse_gpt5_search_response(response, query)
                print(f"📊 Parsed {len(search_results)} search results")
                return search_results
                
            elif self.gpt_model in ['gpt-4o', 'gpt-4o-mini-search-preview']:
                # Use GPT-4o-mini-search-preview API format with web search
                # Note: gpt-4o-mini-search-preview doesn't support temperature parameter
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.completions.create,
                        model="gpt-4o-mini-search-preview",
                        messages=[
                            {"role": "system", "content": "You are a medical policy search assistant. Search for and return relevant medical policy documents."},
                            {"role": "user", "content": search_prompt}
                        ],
                        max_tokens=2000
                    ),
                    timeout=60.0  # GPT-4o-mini-search-preview is faster
                )
                
                # Log the response details
                print(f"\n📥 {self.gpt_model.upper()} SEARCH RESPONSE:")
                print(f"   Model Used: {response.model}")
                print(f"   Usage - Prompt Tokens: {response.usage.prompt_tokens}")
                print(f"   Usage - Completion Tokens: {response.usage.completion_tokens}")
                print(f"   Usage - Total Tokens: {response.usage.total_tokens}")
                print(f"   Response Content Length: {len(response.choices[0].message.content)} characters")
                print(f"   Response Content Preview: {response.choices[0].message.content[:300]}...")
                
                print(f"✅ {self.gpt_model} search successful for: {query}")
                
                # Extract search results from GPT-4o response
                search_results = self._parse_gpt4_search_response(response, query)
                print(f"📊 Parsed {len(search_results)} search results")
                return search_results
                    
        except asyncio.TimeoutError:
            print(f"❌ {self.gpt_model} search timed out for: {query}")
            print(f"⚠️  Search timeout - no real results available")
            return []
        except Exception as e:
            print(f"❌ Error in {self.gpt_model} search: {e}")
            print(f"   Error Type: {type(e).__name__}")
            print(f"   Error Details: {str(e)}")
            print(f"⚠️  Search error - no real results available")
            return []
    

    
    async def _parse_policy_document_with_gpt(self, session: aiohttp.ClientSession, search_result: Dict) -> Optional[Dict]:
        """
        Parse a policy document using either GPT-4 or GPT-5 based on configuration.
        """
        
        # Enhanced prompt for Medicare document analysis
        prompt = create_medicare_document_analysis_prompt(search_result)
        
        # Log the request details
        # For document parsing, we always use gpt-4o (not the search-preview model)
        actual_model = "gpt-4o" if self.gpt_model in ['gpt-4o', 'gpt-4o-mini-search-preview'] else self.gpt_model
        print(f"\n📄 {actual_model.upper()} POLICY DOCUMENT PARSING REQUEST:")
        print(f"   Document Title: {search_result.get('title', 'Unknown')}")
        print(f"   Document URL: {search_result.get('url', 'Unknown')}")
        print(f"   Model: {actual_model}")
        print(f"   Temperature: 0.5")
        print(f"   User Message Length: {len(prompt)} characters")
        print(f"   User Message Preview: {prompt[:200]}...")
        
        try:
            print(f"\n📤 Sending policy document parsing request to OpenAI API...")
            
            import asyncio
            
            if self.gpt_model == 'gpt-5-nano':
                # Use GPT-5 API format
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.responses.create,
                        model="gpt-5-nano",
                        input=prompt
                    ),
                    timeout=30.0
                )
                
                # Log the response details
                print(f"\n📥 {actual_model.upper()} POLICY DOCUMENT PARSING RESPONSE:")
                print(f"   Model Used: {response.model}")
                print(f"   Response Content Length: {len(response.output_text)} characters")
                print(f"   Response Content Preview: {response.output_text[:300]}...")
                
                print(f"✅ Policy document parsing successful for: {search_result.get('title', 'Unknown')}")
                
                # Parse the response
                parsed_document = self._parse_gpt5_policy_response(response, search_result)
                if parsed_document:
                    print(f"📊 Successfully parsed policy document with {len(parsed_document.get('requirements', []))} requirements")
                else:
                    print(f"⚠️  Failed to parse policy document")
                
                return parsed_document
                
            else:
                # Use GPT-4o API format (no web search needed for document parsing)
                # Note: Always use gpt-4o for document parsing, not the search-preview model
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.completions.create,
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a medical policy document analyzer. Extract structured information from policy documents."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.5,
                        max_tokens=1500
                    ),
                    timeout=30.0
                )
                
                # Log the response details
                print(f"\n📥 {actual_model.upper()} POLICY DOCUMENT PARSING RESPONSE:")
                print(f"   Model Used: {response.model}")
                print(f"   Usage - Prompt Tokens: {response.usage.prompt_tokens}")
                print(f"   Usage - Completion Tokens: {response.usage.completion_tokens}")
                print(f"   Usage - Total Tokens: {response.usage.total_tokens}")
                print(f"   Response Content Length: {len(response.choices[0].message.content)} characters")
                print(f"   Response Content Preview: {response.choices[0].message.content[:300]}...")
                
                print(f"✅ Policy document parsing successful for: {search_result.get('title', 'Unknown')}")
                
                # Parse the response
                parsed_document = self._parse_gpt4_policy_response(response, search_result)
                if parsed_document:
                    print(f"📊 Successfully parsed policy document with {len(parsed_document.get('requirements', []))} requirements")
                else:
                    print(f"⚠️  Failed to parse policy document")
                
                return parsed_document
            
            content = response.output_text
            
            # Parse JSON response
            try:
                if '{' in content and '}' in content:
                    start_idx = content.find('{')
                    end_idx = content.rfind('}') + 1
                    json_str = content[start_idx:end_idx]
                    parsed_doc = json.loads(json_str)
                    
                    # Add source information
                    parsed_doc['source'] = search_result.get('source', 'Unknown')
                    parsed_doc['document_type'] = search_result.get('type', 'Unknown')
                    return parsed_doc
            except json.JSONDecodeError:
                pass
            
            # Fallback to structured extraction
            return self._extract_document_info_from_text(content, search_result)
                
        except asyncio.TimeoutError:
            print(f"GPT-5 document parsing timed out")
            return self._get_fallback_document_info(search_result)
        except Exception as e:
            print(f"Error in GPT-5 document parsing: {e}")
            return self._get_fallback_document_info(search_result)
    

    
    async def _analyze_coverage_and_requirements_with_gpt(
        self, 
        cpt_code: str, 
        insurance_provider: str, 
        policy_documents: List[Dict],
        patient_context: Optional[Dict] = None,
        mac_jurisdiction: Optional[Dict] = None
    ) -> CoverageAnalysis:
        """
        Analyze coverage status and extract requirements from policy documents using GPT-5.
        Enhanced for Medicare NCDs, LCDs, and LCAs.
        """
        
        # Enhanced analysis prompt for Medicare documents
        prompt = create_medicare_analysis_prompt(
            cpt_code, insurance_provider, policy_documents, patient_context, mac_jurisdiction
        )
        
        try:
            import asyncio
            
            if self.gpt_model == 'gpt-5-nano':
                # Use GPT-5 API format
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.responses.create,
                        model="gpt-5-nano",
                        input=prompt
                    ),
                    timeout=30.0
                )
                content = response.output_text
            else:
                # Use GPT-4o API format (no web search needed for analysis)
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.completions.create,
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a medical policy analyst. Analyze coverage and requirements from policy documents."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.6,
                        max_tokens=2000
                    ),
                    timeout=30.0
                )
                content = response.choices[0].message.content
            
            # Parse analysis results
            analysis_result = self._parse_analysis_response(content, cpt_code, insurance_provider, mac_jurisdiction)
            return analysis_result
                
        except asyncio.TimeoutError:
            print(f"{self.gpt_model} analysis timed out")
            return self._get_fallback_analysis(cpt_code, insurance_provider, policy_documents, mac_jurisdiction)
        except Exception as e:
            print(f"Error in {self.gpt_model} analysis: {e}")
            return self._get_fallback_analysis(cpt_code, insurance_provider, policy_documents, mac_jurisdiction)
    

    
    def _parse_gpt4_search_response(self, response, query: str) -> List[Dict]:
        """
        Parse GPT-4o-mini-search-preview response and extract structured results.
        """
        import re
        
        try:
            # Extract content from GPT-4o-mini-search-preview response
            content = response.choices[0].message.content
            print(f"🔍 Parsing GPT-4o-mini-search-preview response content (length: {len(content)})")
            
            # Try to parse JSON from the response
            if '[' in content and ']' in content:
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                json_str = content[start_idx:end_idx]
                print(f"📋 Extracted JSON string (length: {len(json_str)})")
                
                try:
                    results = json.loads(json_str)
                    if isinstance(results, list):
                        print(f"✅ Successfully parsed {len(results)} JSON results")
                        return results
                    else:
                        print(f"⚠️  Parsed JSON is not a list: {type(results)}")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    print(f"📋 JSON string preview: {json_str[:200]}...")
                    
                    # Try to clean up common JSON issues
                    try:
                        # Remove markdown formatting that might be mixed in
                        cleaned_json = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', json_str)
                        cleaned_json = re.sub(r'```json\s*', '', cleaned_json)
                        cleaned_json = re.sub(r'\s*```', '', cleaned_json)
                        
                        results = json.loads(cleaned_json)
                        if isinstance(results, list):
                            print(f"✅ Successfully parsed {len(results)} results after cleanup")
                            return results
                    except:
                        print(f"⚠️  JSON cleanup also failed")
            
            # If JSON parsing fails, try to extract structured information
            print(f"🔄 Falling back to text extraction for query: {query}")
            return self._extract_structured_results_from_text(content, query)
            
        except Exception as e:
            print(f"❌ Error parsing GPT-4o-mini-search-preview response: {e}")
            print(f"   Error Type: {type(e).__name__}")
            print(f"⚠️  Parse error - no real results available")
            return []
    
    def _parse_gpt5_search_response(self, response, query: str) -> List[Dict]:
        """
        Parse GPT-5 search response and extract structured results.
        """
        try:
            # Extract content from GPT-5 response
            content = response.output_text
            
            # Try to parse JSON from the response
            if '[' in content and ']' in content:
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                json_str = content[start_idx:end_idx]
                
                try:
                    results = json.loads(json_str)
                    if isinstance(results, list):
                        return results
                except json.JSONDecodeError:
                    pass
            
            # If JSON parsing fails, try to extract structured information
            return self._extract_structured_results_from_text(content, query)
            
        except Exception as e:
            print(f"Error parsing GPT-5 search response: {e}")
            return self._get_fallback_search_results(query)
    
    # def _validate_search_results(self, results: List[Dict], query: str) -> List[Dict]:
    #     """
    #     Validate search results to filter out hallucinations and fake data.
    #     """
    #     validated_results = []
        
    #     for result in results:
    #         # Check for required fields
    #         if not isinstance(result, dict):
    #             continue
                
    #         title = result.get('title', '')
    #         url = result.get('url', '')
            
    #         # Skip results with missing essential fields
    #         if not title or not url:
    #             continue
            
    #         # Filter out common hallucination patterns
    #         if any(pattern in url.lower() for pattern in [
    #             'example.com', 'example-', 'placeholder', 'fake', 'dummy', 'test',
    #             'sample.com', 'demo.com', 'mock.com', 'temporary.com'
    #         ]):
    #             print(f"🚫 Filtered out hallucinated URL: {url}")
    #             continue
            
    #         # Filter out generic or suspicious titles
    #         if any(pattern in title.lower() for pattern in [
    #             'example', 'placeholder', 'fake', 'dummy', 'test', 'sample',
    #             'mock', 'temporary', 'generic'
    #         ]):
    #             print(f"🚫 Filtered out suspicious title: {title}")
    #             continue
            
    #         # Check for realistic URL patterns
    #         if not any(domain in url.lower() for domain in [
    #             'cms.gov', 'medicare.gov', 'fda.gov', 'nccn.org', 'asco.org',
    #             'medicare', 'gov', 'org', 'edu', 'health', 'medical'
    #         ]):
    #             print(f"⚠️  Suspicious URL pattern: {url}")
    #             # Don't filter out completely, but flag for review
            
    #         # Validate URL format
    #         if not url.startswith(('http://', 'https://')):
    #             print(f"🚫 Invalid URL format: {url}")
    #             continue
            
    #         # If we get here, the result looks valid
    #         validated_results.append(result)
        
    #     print(f"🔍 Validation: {len(results)} total results, {len(validated_results)} validated")
    #     return validated_results
    
    def _extract_structured_results_from_text(self, text: str, query: str) -> List[Dict]:
        """
        Extract structured search results from GPT text response.
        Handles both structured text and markdown-formatted responses.
        """
        results = []
        
        # First, try to extract markdown links if present
        import re
        
        # Look for markdown links: [text](url)
        markdown_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text)
        
        if markdown_links:
            print(f"🔍 Found {len(markdown_links)} markdown links in response")
            for i, (title, url) in enumerate(markdown_links):
                # Skip only if it's just a bare domain name without any descriptive text
                # But keep domain names that are part of actual document titles
                if (title.lower() in ['cms.gov', 'medicare.gov', 'fda.gov', 'nccn.org', 'asco.org'] and 
                    len(title) <= 20):  # Only skip if it's a short domain name
                    print(f"⏭️  Skipping bare domain: {title}")
                    continue
                    
                # Clean up the title if it's a domain name but has a longer description
                clean_title = title
                if title.lower() in ['cms.gov', 'medicare.gov', 'fda.gov', 'nccn.org', 'asco.org']:
                    # Extract a better title from the URL or use a generic one
                    if 'medicare-coverage-database' in url:
                        clean_title = 'Medicare Coverage Database Article'
                    elif 'medicare.gov' in url:
                        clean_title = 'Medicare.gov Policy Document'
                    elif 'fda.gov' in url:
                        clean_title = 'FDA Policy Document'
                    elif 'nccn.org' in url:
                        clean_title = 'NCCN Clinical Practice Guidelines'
                    elif 'asco.org' in url:
                        clean_title = 'ASCO Clinical Practice Guidelines'
                    else:
                        clean_title = f'Policy Document from {title}'
                
                result = {
                    'title': clean_title,
                    'url': url,
                    'snippet': f'Policy document related to {query}',
                    'relevance': 85 - (i * 5),  # Decreasing relevance for each result
                    'type': 'policy_document',
                    'source': 'GPT Search'
                }
                results.append(result)
                print(f"✅ Added result: {clean_title}")
        
        # If no markdown links found, try structured text parsing
        if not results:
            lines = text.split('\n')
            current_result = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('Title:') or line.startswith('Name:'):
                    if current_result:
                        results.append(current_result)
                    current_result = {'title': line.split(':', 1)[1].strip()}
                elif line.startswith('URL:') or line.startswith('Link:'):
                    current_result['url'] = line.split(':', 1)[1].strip()
                elif line.startswith('Snippet:') or line.startswith('Description:'):
                    current_result['snippet'] = line.split(':', 1)[1].strip()
                elif line.startswith('Relevance:') or line.startswith('Score:'):
                    try:
                        relevance = int(line.split(':', 1)[1].strip().replace('%', ''))
                        current_result['relevance'] = relevance
                    except:
                        current_result['relevance'] = 80
                elif line.startswith('Type:') or line.startswith('Category:'):
                    current_result['type'] = line.split(':', 1)[1].strip()
                elif line.startswith('Source:') or line.startswith('Provider:'):
                    current_result['source'] = line.split(':', 1)[1].strip()
            
            # Add the last result
            if current_result:
                results.append(current_result)
        
        # If still no results, create a fallback result based on the query
        if not results:
            print(f"⚠️  No structured results found, creating fallback for query: {query}")
            results.append({
                'title': f'Policy document for {query}',
                'url': f'https://www.cms.gov/search?q={query.replace(" ", "+")}',
                'snippet': f'Search results for {query}',
                'relevance': 70,
                'type': 'policy_document',
                'source': 'Fallback'
            })
        
        # Add default values for missing fields
        for result in results:
            result.setdefault('relevance', 80)
            result.setdefault('type', 'policy_document')
            result.setdefault('source', result.get('source', 'Unknown'))
        
        print(f"📊 Extracted {len(results)} results from text parsing")
        return results
    
    async def _extract_policy_documents_with_gpt(self, search_results: List[Dict]) -> List[Dict]:
        """
        Extract and parse policy documents from search results using GPT-5.
        """
        
        extracted_documents = []
        
        # Filter documents that need parsing
        documents_to_parse = [
            result for result in search_results 
            if result.get('type') in ['policy_document', 'coverage_determination', 'ncd', 'lcd', 'lca']
        ]
        
        if not documents_to_parse:
            return extracted_documents
        
        # Only parse the top 3 most relevant documents to avoid timeouts
        documents_to_parse = documents_to_parse[:3]
        print(f"📄 Parsing top {len(documents_to_parse)} policy documents in parallel...")
        
        # Create tasks for document parsing
        parse_tasks = []
        for result in documents_to_parse:
            task = self._parse_policy_document_with_gpt(None, result)  # session not needed
            parse_tasks.append(task)
        
        # Execute all parsing in parallel
        try:
            parse_results = await asyncio.gather(*parse_tasks, return_exceptions=True)
            
            # Process results, handling any exceptions
            for i, result in enumerate(parse_results):
                if isinstance(result, Exception):
                    print(f"❌ Error parsing document '{documents_to_parse[i].get('title', 'Unknown')}': {result}")
                    continue
                elif result:
                    extracted_documents.append(result)
                    
        except Exception as e:
            print(f"❌ Error in parallel document parsing: {e}")
            # Fallback to sequential parsing if parallel fails
            for result in documents_to_parse:
                try:
                    extracted_doc = await self._parse_policy_document_with_gpt(None, result)
                    if extracted_doc:
                        extracted_documents.append(extracted_doc)
                except Exception as e:
                    print(f"Error parsing document {result.get('title', 'Unknown')}: {e}")
                    continue
        
        return extracted_documents
    
    def _parse_gpt4_policy_response(self, response, search_result: Dict) -> Optional[Dict]:
        """
        Parse GPT-4o policy document response.
        """
        try:
            content = response.choices[0].message.content
            return self._extract_document_info_from_text(content, search_result)
        except Exception as e:
            print(f"Error parsing GPT-4o policy response: {e}")
            return None
    
    def _parse_gpt5_policy_response(self, response, search_result: Dict) -> Optional[Dict]:
        """
        Parse GPT-5 policy document response.
        """
        try:
            content = response.output_text
            return self._extract_document_info_from_text(content, search_result)
        except Exception as e:
            print(f"Error parsing GPT-5 policy response: {e}")
            return None
    
    def _extract_document_info_from_text(self, text: str, search_result: Dict) -> Dict:
        """
        Extract document information from GPT text response.
        """
        doc_info = {
            "title": search_result.get("title", ""),
            "url": search_result.get("url", ""),
            "source": search_result.get("source", "Unknown"),
            "document_type": search_result.get("type", "Unknown"),
            "requirements": [],
            "evidence_basis": "Based on clinical studies and medical literature",
            "clinical_criteria": [],
            "coverage_status": "Covered with prior authorization",
            "cpt_codes": [],
            "documentation_needed": [],
            "limitations": [],
            "effective_date": "",
            "revision_date": ""
        }
        
        # Extract requirements
        if "requirements" in text.lower():
            lines = text.split('\n')
            in_requirements = False
            for line in lines:
                line = line.strip()
                if "requirements" in line.lower() and ":" in line:
                    in_requirements = True
                    continue
                elif in_requirements and line.startswith('-'):
                    req = line[1:].strip()
                    if req:
                        doc_info["requirements"].append(req)
                elif in_requirements and not line:
                    break
        
        # Extract clinical criteria
        if "criteria" in text.lower():
            lines = text.split('\n')
            in_criteria = False
            for line in lines:
                line = line.strip()
                if "criteria" in line.lower() and ":" in line:
                    in_criteria = True
                    continue
                elif in_criteria and line.startswith('-'):
                    criteria = line[1:].strip()
                    if criteria:
                        doc_info["clinical_criteria"].append(criteria)
                elif in_criteria and not line:
                    break
        
        # Add default requirements if none found
        if not doc_info["requirements"]:
            doc_info["requirements"] = [
                "Genetic counselor consultation required",
                "Family history documentation",
                "Clinical indication documentation",
                "Provider credentials verification"
            ]
        
        return doc_info
    
    def _parse_analysis_response(self, content: str, cpt_code: str, insurance_provider: str, mac_jurisdiction: Optional[Dict]) -> CoverageAnalysis:
        """
        Parse GPT-5 analysis response and create CoverageAnalysis object.
        """
        try:
            # Try to parse JSON response
            if '{' in content and '}' in content:
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                json_str = content[start_idx:end_idx]
                analysis_data = json.loads(json_str)
                
                # Convert to CoverageAnalysis object
                requirements = []
                for req_data in analysis_data.get('requirements', []):
                    requirement = InsuranceRequirement(
                        requirement_type=req_data.get('requirement_type', 'Unknown'),
                        description=req_data.get('description', ''),
                        evidence_basis=req_data.get('evidence_basis', ''),
                        documentation_needed=req_data.get('documentation_needed', []),
                        clinical_criteria=req_data.get('clinical_criteria', []),
                        source_document=req_data.get('source_document', ''),
                        confidence_score=req_data.get('confidence_score', 0.9)
                    )
                    requirements.append(requirement)
                
                return CoverageAnalysis(
                    cpt_code=cpt_code,
                    insurance_provider=insurance_provider,
                    coverage_status=analysis_data.get('coverage_status', 'Covered with prior authorization'),
                    coverage_details=analysis_data.get('coverage_details', f'CPT code {cpt_code} is covered under {insurance_provider} with prior authorization requirements.'),
                    requirements=requirements,
                    patient_criteria_match={},
                    confidence_score=analysis_data.get('confidence_score', 0.9),
                    search_sources=[],
                    recommendations=analysis_data.get('recommendations', []),
                    mac_jurisdiction=mac_jurisdiction["name"] if mac_jurisdiction else None,
                    ncd_applicable=analysis_data.get('medicare_specific', {}).get('ncd_applicable', False),
                    lcd_applicable=analysis_data.get('medicare_specific', {}).get('lcd_applicable', False)
                )
            
        except json.JSONDecodeError:
            pass
        
        # Fallback to structured extraction
        return self._extract_analysis_from_text(content, cpt_code, insurance_provider, mac_jurisdiction)
    
    def _extract_analysis_from_text(self, text: str, cpt_code: str, insurance_provider: str, mac_jurisdiction: Optional[Dict]) -> CoverageAnalysis:
        """
        Extract analysis information from GPT-5 text response.
        """
        # Default requirements
        requirements = [
            InsuranceRequirement(
                requirement_type="Genetic counselor consultation required",
                description="Requirement for genetic counselor consultation",
                evidence_basis="Based on clinical studies and medical literature",
                documentation_needed=["Genetic counselor consultation documentation"],
                clinical_criteria=["High-risk patient population", "Appropriate clinical indication"],
                source_document="Medical Policy Document",
                confidence_score=0.9
            ),
            InsuranceRequirement(
                requirement_type="Family history documentation",
                description="Requirement for family history documentation",
                evidence_basis="Based on clinical studies and medical literature",
                documentation_needed=["Family history documentation"],
                clinical_criteria=["High-risk patient population", "Appropriate clinical indication"],
                source_document="Medical Policy Document",
                confidence_score=0.9
            )
        ]
        
        # Extract recommendations from text
        recommendations = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•'):
                rec = line[1:].strip()
                if rec and len(rec) > 10:
                    recommendations.append(rec)
        
        if not recommendations:
            recommendations = [
                "Ensure all required documentation is complete and current",
                "Verify provider credentials and network participation",
                "Include clinical justification for the requested service"
            ]
        
        return CoverageAnalysis(
            cpt_code=cpt_code,
            insurance_provider=insurance_provider,
            coverage_status="Covered with prior authorization",
            coverage_details=f"CPT code {cpt_code} is covered under {insurance_provider} with prior authorization requirements.",
            requirements=requirements,
            patient_criteria_match={},
            confidence_score=0.85,
            search_sources=[],
            recommendations=recommendations,
            mac_jurisdiction=mac_jurisdiction["name"] if mac_jurisdiction else None,
            ncd_applicable=False,
            lcd_applicable=False
        )
    
    async def _check_patient_criteria_with_gpt(
        self, 
        requirements: List[InsuranceRequirement], 
        patient_context: Dict
    ) -> Dict[str, bool]:
        """
        Check patient data against insurance requirements using GPT-5.
        """
        
        # Create criteria matching prompt
        requirements_text = "\n".join([
            f"- {req.requirement_type}: {req.description}"
            for req in requirements
        ])
        
        prompt = create_criteria_matching_prompt(requirements_text, patient_context)
        
        try:
            import asyncio
            
            if self.gpt_model == 'gpt-5-nano':
                # Use GPT-5 API format
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.responses.create,
                        model="gpt-5-nano",
                        input=prompt
                    ),
                    timeout=30.0
                )
                content = response.output_text
            else:
                # Use GPT-4o API format (no web search needed for criteria matching)
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.completions.create,
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a medical criteria matching assistant. Check if patient data meets insurance requirements."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.5,
                        max_tokens=1000
                    ),
                    timeout=30.0
                )
                content = response.choices[0].message.content
            
            # Parse criteria matching results
            criteria_match = self._parse_criteria_response(content, requirements)
            return criteria_match
                
        except asyncio.TimeoutError:
            print(f"{self.gpt_model} criteria matching timed out")
            return self._get_fallback_criteria_match(requirements, patient_context)
        except Exception as e:
            print(f"Error in {self.gpt_model} criteria matching: {e}")
            return self._get_fallback_criteria_match(requirements, patient_context)
    
    def _parse_criteria_response(self, content: str, requirements: List[InsuranceRequirement]) -> Dict[str, bool]:
        """
        Parse GPT-5 criteria matching response.
        """
        try:
            # Try to parse JSON response
            if '{' in content and '}' in content:
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                json_str = content[start_idx:end_idx]
                criteria_data = json.loads(json_str)
                
                # Convert to requirement-based mapping
                criteria_match = {}
                for req in requirements:
                    req_name = req.requirement_type
                    criteria_match[req_name] = criteria_data.get(req_name, False)
                
                return criteria_match
            
        except json.JSONDecodeError:
            pass
        
        # Fallback to default matching
        return self._get_fallback_criteria_match(requirements, {})
    
    async def _generate_recommendations_with_gpt(
        self, 
        coverage_info: CoverageAnalysis, 
        patient_criteria_match: Dict[str, bool], 
        patient_context: Optional[Dict]
    ) -> List[str]:
        """
        Generate recommendations using GPT-5 based on coverage analysis and patient criteria.
        """
        
        # Create recommendations prompt
        prompt = create_recommendations_prompt(coverage_info, patient_criteria_match, patient_context)
        
        try:
            import asyncio
            
            if self.gpt_model == 'gpt-5-nano':
                # Use GPT-5 API format
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.responses.create,
                        model="gpt-5-nano",
                        input=prompt
                    ),
                    timeout=30.0
                )
                content = response.output_text
            else:
                # Use GPT-4o API format (no web search needed for recommendations)
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.completions.create,
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a medical prior authorization assistant. Generate actionable recommendations."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.8,
                        max_tokens=1500
                    ),
                    timeout=30.0
                )
                content = response.choices[0].message.content
            
            # Parse recommendations
            recommendations = self._parse_recommendations_response(content)
            return recommendations
                
        except asyncio.TimeoutError:
            print(f"{self.gpt_model} recommendations timed out")
            return self._get_fallback_recommendations(coverage_info, patient_criteria_match)
        except Exception as e:
            print(f"Error in {self.gpt_model} recommendations: {e}")
            return self._get_fallback_recommendations(coverage_info, patient_criteria_match)
    
    def _parse_recommendations_response(self, content: str) -> List[str]:
        """
        Parse GPT-5 recommendations response.
        """
        try:
            # Try to parse JSON array
            if '[' in content and ']' in content:
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                json_str = content[start_idx:end_idx]
                recommendations = json.loads(json_str)
                
                if isinstance(recommendations, list):
                    return recommendations
            
        except json.JSONDecodeError:
            pass
        
        # Fallback to text extraction
        recommendations = []
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•') or line.startswith('1.') or line.startswith('2.'):
                rec = line.lstrip('-•123456789. ').strip()
                if rec and len(rec) > 10:
                    recommendations.append(rec)
        
        return recommendations if recommendations else self._get_default_recommendations()
    
    # Fallback methods for when GPT-5 is not available
    def _get_fallback_search_results(self, query: str) -> List[Dict]:
        """Fallback search results when GPT-5 is not available"""
        # Return empty results instead of fake ones to avoid showing example URLs
        print(f"⚠️  No real search results available for: {query}")
        return []
    
    def _get_fallback_document_info(self, search_result: Dict) -> Dict:
        """Fallback document information when GPT-5 is not available"""
        doc_info = DEFAULT_DOCUMENT_INFO.copy()
        doc_info["title"] = search_result.get("title", "")
        doc_info["url"] = search_result.get("url", "")
        doc_info["source"] = search_result.get("source", "Unknown")
        return doc_info
    
    def _get_fallback_analysis(self, cpt_code: str, insurance_provider: str, policy_documents: List[Dict], mac_jurisdiction: Optional[Dict]) -> CoverageAnalysis:
        """Fallback analysis when GPT-5 is not available"""
        # Convert default requirements to InsuranceRequirement objects
        requirements = []
        for req_data in DEFAULT_REQUIREMENTS:
            requirement = InsuranceRequirement(
                requirement_type=req_data["requirement_type"],
                description=req_data["description"],
                evidence_basis=req_data["evidence_basis"],
                documentation_needed=req_data["documentation_needed"],
                clinical_criteria=req_data["clinical_criteria"],
                source_document=req_data["source_document"],
                confidence_score=req_data["confidence_score"]
            )
            requirements.append(requirement)
        
        return CoverageAnalysis(
            cpt_code=cpt_code,
            insurance_provider=insurance_provider,
            coverage_status="Covered with prior authorization",
            coverage_details=f"CPT code {cpt_code} is covered under {insurance_provider} with prior authorization requirements.",
            requirements=requirements,
            patient_criteria_match={},
            confidence_score=0.8,
            search_sources=[],
            recommendations=DEFAULT_RECOMMENDATIONS,
            mac_jurisdiction=mac_jurisdiction["name"] if mac_jurisdiction else None,
            ncd_applicable=False,
            lcd_applicable=False
        )
    
    def _get_fallback_criteria_match(self, requirements: List[InsuranceRequirement], patient_context: Dict) -> Dict[str, bool]:
        """Fallback criteria matching when GPT-5 is not available"""
        return get_default_criteria_match(requirements, patient_context)
    
    def _get_fallback_recommendations(self, coverage_info: CoverageAnalysis, patient_criteria_match: Dict[str, bool]) -> List[str]:
        """Fallback recommendations when GPT-5 is not available"""
        return DEFAULT_RECOMMENDATIONS
    

    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate search results"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result.get("url") not in seen_urls:
                seen_urls.add(result.get("url"))
                unique_results.append(result)
        
        return unique_results
    
    async def _analyze_documents_with_parsing_agent(self, search_results: List[Dict], patient_context: Dict, cpt_code: str, insurance_provider: str) -> Dict:
        """
        Parsing agent that analyzes documents to determine:
        - Checklist of critical requirements for coverage
        - Validation of clinician's PA request against EHR
        - Draft message to clinician if more documents needed
        - Checklist of requirements and medical knowledge for determination
        """
        try:
            print(f"🔍 Parsing Agent: Analyzing {len(search_results)} documents for coverage requirements...")
            
            # Filter relevant documents (policy documents, LCDs, NCDs)
            relevant_docs = [
                doc for doc in search_results 
                if doc.get('type') in ['policy_document', 'coverage_determination', 'ncd', 'lcd', 'lca'] 
                and doc.get('relevance', 0) > 50
            ]
            
            if not relevant_docs:
                print("⚠️  No relevant policy documents found for parsing")
                return {
                    'critical_requirements': [],
                    'request_validation': {'is_valid': False, 'missing_documents': ['No policy documents found']},
                    'clinician_message': 'Unable to analyze coverage requirements due to insufficient policy documentation.',
                    'requirements_checklist': [],
                    'medical_knowledge': []
                }
            
            # Create prompt for parsing agent
            prompt = create_parsing_agent_prompt(relevant_docs, patient_context, cpt_code, insurance_provider)
            
            # Call GPT-5 for analysis
            response = await self._call_gpt5_direct(prompt)
            
            if not response:
                print("❌ Parsing Agent: No response from GPT-5")
                return self._create_fallback_parsing_result()
            
            # Parse the response
            parsing_result = self._parse_parsing_agent_response(response, relevant_docs)
            
            print(f"✅ Parsing Agent: Analysis complete - {len(parsing_result.get('critical_requirements', []))} requirements found")
            return parsing_result
            
        except Exception as e:
            print(f"❌ Parsing Agent Error: {e}")
            return self._create_fallback_parsing_result()
    
    async def _call_gpt5_direct(self, prompt: str):
        """
        Call GPT-5 directly for analysis without web search.
        """
        try:
            import asyncio
            
            if self.gpt_model == 'gpt-5-nano':
                # Use GPT-5 API format
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.responses.create,
                        model="gpt-5-nano",
                        input=prompt
                    ),
                    timeout=60.0
                )
                return response
            else:
                # Use GPT-4o API format as fallback
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.completions.create,
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a medical insurance parsing agent analyzing policy documents."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=2000
                    ),
                    timeout=60.0
                )
                return response
                
        except asyncio.TimeoutError:
            print(f"GPT-5 direct call timed out")
            return None
        except Exception as e:
            print(f"Error in GPT-5 direct call: {e}")
            return None
    

    
    def _parse_parsing_agent_response(self, response, relevant_docs: List[Dict]) -> Dict:
        """
        Parse the parsing agent's response and extract structured information.
        """
        try:
            # Handle both GPT-5 and GPT-4o responses
            if hasattr(response, 'output_text'):
                content = response.output_text  # GPT-5 format
            elif hasattr(response, 'choices') and len(response.choices) > 0:
                content = response.choices[0].message.content  # GPT-4o format
            else:
                print("❌ Unknown response format")
                return self._create_fallback_parsing_result()
            
            print(f"🔍 Parsing agent response content: {content[:500]}...")
            
            # Try to extract JSON from the response
            if '{' in content and '}' in content:
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx]
                    try:
                        result = json.loads(json_str)
                        print(f"✅ Successfully parsed JSON from parsing agent response")
                        
                        # Validate that required fields are present
                        if 'request_validation' not in result:
                            result['request_validation'] = {'is_valid': False, 'missing_documents': [], 'validation_notes': 'Missing validation data'}
                        if 'clinician_message' not in result:
                            result['clinician_message'] = 'Additional documentation required. Please contact the prior authorization team.'
                        if 'critical_requirements' not in result:
                            result['critical_requirements'] = []
                            
                        return result
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error in parsing agent response: {e}")
                        print(f"🔍 JSON string: {json_str}")
            
            # Fallback: extract structured information from text
            print(f"⚠️  Falling back to text extraction for parsing agent response")
            return self._extract_parsing_info_from_text(content, relevant_docs)
            
        except Exception as e:
            print(f"❌ Error parsing parsing agent response: {e}")
            return self._create_fallback_parsing_result()
    
    def _extract_parsing_info_from_text(self, text: str, relevant_docs: List[Dict]) -> Dict:
        """
        Extract parsing information from text response when JSON parsing fails.
        """
        result = {
            'critical_requirements': [],
            'request_validation': {'is_valid': True, 'missing_documents': [], 'validation_notes': 'Analysis completed'},
            'clinician_message': 'Request appears valid based on available documentation.',
            'requirements_checklist': [],
            'medical_knowledge': []
        }
        
        # Extract critical requirements
        if 'requirements' in text.lower():
            lines = text.split('\n')
            in_requirements = False
            for line in lines:
                line = line.strip()
                if 'requirement' in line.lower() and ':' in line:
                    req_text = line.split(':', 1)[1].strip()
                    if req_text:
                        result['critical_requirements'].append({
                            'requirement': req_text,
                            'criteria': 'See policy document',
                            'documentation_needed': 'Clinical documentation',
                            'clinical_criteria': 'Medical necessity'
                        })
        
        # Extract medical knowledge
        if 'medical' in text.lower() or 'evidence' in text.lower():
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if any(keyword in line.lower() for keyword in ['study', 'evidence', 'clinical', 'medical']):
                    result['medical_knowledge'].append({
                        'topic': 'Medical evidence',
                        'evidence': line,
                        'source_document': relevant_docs[0].get('title', 'Policy Document') if relevant_docs else 'Unknown',
                        'relevance': 'High'
                    })
        
        return result
    
    def _create_fallback_parsing_result(self) -> Dict:
        """
        Create a fallback result when parsing agent fails.
        """
        return DEFAULT_PARSING_RESULT
    
    def _deduplicate_search_results(self, search_results: List[Dict]) -> List[Dict]:
        """
        Deduplicate search results based on URL and title.
        
        Args:
            search_results: List of search result dictionaries
            
        Returns:
            List of deduplicated search results
        """
        seen_urls = set()
        seen_titles = set()
        unique_results = []
        
        for result in search_results:
            url = result.get('url', '').lower()
            title = result.get('title', '').lower()
            
            # Skip if we've seen this URL or title before
            if url in seen_urls or title in seen_titles:
                continue
            
            # Add to seen sets
            seen_urls.add(url)
            seen_titles.add(title)
            unique_results.append(result)
        
        print(f"🔍 Deduplicated {len(search_results)} results to {len(unique_results)} unique results")
        return unique_results
    
    async def _extract_policy_documents(self, search_results: List[Dict]) -> List[Dict]:
        """
        Extract policy documents from search results by analyzing each result.
        
        Args:
            search_results: List of search result dictionaries
            
        Returns:
            List of extracted policy documents with detailed information
        """
        policy_documents = []
        
        for result in search_results:
            try:
                # Analyze the document using GPT
                analysis_result = await self._analyze_document_with_gpt(result)
                if analysis_result:
                    policy_documents.append(analysis_result)
                    print(f"✅ Policy document parsing successful for: {result.get('title', 'Unknown')}")
            except Exception as e:
                print(f"❌ Error analyzing document {result.get('title', 'Unknown')}: {e}")
                continue
        
        print(f"📊 Successfully parsed {len(policy_documents)} policy documents")
        return policy_documents
    
    async def _analyze_document_with_gpt(self, search_result: Dict) -> Optional[Dict]:
        """
        Analyze a single document using GPT to extract policy information.
        
        Args:
            search_result: Single search result dictionary
            
        Returns:
            Dictionary with extracted policy information or None if analysis fails
        """
        try:
            # Create analysis prompt
            prompt = create_medicare_document_analysis_prompt(search_result)
            
            # Get GPT response
            response = await self._get_gpt_response(prompt)
            if not response:
                return None
            
            # Parse the response
            analysis_result = self._parse_document_analysis_response(response, search_result)
            return analysis_result
            
        except Exception as e:
            print(f"❌ Error in document analysis: {e}")
            return None
    
    def _parse_document_analysis_response(self, response, search_result: Dict) -> Dict:
        """
        Parse the GPT response for document analysis.
        
        Args:
            response: GPT response object
            search_result: Original search result
            
        Returns:
            Dictionary with parsed analysis results
        """
        try:
            # Handle both GPT-5 and GPT-4o responses
            if hasattr(response, 'output_text'):
                content = response.output_text  # GPT-5 format
            elif hasattr(response, 'choices') and len(response.choices) > 0:
                content = response.choices[0].message.content  # GPT-4o format
            else:
                print("❌ Unknown response format")
                return self._create_default_document_info(search_result)
            
            # Try to extract JSON from the response
            if '{' in content and '}' in content:
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx]
                    try:
                        result = json.loads(json_str)
                        # Add the original search result info
                        result['original_search_result'] = search_result
                        return result
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error in document analysis: {e}")
            
            # Fallback to default document info
            return self._create_default_document_info(search_result)
            
        except Exception as e:
            print(f"❌ Error parsing document analysis response: {e}")
            return self._create_default_document_info(search_result)
    
    def _create_default_document_info(self, search_result: Dict) -> Dict:
        """
        Create default document information when analysis fails.
        
        Args:
            search_result: Original search result
            
        Returns:
            Dictionary with default document information
        """
        return {
            'title': search_result.get('title', 'Unknown'),
            'url': search_result.get('url', ''),
            'source': search_result.get('source', 'Unknown'),
            'document_type': 'policy_document',
            'requirements': ['Standard medical necessity criteria apply'],
            'evidence_basis': 'Based on clinical studies and medical literature',
            'clinical_criteria': ['Appropriate clinical indication'],
            'coverage_status': 'Covered with prior authorization',
            'cpt_codes': [],
            'documentation_needed': ['Clinical documentation'],
            'limitations': ['Standard policy limitations apply'],
            'effective_date': 'N/A',
            'revision_date': 'N/A',
            'original_search_result': search_result
        }

# Global instance
enhanced_insurance_analyzer = EnhancedInsuranceAnalysis()

def run_automation_workflow(auth_id: str, auth_data: dict, background_tasks: dict, automation_details: dict, db) -> dict:
    """
    Run the complete automation workflow for prior authorization.
    
    Args:
        auth_id: The authorization ID
        auth_data: The authorization data
        background_tasks: Dictionary to store background task status
        automation_details: Dictionary to store detailed automation results
        db: Database interface
    
    Returns:
        dict: Result of the automation workflow
    """
    try:
        # Extract basic information
        cpt_code = auth_data.get('cpt_code', '81455')
        insurance_provider = auth_data.get('insurance_provider', 'Original Medicare')
        service_type = 'genetic testing'
        
        # Get patient context
        patient_mrn = auth_data.get('patient_mrn', '')
        patient_context = _build_patient_context(patient_mrn, auth_data)
        
        # Update progress
        background_tasks[auth_id]['progress'] = 10
        background_tasks[auth_id]['message'] = 'Determining MAC jurisdiction...'
        background_tasks[auth_id]['last_update'] = datetime.now()
        
        # Determine MAC jurisdiction
        mac_jurisdiction = None
        if any(medicare_term in insurance_provider.lower() 
               for medicare_term in ['medicare', 'original medicare', 'cms']):
            patient_state = patient_context.get('patient_state', 'CT')
            mac_jurisdiction = enhanced_insurance_analyzer.get_mac_jurisdiction(patient_state)
        
        # Update progress
        background_tasks[auth_id]['progress'] = 20
        background_tasks[auth_id]['message'] = 'Generating search queries...'
        background_tasks[auth_id]['last_update'] = datetime.now()
        
        # Generate search queries
        search_queries = enhanced_insurance_analyzer._generate_medicare_search_queries(
            cpt_code, insurance_provider, service_type, mac_jurisdiction
        )
        
        # Take top 5 queries to avoid timeouts
        important_queries = search_queries[:5]
        
        # Update progress
        background_tasks[auth_id]['progress'] = 30
        background_tasks[auth_id]['message'] = f'Running {len(important_queries)} searches...'
        background_tasks[auth_id]['last_update'] = datetime.now()
        
        # Run searches
        all_search_results = []
        for i, query in enumerate(important_queries):
            try:
                background_tasks[auth_id]['message'] = f'Searching: {query[:50]}...'
                background_tasks[auth_id]['last_update'] = datetime.now()
                
                # Update current activity
                automation_details[auth_id]['current_activity'] = f'Searching: {query}'
                
                search_results = asyncio.run(enhanced_insurance_analyzer._gpt_search(None, query))
                if search_results:
                    all_search_results.extend(search_results)
                    
                    # Store search results with query context
                    automation_details[auth_id]['search_results'].append({
                        'query': query,
                        'results': search_results,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Add citations
                    for result in search_results:
                        if result.get('url') and result.get('title'):
                            automation_details[auth_id]['citations'].append({
                                'source': result.get('source', 'Unknown'),
                                'url': result.get('url'),
                                'title': result.get('title'),
                                'relevance': result.get('relevance', 0),
                                'type': 'search_result'
                            })
                
                background_tasks[auth_id]['progress'] = 30 + (i * 10)
                background_tasks[auth_id]['last_update'] = datetime.now()
                
            except Exception as e:
                print(f"Error in search query '{query}': {e}")
        
        # Update progress
        background_tasks[auth_id]['progress'] = 70
        background_tasks[auth_id]['message'] = 'Processing search results...'
        background_tasks[auth_id]['last_update'] = datetime.now()
        
        # Process and deduplicate results
        unique_results = enhanced_insurance_analyzer._deduplicate_search_results(all_search_results)
        
        # Update progress
        background_tasks[auth_id]['progress'] = 75
        background_tasks[auth_id]['message'] = 'Extracting policy documents...'
        background_tasks[auth_id]['last_update'] = datetime.now()
        
        # Extract policy documents
        automation_details[auth_id]['current_activity'] = 'Extracting policy documents from search results'
        policy_documents = asyncio.run(enhanced_insurance_analyzer._extract_policy_documents(unique_results[:10]))
        automation_details[auth_id]['extracted_documents'] = policy_documents
        
        # Update progress
        background_tasks[auth_id]['progress'] = 80
        background_tasks[auth_id]['message'] = 'Running parsing agent analysis...'
        background_tasks[auth_id]['last_update'] = datetime.now()
        
        # Run parsing agent analysis
        automation_details[auth_id]['current_activity'] = 'Running parsing agent analysis'
        parsing_agent_result = asyncio.run(enhanced_insurance_analyzer._analyze_documents_with_parsing_agent(
            unique_results[:10], patient_context, cpt_code, insurance_provider
        ))
        
        # Store parsing agent results
        automation_details[auth_id]['parsing_agent_results'] = parsing_agent_result
        
        # Update progress
        background_tasks[auth_id]['progress'] = 90
        background_tasks[auth_id]['message'] = 'Analyzing coverage and requirements...'
        background_tasks[auth_id]['last_update'] = datetime.now()
        
        # Analyze coverage and requirements
        coverage_info = asyncio.run(enhanced_insurance_analyzer._analyze_coverage_and_requirements_with_gpt(
            cpt_code, insurance_provider, policy_documents, patient_context, mac_jurisdiction
        ))
        
        # Check patient criteria
        patient_criteria_match = {}
        if patient_context:
            patient_criteria_match = asyncio.run(enhanced_insurance_analyzer._check_patient_criteria_with_gpt(
                coverage_info.requirements, patient_context
            ))
        
        # Generate recommendations
        recommendations = asyncio.run(enhanced_insurance_analyzer._generate_recommendations_with_gpt(
            coverage_info, patient_criteria_match, patient_context
        ))
        
        # Create final result
        final_result = {
            'cpt_code': cpt_code,
            'insurance_provider': insurance_provider,
            'coverage_status': coverage_info.coverage_status,
            'coverage_details': coverage_info.coverage_details,
            'requirements': [
                {
                    'requirement_type': req.requirement_type,
                    'description': req.description,
                    'evidence_basis': req.evidence_basis,
                    'documentation_needed': req.documentation_needed,
                    'clinical_criteria': req.clinical_criteria,
                    'source_document': req.source_document,
                    'confidence_score': req.confidence_score
                }
                for req in coverage_info.requirements
            ],
            'patient_criteria_match': patient_criteria_match,
            'confidence_score': coverage_info.confidence_score,
            'search_sources': unique_results[:10],
            'recommendations': recommendations,
            'mac_jurisdiction': mac_jurisdiction["name"] if mac_jurisdiction else None,
            'ncd_applicable': coverage_info.ncd_applicable if hasattr(coverage_info, 'ncd_applicable') else False,
            'lcd_applicable': coverage_info.lcd_applicable if hasattr(coverage_info, 'lcd_applicable') else False,
            'parsing_agent_result': parsing_agent_result
        }
        
        # Check if automation should pause for clinician input
        workflow_result = _check_automation_continuation(
            auth_id, parsing_agent_result, automation_details, background_tasks, db
        )
        
        if workflow_result['should_pause']:
            return workflow_result
        
        # Continue with form completion
        return _continue_with_form_completion(auth_id, auth_data, automation_details, background_tasks, db)
        
    except Exception as e:
        print(f"Error in automation workflow: {e}")
        return {'error': str(e)}

def _build_patient_context(patient_mrn: str, auth_data: dict) -> dict:
    """
    Build patient context from EHR data.
    """
    patient_context = {}
    
    if patient_mrn:
        try:
            # Import the EHR system
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from backend.mock_ehr_system import MockEHRSystem
            ehr_system = MockEHRSystem()
            ehr_data = ehr_system.get_patient_data(patient_mrn)
            
            # Check for genetic counseling documentation
            has_genetic_counseling = False
            if 'genetics_counseling_and_consent' in ehr_data:
                counseling_data = ehr_data['genetics_counseling_and_consent']
                has_genetic_counseling = (
                    counseling_data.get('genetic_counselor') and 
                    counseling_data.get('counseling_date') and
                    counseling_data.get('risk_assessment_completed', False)
                )
            
            # Check for family history documentation
            has_family_history = False
            if 'family_history' in ehr_data and ehr_data['family_history']:
                has_family_history = len(ehr_data['family_history']) > 0
            
            # Check for clinical indication documentation
            has_clinical_indication = False
            if 'clinical_notes' in ehr_data and ehr_data['clinical_notes']:
                clinical_notes = ehr_data['clinical_notes']
                has_clinical_indication = any(
                    'medical necessity' in note.get('content', '').lower() or
                    'clinical indication' in note.get('content', '').lower()
                    for note in clinical_notes
                )
            
            patient_context = {
                'has_genetic_counseling': has_genetic_counseling,
                'has_family_history': has_family_history,
                'has_clinical_indication': has_clinical_indication,
                'provider_credentials_valid': True,
                'patient_state': auth_data.get('patient_state', 'CT')
            }
            
            print(f"🔍 Patient context for {patient_mrn}:")
            print(f"  - Has genetic counseling: {has_genetic_counseling}")
            print(f"  - Has family history: {has_family_history}")
            print(f"  - Has clinical indication: {has_clinical_indication}")
            
        except Exception as e:
            print(f"Error getting EHR data: {e}")
            patient_context = {
                'has_genetic_counseling': False,
                'has_family_history': False,
                'has_clinical_indication': True,
                'provider_credentials_valid': True,
                'patient_state': auth_data.get('patient_state', 'CT')
            }
    
    return patient_context

def _check_automation_continuation(auth_id: str, parsing_agent_result: dict, automation_details: dict, background_tasks: dict, db) -> dict:
    """
    Check if automation should continue or pause for clinician input.
    """
    print(f"🔍 Parsing agent result: {parsing_agent_result}")
    print(f"🔍 Request validation: {parsing_agent_result.get('request_validation', {})}")
    print(f"🔍 Is valid: {parsing_agent_result.get('request_validation', {}).get('is_valid', True)}")
    
    # Check the condition more explicitly
    has_parsing_result = bool(parsing_agent_result)
    is_valid = parsing_agent_result.get('request_validation', {}).get('is_valid', True)
    should_pause = has_parsing_result and not is_valid
    
    print(f"🔍 Condition check:")
    print(f"  - Has parsing result: {has_parsing_result}")
    print(f"  - Is valid: {is_valid}")
    print(f"  - Should pause: {should_pause}")
    print(f"  - Parsing agent result type: {type(parsing_agent_result)}")
    print(f"  - Parsing agent result keys: {list(parsing_agent_result.keys()) if isinstance(parsing_agent_result, dict) else 'Not a dict'}")
    print(f"  - Request validation type: {type(parsing_agent_result.get('request_validation', {}))}")
    print(f"  - Is valid type: {type(is_valid)}")
    print(f"  - Is valid value: {repr(is_valid)}")
    
    if should_pause:
        print(f"🛑 PAUSING AUTOMATION - Request is invalid")
        # Request is invalid - use parsing agent's clinician message
        clinician_message = parsing_agent_result.get('clinician_message', '')
        missing_documents = parsing_agent_result.get('request_validation', {}).get('missing_documents', [])
        
        print(f"🔍 Clinician message: {clinician_message[:100]}...")
        print(f"🔍 Missing documents: {missing_documents}")
        
        # Store the message and missing requirements
        automation_details[auth_id]['clinician_message'] = clinician_message
        automation_details[auth_id]['missing_requirements'] = missing_documents
        automation_details[auth_id]['needs_clinician_input'] = True
        automation_details[auth_id]['parsing_agent_results'] = parsing_agent_result
        
        # Update status to indicate waiting for clinician input
        background_tasks[auth_id]['progress'] = 50
        background_tasks[auth_id]['message'] = 'Waiting for clinician input - requirements not met'
        background_tasks[auth_id]['is_running'] = False
        background_tasks[auth_id]['last_update'] = datetime.now()
        
        # Update database status to 'review' (will be changed to 'deferred' when message is sent)
        db.update_prior_auth_status(auth_id, 'review')
        print(f"🛑 AUTOMATION PAUSED - Waiting for clinician input")
        
        return {
            'should_pause': True,
            'clinician_message': clinician_message,
            'missing_documents': missing_documents
        }
    
    print(f"✅ CONTINUING AUTOMATION - Request is valid")
    return {'should_pause': False}

def _continue_with_form_completion(auth_id: str, auth_data: dict, automation_details: dict, background_tasks: dict, db) -> dict:
    """
    Continue automation with form completion.
    """
    # Step 2: Form Completion (only if requirements are met)
    background_tasks[auth_id]['current_step'] = 2
    background_tasks[auth_id]['message'] = 'Coverage analysis complete. Starting form completion...'
    background_tasks[auth_id]['progress'] = 50
    background_tasks[auth_id]['last_update'] = datetime.now()
    
    # Final check - don't complete if there are missing requirements
    if automation_details[auth_id].get('needs_clinician_input', False):
        print(f"🛑 PREVENTING COMPLETION - Clinician input still needed")
        background_tasks[auth_id]['progress'] = 50
        background_tasks[auth_id]['message'] = 'Waiting for clinician input - requirements not met'
        background_tasks[auth_id]['is_running'] = False
        background_tasks[auth_id]['last_update'] = datetime.now()
        return {'should_pause': True}
    
    # Simulate form completion
    form_result = {
        'status': 'completed',
        'form_data': automation_details[auth_id].get('form_data', {}),
        'message': 'Form completion simulated successfully'
    }
    
    # Store results and mark as complete
    background_tasks[auth_id]['results']['form'] = form_result
    background_tasks[auth_id]['current_step'] = 3
    background_tasks[auth_id]['message'] = 'Automation complete!'
    background_tasks[auth_id]['progress'] = 100
    background_tasks[auth_id]['is_running'] = False
    background_tasks[auth_id]['last_update'] = datetime.now()
    
    # Update database status
    db.update_prior_auth_status(auth_id, 'completed')
    
    return {'should_pause': False, 'form_result': form_result}
