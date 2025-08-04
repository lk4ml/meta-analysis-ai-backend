import openai
import anthropic
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

class AIService:
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize OpenAI if API key is available
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key != "your_openai_api_key_here":
            openai.api_key = openai_key
            self.openai_client = openai
        
        # Initialize Anthropic if API key is available
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key and anthropic_key != "your_anthropic_api_key_here":
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
    
    def rephrase_research_question(self, question: str, pico: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Rephrase research question for better specificity using AI
        """
        if pico:
            prompt = f"""
            Rephrase the following research question to be more specific and suitable for PubMed search.
            
            Original question: {question}
            
            PICO criteria provided:
            - Population: {pico.get('population', 'Not specified')}
            - Intervention: {pico.get('intervention', 'Not specified')}
            - Comparison: {pico.get('comparison', 'Not specified')}
            - Outcome: {pico.get('outcome', 'Not specified')}
            
            Please provide:
            1. A rephrased question that incorporates the PICO elements more clearly
            2. Suggested MeSH terms for PubMed search (focus on the main concepts, not study types)
            
            Format your response as:
            REPHRASED: [your rephrased question]
            MESH_TERMS: [comma-separated list of suggested MeSH terms]
            """
        else:
            prompt = f"""
            Rephrase the following research question to be more specific and suitable for PubMed search.
            
            Original question: {question}
            
            Since no PICO criteria were provided, please:
            1. Suggest specific PICO elements that could improve the question
            2. Provide a rephrased question
            3. Suggest MeSH terms for PubMed search (focus on the main concepts, not study types)
            
            Format your response as:
            SUGGESTED_PICO:
            - Population: [suggestion]
            - Intervention: [suggestion]
            - Comparison: [suggestion]
            - Outcome: [suggestion]
            
            REPHRASED: [your rephrased question]
            MESH_TERMS: [comma-separated list of suggested MeSH terms]
            """
        
        try:
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.3
                )
                ai_response = response.choices[0].message.content
            elif self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                ai_response = response.content[0].text
            else:
                # Fallback for demo purposes
                ai_response = f"REPHRASED: {question} - systematic review and meta-analysis\nMESH_TERMS: systematic review, meta-analysis, clinical trial"
            
            return self._parse_ai_response(ai_response, question, pico)
            
        except Exception as e:
            print(f"AI service error: {e}")
            # Fallback response - don't add restrictive systematic review terms
            return {
                "rephrased_question": question,  # Use original question without restrictive terms
                "pico_suggestions": pico if pico else {
                    "population": "Please specify target population",
                    "intervention": "Please specify intervention",
                    "comparison": "Please specify comparison",
                    "outcome": "Please specify outcome measures"
                },
                "mesh_terms": []
            }
    
    def _parse_ai_response(self, response: str, original_question: str, pico: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse AI response into structured format"""
        result = {
            "rephrased_question": original_question,
            "pico_suggestions": pico,
            "mesh_terms": []
        }
        
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('REPHRASED:'):
                result["rephrased_question"] = line.replace('REPHRASED:', '').strip()
            elif line.startswith('MESH_TERMS:'):
                mesh_terms = line.replace('MESH_TERMS:', '').strip()
                result["mesh_terms"] = [term.strip() for term in mesh_terms.split(',')]
            elif line.startswith('SUGGESTED_PICO:') and not pico:
                # Parse PICO suggestions
                pico_suggestions = {}
                idx = lines.index(line)
                for i in range(idx + 1, min(idx + 5, len(lines))):
                    if lines[i].strip().startswith('- Population:'):
                        pico_suggestions["population"] = lines[i].replace('- Population:', '').strip()
                    elif lines[i].strip().startswith('- Intervention:'):
                        pico_suggestions["intervention"] = lines[i].replace('- Intervention:', '').strip()
                    elif lines[i].strip().startswith('- Comparison:'):
                        pico_suggestions["comparison"] = lines[i].replace('- Comparison:', '').strip()
                    elif lines[i].strip().startswith('- Outcome:'):
                        pico_suggestions["outcome"] = lines[i].replace('- Outcome:', '').strip()
                result["pico_suggestions"] = pico_suggestions
        
        return result
    
    def screen_papers(self, papers: List[Dict[str, Any]], research_question: str) -> List[Dict[str, Any]]:
        """
        Screen papers using AI to generate screening columns
        """
        screened_papers = []
        
        for paper in papers:
            try:
                prompt = f"""
                Based on the research question and paper details below, please evaluate this paper for inclusion in a systematic review.
                
                Research Question: {research_question}
                
                Paper Details:
                Title: {paper.get('title', 'N/A')}
                Abstract: {paper.get('abstract', 'N/A')[:1000]}...
                
                Please rate each criterion as "Yes", "Maybe", or "No":
                
                1. Study Design: Is this an appropriate study design (RCT, cohort, case-control, etc.)?
                2. Intervention: Does the study evaluate the relevant intervention?
                3. Population: Does the study include the target population?
                4. Outcomes: Does the study measure relevant outcomes?
                5. Treatment Characteristics: Are treatment details adequately described?
                
                Format your response as:
                STUDY_DESIGN: [Yes/Maybe/No]
                INTERVENTION: [Yes/Maybe/No]
                POPULATION: [Yes/Maybe/No]
                OUTCOMES: [Yes/Maybe/No]
                TREATMENT_CHARACTERISTICS: [Yes/Maybe/No]
                """
                
                if self.openai_client:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=200,
                        temperature=0.1
                    )
                    ai_response = response.choices[0].message.content
                elif self.anthropic_client:
                    response = self.anthropic_client.messages.create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=200,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    ai_response = response.content[0].text
                else:
                    # Fallback for demo
                    ai_response = "STUDY_DESIGN: Maybe\nINTERVENTION: Yes\nPOPULATION: Maybe\nOUTCOMES: Yes\nTREATMENT_CHARACTERISTICS: Maybe"
                
                screening_result = self._parse_screening_response(ai_response, paper.get('pmid', ''))
                screened_papers.append(screening_result)
                
            except Exception as e:
                print(f"Error screening paper {paper.get('pmid', 'unknown')}: {e}")
                # Fallback screening
                screened_papers.append({
                    "pmid": paper.get('pmid', ''),
                    "study_design": "Maybe",
                    "intervention": "Maybe",
                    "population": "Maybe",
                    "outcomes": "Maybe",
                    "treatment_characteristics": "Maybe",
                    "score": 2.5
                })
        
        return screened_papers
    
    def _parse_screening_response(self, response: str, pmid: str) -> Dict[str, Any]:
        """Parse AI screening response"""
        result = {
            "pmid": pmid,
            "study_design": "Maybe",
            "intervention": "Maybe",
            "population": "Maybe",
            "outcomes": "Maybe",
            "treatment_characteristics": "Maybe",
            "score": 0.0
        }
        
        lines = response.split('\n')
        for line in lines:
            line = line.strip().upper()
            if line.startswith('STUDY_DESIGN:'):
                result["study_design"] = line.replace('STUDY_DESIGN:', '').strip()
            elif line.startswith('INTERVENTION:'):
                result["intervention"] = line.replace('INTERVENTION:', '').strip()
            elif line.startswith('POPULATION:'):
                result["population"] = line.replace('POPULATION:', '').strip()
            elif line.startswith('OUTCOMES:'):
                result["outcomes"] = line.replace('OUTCOMES:', '').strip()
            elif line.startswith('TREATMENT_CHARACTERISTICS:'):
                result["treatment_characteristics"] = line.replace('TREATMENT_CHARACTERISTICS:', '').strip()
        
        # Calculate score: Yes=1, Maybe=0.5, No=0
        score = 0.0
        for key in ["study_design", "intervention", "population", "outcomes", "treatment_characteristics"]:
            value = result[key].upper()
            if value == "YES":
                score += 1.0
            elif value == "MAYBE":
                score += 0.5
        
        result["score"] = score
        return result
    
    def extract_data(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract structured meta-analysis data from papers
        """
        extracted_data = []
        
        for paper in papers:
            try:
                prompt = f"""
                Extract the following structured data from this research paper for meta-analysis:
                
                Title: {paper.get('title', 'N/A')}
                Abstract: {paper.get('abstract', 'N/A')[:1500]}...
                
                Please extract:
                1. Study Design (e.g., RCT, cohort study, case-control)
                2. Patient Characteristics (sample size, demographics, inclusion criteria)
                3. Treatment Characteristics (dosage, duration, administration)
                4. Intervention details
                5. Comparison/Control details
                6. Outcomes measured and results
                
                Format as:
                STUDY_DESIGN: [description]
                PATIENT_CHARACTERISTICS: [description]
                TREATMENT_CHARACTERISTICS: [description]
                INTERVENTION: [description]
                COMPARISON: [description]
                OUTCOMES: [description]
                """
                
                if self.openai_client:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=400,
                        temperature=0.1
                    )
                    ai_response = response.choices[0].message.content
                elif self.anthropic_client:
                    response = self.anthropic_client.messages.create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=400,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    ai_response = response.content[0].text
                else:
                    # Fallback for demo
                    ai_response = f"STUDY_DESIGN: Clinical study\nPATIENT_CHARACTERISTICS: Not specified in abstract\nTREATMENT_CHARACTERISTICS: Not specified\nINTERVENTION: {paper.get('title', 'Study intervention')}\nCOMPARISON: Control group\nOUTCOMES: Primary and secondary outcomes measured"
                
                extraction_result = self._parse_extraction_response(ai_response, paper.get('pmid', ''))
                extracted_data.append(extraction_result)
                
            except Exception as e:
                print(f"Error extracting data from paper {paper.get('pmid', 'unknown')}: {e}")
                # Fallback extraction
                extracted_data.append({
                    "pmid": paper.get('pmid', ''),
                    "study_design": "Not specified",
                    "patient_characteristics": "Not specified",
                    "treatment_characteristics": "Not specified",
                    "intervention": paper.get('title', 'Not specified')[:100],
                    "comparison": "Not specified",
                    "outcomes": "Not specified"
                })
        
        return extracted_data
    
    def _parse_extraction_response(self, response: str, pmid: str) -> Dict[str, Any]:
        """Parse AI extraction response"""
        result = {
            "pmid": pmid,
            "study_design": "Not specified",
            "patient_characteristics": "Not specified",
            "treatment_characteristics": "Not specified",
            "intervention": "Not specified",
            "comparison": "Not specified",
            "outcomes": "Not specified"
        }
        
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.upper().startswith('STUDY_DESIGN:'):
                result["study_design"] = line[len('STUDY_DESIGN:'):].strip()
            elif line.upper().startswith('PATIENT_CHARACTERISTICS:'):
                result["patient_characteristics"] = line[len('PATIENT_CHARACTERISTICS:'):].strip()
            elif line.upper().startswith('TREATMENT_CHARACTERISTICS:'):
                result["treatment_characteristics"] = line[len('TREATMENT_CHARACTERISTICS:'):].strip()
            elif line.upper().startswith('INTERVENTION:'):
                result["intervention"] = line[len('INTERVENTION:'):].strip()
            elif line.upper().startswith('COMPARISON:'):
                result["comparison"] = line[len('COMPARISON:'):].strip()
            elif line.upper().startswith('OUTCOMES:'):
                result["outcomes"] = line[len('OUTCOMES:'):].strip()
        
        return result