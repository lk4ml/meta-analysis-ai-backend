#!/usr/bin/env python3
"""
Demo script to test the Meta-Analysis AI Backend API
This script demonstrates the complete workflow from research question to final report
"""

import requests
import json
import time
import sys
from typing import Dict, Any

class MetaAnalysisDemo:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.question_id = None
        
    def test_health(self) -> bool:
        """Test if the API is running"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ API is healthy and running")
                return True
            else:
                print(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Could not connect to API: {e}")
            return False
    
    def create_research_question(self) -> Dict[str, Any]:
        """Step 1: Create a research question with PICO criteria"""
        print("\n🔬 Step 1: Creating Research Question")
        
        payload = {
            "question": "Does Pembrolizumab improve survival in elderly lung cancer patients?",
            "pico": {
                "population": "Elderly lung cancer patients (age >65)",
                "intervention": "Pembrolizumab (PD-1 inhibitor)",
                "comparison": "Standard chemotherapy or placebo",
                "outcome": "Overall survival and progression-free survival"
            }
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/research-question",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                self.question_id = data["question_id"]
                print(f"✅ Research question created with ID: {self.question_id}")
                print(f"📝 Original: {payload['question']}")
                print(f"🔄 Rephrased: {data['rephrased_question']}")
                return data
            else:
                print(f"❌ Failed to create research question: {response.status_code}")
                print(f"Response: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Error creating research question: {e}")
            return {}
    
    def search_pubmed(self, max_results: int = 20) -> Dict[str, Any]:
        """Step 2: Search PubMed for relevant papers"""
        print(f"\n🔍 Step 2: Searching PubMed (max {max_results} results)")
        
        if not self.question_id:
            print("❌ No question ID available")
            return {}
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/pubmed-search",
                params={
                    "question_id": self.question_id,
                    "max_results": max_results
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {len(data['papers'])} papers (out of {data['total_count']} total)")
                print(f"🔎 Query translation: {data['query_translation'][:100]}...")
                
                # Show first few papers
                for i, paper in enumerate(data['papers'][:3]):
                    print(f"  📄 {i+1}. PMID: {paper['pmid']} - {paper['title'][:80]}...")
                
                return data
            else:
                print(f"❌ Failed to search PubMed: {response.status_code}")
                print(f"Response: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Error searching PubMed: {e}")
            return {}
    
    def screen_papers(self, papers_data: Dict[str, Any]) -> Dict[str, Any]:
        """Step 3: Screen papers using AI"""
        print(f"\n🤖 Step 3: AI Screening Papers")
        
        if not papers_data or not papers_data.get('papers'):
            print("❌ No papers to screen")
            return {}
        
        # Prepare papers for screening (first 10 to avoid long processing)
        papers_to_screen = []
        for paper in papers_data['papers'][:10]:
            papers_to_screen.append({
                "pmid": paper['pmid'],
                "title": paper['title'],
                "abstract": paper['abstract']
            })
        
        payload = {
            "question_id": self.question_id,
            "papers": papers_to_screen
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/screening-columns",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Screened {len(data['screened_papers'])} papers")
                
                # Show screening results
                high_score_papers = [p for p in data['screened_papers'] if p['score'] >= 4.0]
                print(f"📊 Papers with score ≥ 4.0: {len(high_score_papers)}")
                
                for paper in data['screened_papers'][:5]:
                    print(f"  📋 PMID: {paper['pmid']} - Score: {paper['score']}")
                    print(f"      Study Design: {paper['study_design']}, Intervention: {paper['intervention']}")
                
                return data
            else:
                print(f"❌ Failed to screen papers: {response.status_code}")
                print(f"Response: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Error screening papers: {e}")
            return {}
    
    def get_filtered_papers(self, min_score: float = 3.0) -> Dict[str, Any]:
        """Step 4: Get filtered papers above score threshold"""
        print(f"\n📊 Step 4: Getting Filtered Papers (score ≥ {min_score})")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/filtered-papers",
                params={
                    "question_id": self.question_id,
                    "min_score": min_score
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {len(data)} filtered papers")
                
                for paper in data[:3]:
                    print(f"  🎯 PMID: {paper['pmid']} - Score: {paper['score']}")
                
                return {"papers": data}
            else:
                print(f"❌ Failed to get filtered papers: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Error getting filtered papers: {e}")
            return {}
    
    def extract_data(self, filtered_papers: Dict[str, Any]) -> Dict[str, Any]:
        """Step 5: Extract structured data from top papers"""
        print(f"\n📝 Step 5: Extracting Structured Data")
        
        if not filtered_papers or not filtered_papers.get('papers'):
            print("❌ No filtered papers for data extraction")
            return {}
        
        # Extract data from top 5 papers
        paper_ids = [paper['pmid'] for paper in filtered_papers['papers'][:5]]
        
        payload = {
            "paper_ids": paper_ids
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/extract-data",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Extracted data from {len(data['extracted_data'])} papers")
                
                for extraction in data['extracted_data'][:2]:
                    print(f"  📄 PMID: {extraction['pmid']}")
                    print(f"      Study Design: {extraction['study_design'][:50]}...")
                    print(f"      Intervention: {extraction['intervention'][:50]}...")
                
                return data
            else:
                print(f"❌ Failed to extract data: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Error extracting data: {e}")
            return {}
    
    def generate_report(self, format: str = "csv") -> Dict[str, Any]:
        """Step 6: Generate final report"""
        print(f"\n📊 Step 6: Generating {format.upper()} Report")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/generate-report",
                params={
                    "question_id": self.question_id,
                    "format": format,
                    "min_score": 2.0,
                    "include_all": True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Report generated: {data['report_url']}")
                return data
            else:
                print(f"❌ Failed to generate report: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Error generating report: {e}")
            return {}
    
    def preview_report(self) -> Dict[str, Any]:
        """Preview report data before generation"""
        print(f"\n👁 Previewing Report Data")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/report-preview/{self.question_id}",
                params={"min_score": 2.0, "limit": 5}
            )
            
            if response.status_code == 200:
                data = response.json()
                stats = data['statistics']
                print(f"✅ Report Preview:")
                print(f"   📄 Total Papers: {stats['total_papers']}")
                print(f"   🔍 Screened Papers: {stats['screened_papers']}")
                print(f"   📊 Extracted Papers: {stats['extracted_papers']}")
                return data
            else:
                print(f"❌ Failed to preview report: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Error previewing report: {e}")
            return {}
    
    def run_full_demo(self):
        """Run the complete demo workflow"""
        print("🚀 Starting Meta-Analysis AI Backend Demo")
        print("=" * 50)
        
        # Step 0: Health check
        if not self.test_health():
            print("❌ API is not available. Please start the server first.")
            sys.exit(1)
        
        # Step 1: Create research question
        question_data = self.create_research_question()
        if not question_data:
            return
        
        # Step 2: Search PubMed
        papers_data = self.search_pubmed(max_results=15)
        if not papers_data:
            return
        
        # Step 3: Screen papers
        screening_data = self.screen_papers(papers_data)
        if not screening_data:
            return
        
        # Step 4: Get filtered papers
        filtered_papers = self.get_filtered_papers(min_score=2.5)
        if not filtered_papers:
            return
        
        # Step 5: Extract data
        extraction_data = self.extract_data(filtered_papers)
        if not extraction_data:
            return
        
        # Step 6: Preview report
        self.preview_report()
        
        # Step 7: Generate reports
        csv_report = self.generate_report("csv")
        excel_report = self.generate_report("xlsx")
        
        print("\n🎉 Demo Completed Successfully!")
        print("=" * 50)
        print(f"📋 Question ID: {self.question_id}")
        print(f"📄 Papers Found: {papers_data.get('total_count', 0)}")
        print(f"🔍 Papers Screened: {len(screening_data.get('screened_papers', []))}")
        print(f"📊 Data Extracted: {len(extraction_data.get('extracted_data', []))}")
        if csv_report:
            print(f"📊 CSV Report: {csv_report.get('report_url', 'N/A')}")
        if excel_report:
            print(f"📊 Excel Report: {excel_report.get('report_url', 'N/A')}")

def main():
    """Main function to run the demo"""
    # You can change the base_url if your API is running on a different host/port
    demo = MetaAnalysisDemo(base_url="http://localhost:8000")
    
    try:
        demo.run_full_demo()
    except KeyboardInterrupt:
        print("\n\n❌ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")

if __name__ == "__main__":
    main()