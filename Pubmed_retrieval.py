import requests
import xml.etree.ElementTree as ET
import pandas as pd
from typing import List, Dict, Optional, Tuple
import time
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class EnhancedPubMedSearcher:
    def __init__(self, email: str = None):
        """
        Initialize PubMed searcher with email for NCBI API access
        
        Args:
            email (str): Email for NCBI API (recommended for higher rate limits)
        """
        self.email = email
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
        """
        Check if the response content is valid XML
        
        Args:
            response_content (bytes): Response content from API
            
        Returns:
            bool: True if valid XML, False otherwise
        """
        try:
            content_str = response_content.decode('utf-8', errors='ignore').strip()
            return content_str.startswith('<?xml') or content_str.startswith('<')
        except Exception:
            return False
            
    def _is_maintenance_page(self, response_content: bytes) -> bool:
        """
        Check if the response is a maintenance page
        
        Args:
            response_content (bytes): Response content from API
            
        Returns:
            bool: True if maintenance page, False otherwise
        """
        try:
            content_str = response_content.decode('utf-8', errors='ignore').lower()
            return any(keyword in content_str for keyword in ['maintenance', 'down_bethesda', '302 found', 'document has moved'])
        except Exception:
            return False
        
    def get_pubmed_query_translation(self, user_question: str) -> Tuple[str, List[str], int]:
        """
        Get PubMed's query translation and all PMIDs
        
        Args:
            user_question (str): User's research question
            
        Returns:
            Tuple[str, List[str], int]: (translation, all_pmids, total_count)
        """
        print(f"🔍 Analyzing question: {user_question}")
        
        # First, get total count and translation
        params = {
            'db': 'pubmed',
            'term': user_question,
            'retmode': 'xml',
            'retmax': 0,  # Just get count and translation
            'sort': 'relevance'
        }
        # Only add email if it's a valid email format
        if self.email and '@' in self.email and '.' in self.email:
            params['email'] = self.email
            
        try:
            response = self.session.get(f"{self.base_url}/esearch.fcgi", params=params, timeout=30)
            response.raise_for_status()
            
            # Check if response is a maintenance page
            if self._is_maintenance_page(response.content):
                print("❌ NCBI E-utilities API is currently under maintenance or unavailable.")
                print("   Please try again later or visit https://eutils.ncbi.nlm.nih.gov/ for status updates.")
                return user_question, [], 0
                
            # Check if response is valid XML
            if not self._is_valid_xml_response(response.content):
                print(f"❌ API returned non-XML response: {response.text[:200]}...")
                return user_question, [], 0
                
            root = ET.fromstring(response.content)
        except requests.RequestException as e:
            print(f"❌ Network error: {e}")
            return user_question, [], 0
        except ET.ParseError as e:
            print(f"❌ XML parsing error: {e}")
            print(f"Response content: {response.text[:500]}...")
            return user_question, [], 0
        
        # Get translation
        translation = root.findtext('.//QueryTranslation')
        if not translation:
            translation = user_question
            
        # Get total count
        count_elem = root.find('.//Count')
        total_count = int(count_elem.text) if count_elem is not None else 0
        
        print(f"📊 Total papers found by PubMed: {total_count}")
        print(f"🔎 PubMed Query Translation:")
        print(f"   {translation}")
        
        if total_count == 0:
            return translation, [], 0
            
        # Now get PMIDs (limited to 1000 for performance, but showing total count)
        all_pmids = []
        batch_size = 1000  # PubMed's max per request
        max_results = 1000  # Limit to 1000 results for performance
        
        print(f"📄 Retrieving first {max_results} PMIDs (out of {total_count} total papers)...")
        
        for start in range(0, min(total_count, max_results), batch_size):
            params = {
                'db': 'pubmed',
                'term': user_question,
                'retmode': 'xml',
                'retstart': start,
                'retmax': min(batch_size, max_results - start),
                'sort': 'relevance'
            }
            # Only add email if it's a valid email format
            if self.email and '@' in self.email and '.' in self.email:
                params['email'] = self.email
                
            try:
                response = self.session.get(f"{self.base_url}/esearch.fcgi", params=params, timeout=30)
                response.raise_for_status()
                
                # Check if response is a maintenance page
                if self._is_maintenance_page(response.content):
                    print("❌ NCBI E-utilities API is currently under maintenance or unavailable.")
                    print("   Please try again later or visit https://eutils.ncbi.nlm.nih.gov/ for status updates.")
                    return translation, all_pmids, total_count
                    
                # Check if response is valid XML
                if not self._is_valid_xml_response(response.content):
                    print(f"❌ API returned non-XML response: {response.text[:200]}...")
                    continue
                    
                root = ET.fromstring(response.content)
            except requests.RequestException as e:
                print(f"❌ Network error: {e}")
                continue
            except ET.ParseError as e:
                print(f"❌ XML parsing error: {e}")
                print(f"Response content: {response.text[:500]}...")
                continue
            
            batch_pmids = [id_elem.text for id_elem in root.findall('.//IdList/Id')]
            all_pmids.extend(batch_pmids)
            
            print(f"📄 Retrieved PMIDs {start+1}-{start+len(batch_pmids)} of {min(total_count, max_results)}")
            
            # Rate limiting
            time.sleep(0.1)
            
        print(f"✅ Retrieved {len(all_pmids)} PMIDs for pagination (out of {total_count} total papers found)")
        
        return translation, all_pmids, total_count
    
    def fetch_article_details(self, pmids: List[str], start_idx: int = 0, count: int = 50) -> List[Dict]:
        """
        Fetch detailed information for a subset of PMIDs
        
        Args:
            pmids (List[str]): List of all PMIDs
            start_idx (int): Starting index for this batch
            count (int): Number of articles to fetch
            
        Returns:
            List[Dict]: List of article dictionaries
        """
        if not pmids:
            return []
            
        # Get the subset of PMIDs for this batch
        end_idx = min(start_idx + count, len(pmids))
        batch_pmids = pmids[start_idx:end_idx]
        
        print(f"📖 Fetching details for articles {start_idx+1}-{end_idx}...")
        
        # Process in smaller batches to avoid API limits
        articles = []
        sub_batch_size = 20
        
        for i in range(0, len(batch_pmids), sub_batch_size):
            sub_batch = batch_pmids[i:i + sub_batch_size]
            sub_articles = self.fetch_batch_details(sub_batch)
            articles.extend(sub_articles)
            
            # Rate limiting
            time.sleep(0.1)
            
        return articles
    
    def fetch_batch_details(self, pmids: List[str]) -> List[Dict]:
        """
        Fetch details for a batch of PMIDs
        
        Args:
            pmids (List[str]): Batch of PMIDs
            
        Returns:
            List[Dict]: List of article details
        """
        if not pmids:
            return []
            
        params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml',
            'rettype': 'abstract'
        }
        # Only add email if it's a valid email format
        if self.email and '@' in self.email and '.' in self.email:
            params['email'] = self.email
            
        try:
            response = self.session.get(f"{self.base_url}/efetch.fcgi", params=params, timeout=30)
            response.raise_for_status()
            
            # Check if response is a maintenance page
            if self._is_maintenance_page(response.content):
                print("❌ NCBI E-utilities API is currently under maintenance or unavailable.")
                print("   Please try again later or visit https://eutils.ncbi.nlm.nih.gov/ for status updates.")
                return []
                
            # Check if response is valid XML
            if not self._is_valid_xml_response(response.content):
                print(f"❌ API returned non-XML response: {response.text[:200]}...")
                return []
                
            root = ET.fromstring(response.content)
            
            articles = []
            for article_elem in root.findall('.//PubmedArticle'):
                article = self.parse_article_xml(article_elem)
                if article:
                    articles.append(article)
                    
            return articles
            
        except Exception as e:
            print(f"❌ Error fetching batch details: {e}")
            return []
    
    def parse_article_xml(self, article_elem) -> Optional[Dict]:
        """
        Parse individual article XML element into structured dictionary
        
        Args:
            article_elem: XML element containing article data
            
        Returns:
            Optional[Dict]: Parsed article data or None if parsing fails
        """
        try:
            article_data = {}
            
            # Extract PMID
            pmid_elem = article_elem.find('.//PMID')
            article_data['PMID'] = pmid_elem.text if pmid_elem is not None else 'Unknown'
            
            # Extract title
            title_elem = article_elem.find('.//ArticleTitle')
            article_data['Title'] = title_elem.text if title_elem is not None else 'No title available'
            
            # Extract abstract
            abstract_texts = []
            for abstract_elem in article_elem.findall('.//AbstractText'):
                label = abstract_elem.get('Label', '')
                text = abstract_elem.text if abstract_elem.text else ''
                if label:
                    abstract_texts.append(f"{label}: {text}")
                else:
                    abstract_texts.append(text)
            
            article_data['Abstract'] = ' '.join(abstract_texts) if abstract_texts else 'No abstract available'
            
            # Extract authors
            authors = []
            for author_elem in article_elem.findall('.//Author'):
                lastname_elem = author_elem.find('LastName')
                forename_elem = author_elem.find('ForeName')
                
                if lastname_elem is not None:
                    lastname = lastname_elem.text
                    forename = forename_elem.text if forename_elem is not None else ''
                    authors.append(f"{forename} {lastname}".strip())
            
            article_data['Authors'] = ', '.join(authors) if authors else 'Authors not available'
            
            # Extract DOI
            doi_elem = article_elem.find('.//ELocationID[@EIdType="doi"]')
            article_data['DOI'] = doi_elem.text if doi_elem is not None else 'No DOI available'
            
            # Extract publication date
            pub_date_elem = article_elem.find('.//PubDate')
            if pub_date_elem is not None:
                year_elem = pub_date_elem.find('Year')
                month_elem = pub_date_elem.find('Month')
                day_elem = pub_date_elem.find('Day')
                
                year = year_elem.text if year_elem is not None else ''
                month = month_elem.text if month_elem is not None else ''
                day = day_elem.text if day_elem is not None else ''
                
                article_data['Publication_Date'] = f"{year}-{month}-{day}".strip('-')
                article_data['Year'] = year
            else:
                article_data['Publication_Date'] = 'Date not available'
                article_data['Year'] = 'Unknown'
            
            return article_data
            
        except Exception as e:
            print(f"❌ Error parsing article XML: {str(e)}")
            return None
    
    def display_results_table(self, articles: List[Dict]):
        """
        Display results in a formatted table
        
        Args:
            articles (List[Dict]): List of articles to display
        """
        if not articles:
            print("❌ No articles to display")
            return
            
        # Create DataFrame for better display
        df = pd.DataFrame(articles)
        
        # Reorder columns
        columns_order = ['PMID', 'Title', 'Authors', 'Year', 'DOI', 'Abstract']
        df = df.reindex(columns=columns_order)
        
        print(f"\n📋 Results Table ({len(articles)} articles):")
        print("="*120)
        
        # Display each article
        for idx, row in df.iterrows():
            print(f"\n{idx+1}. PMID: {row['PMID']}")
            print(f"   Title: {row['Title']}")
            print(f"   Authors: {row['Authors']}")
            print(f"   Year: {row['Year']}")
            print(f"   DOI: {row['DOI']}")
            print(f"   Abstract: {row['Abstract'][:300]}...")
            print("-" * 80)
    
    def run_paginated_search(self, user_question: str):
        """
        Run the complete paginated search workflow
        
        Args:
            user_question (str): User's research question
        """
        print("🚀 Enhanced PubMed Search with Pagination")
        print("="*60)
        
        # Step 1: Get query translation and all PMIDs
        translation, all_pmids, total_count = self.get_pubmed_query_translation(user_question)
        
        if total_count == 0:
            print("❌ No papers found for this query.")
            return
        
        # Step 2: Display first 50 results
        print(f"\n📄 Displaying first 50 results (sorted by relevance):")
        first_50_articles = self.fetch_article_details(all_pmids, 0, 50)
        self.display_results_table(first_50_articles)
        
        # Step 3: Pagination for remaining results
        if total_count > 50:
            print(f"\n📄 Remaining results: {total_count - 50} articles")
            print("Use pagination to view more results.")
            
            current_start = 50
            page_size = 50
            
            while True:
                print(f"\nNavigation options:")
                print(f"  [n] Next {page_size} results (currently showing 1-{current_start})")
                print(f"  [p] Previous {page_size} results")
                print(f"  [j] Jump to specific page")
                print(f"  [s] Save current results to CSV")
                print(f"  [q] Quit")
                
                choice = input("\nEnter choice: ").lower().strip()
                
                if choice == 'q':
                    break
                elif choice == 'n':
                    if current_start < total_count:
                        next_articles = self.fetch_article_details(all_pmids, current_start, page_size)
                        self.display_results_table(next_articles)
                        current_start += page_size
                    else:
                        print("❌ No more results to show.")
                elif choice == 'p':
                    if current_start > 50:
                        current_start = max(50, current_start - page_size)
                        prev_articles = self.fetch_article_details(all_pmids, current_start - page_size, page_size)
                        self.display_results_table(prev_articles)
                    else:
                        print("❌ Already at the beginning.")
                elif choice == 'j':
                    try:
                        page_num = int(input(f"Enter page number (1-{(total_count + page_size - 1) // page_size}): "))
                        if 1 <= page_num <= (total_count + page_size - 1) // page_size:
                            start_idx = (page_num - 1) * page_size
                            current_start = start_idx + page_size
                            jump_articles = self.fetch_article_details(all_pmids, start_idx, page_size)
                            self.display_results_table(jump_articles)
                        else:
                            print("❌ Invalid page number!")
                    except ValueError:
                        print("❌ Invalid input!")
                elif choice == 's':
                    filename = input("Enter filename (default: pubmed_results.csv): ").strip()
                    if not filename:
                        filename = "pubmed_results.csv"
                    
                    # Save all fetched results so far
                    all_fetched = self.fetch_article_details(all_pmids, 0, min(current_start, total_count))
                    df = pd.DataFrame(all_fetched)
                    df.to_csv(filename, index=False)
                    print(f"✅ Results saved to {filename}")
                else:
                    print("❌ Invalid choice!")


def main():
    """Main function to run the enhanced PubMed search"""
    print("🔬 Enhanced PubMed Search with Pagination")
    print("="*50)
    
    email = input("Enter your email (recommended for NCBI API access): ").strip()
    user_question = input("Enter your research question: ").strip()
    
    if not user_question:
        print("❌ Please enter a research question.")
        return
    
    searcher = EnhancedPubMedSearcher(email)
    searcher.run_paginated_search(user_question)


if __name__ == "__main__":
    main() 