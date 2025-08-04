import requests
import xml.etree.ElementTree as ET
import time
from typing import List, Dict, Optional, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
from dotenv import load_dotenv

load_dotenv()

class PubMedService:
    def __init__(self):
        self.email = os.getenv("NCBI_EMAIL", "")
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        
        # Set up session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _is_valid_xml_response(self, response_content: bytes) -> bool:
        """Check if the response content is valid XML"""
        try:
            content_str = response_content.decode('utf-8', errors='ignore').strip()
            return content_str.startswith('<?xml') or content_str.startswith('<')
        except Exception:
            return False
    
    def _is_maintenance_page(self, response_content: bytes) -> bool:
        """Check if the response is a maintenance page"""
        try:
            content_str = response_content.decode('utf-8', errors='ignore').lower()
            return any(keyword in content_str for keyword in ['maintenance', 'down_bethesda', '302 found', 'document has moved'])
        except Exception:
            return False
    
    def search_papers(self, query: str, max_results: int = 100) -> Tuple[str, List[str], int]:
        """
        Search PubMed for papers and return query translation, PMIDs, and total count
        """
        print(f"🔍 Searching PubMed for: {query}")
        
        # First, get total count and translation
        params = {
            'db': 'pubmed',
            'term': query,
            'retmode': 'xml',
            'retmax': 0,  # Just get count and translation
            'sort': 'relevance'
        }
        
        if self.email and '@' in self.email and '.' in self.email:
            params['email'] = self.email
        
        try:
            response = self.session.get(f"{self.base_url}/esearch.fcgi", params=params, timeout=30)
            response.raise_for_status()
            
            if self._is_maintenance_page(response.content):
                print("❌ NCBI E-utilities API is currently under maintenance")
                return query, [], 0
            
            if not self._is_valid_xml_response(response.content):
                print(f"❌ API returned non-XML response")
                return query, [], 0
            
            root = ET.fromstring(response.content)
        except Exception as e:
            print(f"❌ Error during initial search: {e}")
            return query, [], 0
        
        # Get translation and count
        translation = root.findtext('.//QueryTranslation') or query
        count_elem = root.find('.//Count')
        total_count = int(count_elem.text) if count_elem is not None else 0
        
        print(f"📊 Found {total_count} papers total")
        print(f"🔎 Query translation: {translation}")
        
        if total_count == 0:
            return translation, [], 0
        
        # Get PMIDs (limited by max_results)
        all_pmids = []
        batch_size = min(1000, max_results)  # PubMed's max per request or user's limit
        
        print(f"📄 Retrieving up to {max_results} PMIDs...")
        
        for start in range(0, min(total_count, max_results), batch_size):
            params = {
                'db': 'pubmed',
                'term': query,
                'retmode': 'xml',
                'retstart': start,
                'retmax': min(batch_size, max_results - start),
                'sort': 'relevance'
            }
            
            if self.email and '@' in self.email and '.' in self.email:
                params['email'] = self.email
            
            try:
                response = self.session.get(f"{self.base_url}/esearch.fcgi", params=params, timeout=30)
                response.raise_for_status()
                
                if self._is_maintenance_page(response.content) or not self._is_valid_xml_response(response.content):
                    continue
                
                root = ET.fromstring(response.content)
                batch_pmids = [id_elem.text for id_elem in root.findall('.//IdList/Id')]
                all_pmids.extend(batch_pmids)
                
                print(f"📄 Retrieved PMIDs {start+1}-{start+len(batch_pmids)}")
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Error retrieving batch: {e}")
                continue
        
        print(f"✅ Retrieved {len(all_pmids)} PMIDs")
        return translation, all_pmids, total_count
    
    def fetch_paper_details(self, pmids: List[str]) -> List[Dict]:
        """
        Fetch detailed information for a list of PMIDs
        """
        if not pmids:
            return []
        
        print(f"📖 Fetching details for {len(pmids)} papers...")
        
        papers = []
        batch_size = 20  # Process in smaller batches
        
        for i in range(0, len(pmids), batch_size):
            batch_pmids = pmids[i:i + batch_size]
            batch_papers = self._fetch_batch_details(batch_pmids)
            papers.extend(batch_papers)
            time.sleep(0.1)  # Rate limiting
        
        print(f"✅ Retrieved details for {len(papers)} papers")
        return papers
    
    def _fetch_batch_details(self, pmids: List[str]) -> List[Dict]:
        """Fetch details for a batch of PMIDs"""
        if not pmids:
            return []
        
        params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml',
            'rettype': 'abstract'
        }
        
        if self.email and '@' in self.email and '.' in self.email:
            params['email'] = self.email
        
        try:
            response = self.session.get(f"{self.base_url}/efetch.fcgi", params=params, timeout=30)
            response.raise_for_status()
            
            if self._is_maintenance_page(response.content) or not self._is_valid_xml_response(response.content):
                return []
            
            root = ET.fromstring(response.content)
            papers = []
            
            for article_elem in root.findall('.//PubmedArticle'):
                paper = self._parse_article_xml(article_elem)
                if paper:
                    papers.append(paper)
            
            return papers
            
        except Exception as e:
            print(f"❌ Error fetching batch details: {e}")
            return []
    
    def _parse_article_xml(self, article_elem) -> Optional[Dict]:
        """Parse individual article XML element into structured dictionary"""
        try:
            paper = {}
            
            # Extract PMID
            pmid_elem = article_elem.find('.//PMID')
            paper['pmid'] = pmid_elem.text if pmid_elem is not None else 'Unknown'
            
            # Extract title
            title_elem = article_elem.find('.//ArticleTitle')
            paper['title'] = title_elem.text if title_elem is not None else 'No title available'
            
            # Extract abstract
            abstract_texts = []
            for abstract_elem in article_elem.findall('.//AbstractText'):
                label = abstract_elem.get('Label', '')
                text = abstract_elem.text if abstract_elem.text else ''
                if label:
                    abstract_texts.append(f"{label}: {text}")
                else:
                    abstract_texts.append(text)
            
            paper['abstract'] = ' '.join(abstract_texts) if abstract_texts else 'No abstract available'
            
            # Extract authors
            authors = []
            for author_elem in article_elem.findall('.//Author'):
                lastname_elem = author_elem.find('LastName')
                forename_elem = author_elem.find('ForeName')
                
                if lastname_elem is not None:
                    lastname = lastname_elem.text
                    forename = forename_elem.text if forename_elem is not None else ''
                    authors.append(f"{forename} {lastname}".strip())
            
            paper['authors'] = ', '.join(authors) if authors else 'Authors not available'
            
            # Extract DOI
            doi_elem = article_elem.find('.//ELocationID[@EIdType="doi"]')
            paper['doi'] = doi_elem.text if doi_elem is not None else None
            
            # Extract publication date
            pub_date_elem = article_elem.find('.//PubDate')
            if pub_date_elem is not None:
                year_elem = pub_date_elem.find('Year')
                month_elem = pub_date_elem.find('Month')
                day_elem = pub_date_elem.find('Day')
                
                year = year_elem.text if year_elem is not None else ''
                month = month_elem.text if month_elem is not None else ''
                day = day_elem.text if day_elem is not None else ''
                
                paper['publication_date'] = f"{year}-{month}-{day}".strip('-')
            else:
                paper['publication_date'] = 'Date not available'
            
            # Extract MeSH terms
            mesh_terms = []
            for mesh_elem in article_elem.findall('.//MeshHeading/DescriptorName'):
                if mesh_elem.text:
                    mesh_terms.append(mesh_elem.text)
            paper['mesh_terms'] = mesh_terms
            
            # Generate PDF link (if DOI is available)
            if paper.get('doi'):
                paper['pdf_link'] = f"https://doi.org/{paper['doi']}"
            else:
                paper['pdf_link'] = f"https://pubmed.ncbi.nlm.nih.gov/{paper['pmid']}/"
            
            return paper
            
        except Exception as e:
            print(f"❌ Error parsing article XML: {str(e)}")
            return None