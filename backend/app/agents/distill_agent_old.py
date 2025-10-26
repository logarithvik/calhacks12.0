"""
Distillation Agent - Extracts structured information from clinical trial protocols

This agent should:
1. Parse the raw protocol text
2. Extract key information:
   - Study title and phase
   - Duration and timeline
   - Inclusion/exclusion criteria
   - Study design and methodology
   - Biological mechanism
   - Expected side effects
   - Visit schedule
   - Primary and secondary endpoints
3. Return structured data in a standardized format
"""

from typing import Dict, Any


def run_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured information from clinical trial protocol text.
    
    Args:
        input_data: Dictionary containing:
            - protocol_text: str - Raw text from the protocol document
            - trial_id: int - Database ID of the trial
    
    Returns:
        Dictionary containing extracted information:
            - study_title: str
            - phase: str
            - duration: str
            - inclusion_criteria: List[str]
            - exclusion_criteria: List[str]
            - study_design: str
            - biological_mechanism: str
            - side_effects: List[str]
            - visit_schedule: List[Dict]
            - endpoints: Dict
    
    TODO: ADD AGENT LOGIC HERE
    - Implement LLM-based extraction (e.g., using OpenAI GPT-4, Claude, etc.)
    - Use prompt engineering to extract structured data
    - Consider using function calling or structured outputs
    - Add error handling and validation
    
    Example implementation approaches:
    1. Use OpenAI with function calling:
       ```python
       from openai import OpenAI
       client = OpenAI(api_key=settings.openai_api_key)
       response = client.chat.completions.create(
           model="gpt-4",
           messages=[{"role": "user", "content": f"Extract info from: {protocol_text}"}],
           functions=[...],  # Define extraction schema
       )
       ```
    
    2. Use Anthropic Claude with structured prompts:
       ```python
       from anthropic import Anthropic
       client = Anthropic(api_key=settings.anthropic_api_key)
       message = client.messages.create(...)
       ```
    
    3. Use local models with LangChain:
       ```python
       from langchain.chains import create_extraction_chain
       chain = create_extraction_chain(schema, llm)
       result = chain.run(protocol_text)
       ```
    """
    
    protocol_text = input_data.get("protocol_text", "")
    trial_id = input_data.get("trial_id")
    
    # MOCK IMPLEMENTATION - Replace with real AI logic
    mock_result = {
        "study_title": "Example Phase II Clinical Trial",
        "phase": "Phase II",
        "duration": "12 months",
        "inclusion_criteria": [
            "Age 18-65 years",
            "Confirmed diagnosis of condition X",
            "Adequate organ function"
        ],
        "exclusion_criteria": [
            "Pregnancy or breastfeeding",
            "Previous treatment with similar agents",
            "Severe cardiovascular disease"
        ],
        "study_design": "Randomized, double-blind, placebo-controlled trial with 2:1 randomization",
        "biological_mechanism": "The investigational drug targets specific protein pathways involved in disease progression",
        "side_effects": [
            "Nausea (mild to moderate)",
            "Fatigue",
            "Headache",
            "Potential liver enzyme elevation"
        ],
        "visit_schedule": [
            {"visit": "Screening", "day": -7, "procedures": ["Blood work", "Physical exam"]},
            {"visit": "Baseline", "day": 0, "procedures": ["Randomization", "First dose"]},
            {"visit": "Week 4", "day": 28, "procedures": ["Safety labs", "Efficacy assessment"]},
            {"visit": "Week 12", "day": 84, "procedures": ["Final assessment", "Follow-up"]}
        ],
        "endpoints": {
            "primary": "Change in disease severity score at 12 weeks",
            "secondary": ["Quality of life measures", "Safety and tolerability", "Biomarker changes"]
        },
        "simple_summary": f"This is a 12-month study testing a new treatment. Participants will have {len(mock_result['visit_schedule'])} clinic visits and receive either the study drug or placebo."
    }
    
    return mock_result


def simplify_for_patients(extracted_data: Dict[str, Any]) -> str:
    """
    Convert technical medical information into patient-friendly language.
    
    TODO: ADD SIMPLIFICATION LOGIC HERE
    - Use LLM to translate medical jargon
    - Create easy-to-understand explanations
    - Adjust reading level (e.g., 8th grade)
    """
    
    # MOCK IMPLEMENTATION
    simple_text = f"""
# What This Study Is About

**Study Name:** {extracted_data.get('study_title', 'Clinical Trial')}

## Timeline
This study will last {extracted_data.get('duration', 'several months')}.

## What We're Testing
{extracted_data.get('biological_mechanism', 'We are testing a new treatment approach.')}

## Who Can Join
You may be eligible if you:
{chr(10).join(f'- {criterion}' for criterion in extracted_data.get('inclusion_criteria', []))}

## What to Expect
You'll need to visit the clinic {len(extracted_data.get('visit_schedule', []))} times during the study.

## Possible Side Effects
{chr(10).join(f'- {effect}' for effect in extracted_data.get('side_effects', []))}

## What We're Measuring
We'll track: {extracted_data.get('endpoints', {}).get('primary', 'health outcomes')}
"""
    
    return simple_text
