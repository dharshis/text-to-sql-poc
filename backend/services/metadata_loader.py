"""
Generic metadata loader for any dataset.

This module loads metadata markdown files from dataset-specific directories
and makes them available for retrieval and context augmentation.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
import re

logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent


class MetadataDocument:
    """Represents a single metadata document chunk."""
    
    def __init__(
        self,
        dataset_id: str,
        file_name: str,
        section: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        self.dataset_id = dataset_id
        self.file_name = file_name
        self.section = section
        self.content = content
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "dataset_id": self.dataset_id,
            "file_name": self.file_name,
            "section": self.section,
            "content": self.content,
            "metadata": self.metadata
        }
    
    def __repr__(self):
        return f"<MetadataDocument(dataset={self.dataset_id}, file={self.file_name}, section={self.section})>"


class MetadataLoader:
    """Loads and parses metadata markdown files for any dataset."""
    
    def __init__(self, dataset_id: str, metadata_root: Optional[Path] = None):
        """
        Initialize metadata loader for a specific dataset.
        
        Args:
            dataset_id: Dataset identifier (e.g., "em_market", "sales")
            metadata_root: Optional custom metadata directory root
        """
        self.dataset_id = dataset_id
        self.metadata_root = metadata_root or (PROJECT_ROOT / "metadata")
        self.dataset_metadata_dir = self.metadata_root / dataset_id
        self.documents: List[MetadataDocument] = []
        
        logger.info(f"Initialized MetadataLoader for dataset: {dataset_id}")
        logger.info(f"Metadata directory: {self.dataset_metadata_dir}")
    
    def load_all(self) -> List[MetadataDocument]:
        """
        Load all metadata files for the dataset.
        
        Returns:
            List of MetadataDocument objects
        """
        if not self.dataset_metadata_dir.exists():
            logger.warning(f"Metadata directory not found: {self.dataset_metadata_dir}")
            return []
        
        self.documents = []
        
        # Load all .md files in dataset directory
        md_files = list(self.dataset_metadata_dir.glob("*.md"))
        logger.info(f"Found {len(md_files)} metadata files for {self.dataset_id}")
        
        for md_file in md_files:
            try:
                docs = self._parse_markdown_file(md_file)
                self.documents.extend(docs)
                logger.debug(f"Loaded {len(docs)} sections from {md_file.name}")
            except Exception as e:
                logger.error(f"Error loading {md_file.name}: {e}")
        
        logger.info(f"Total metadata documents loaded: {len(self.documents)}")
        return self.documents
    
    def _parse_markdown_file(self, file_path: Path) -> List[MetadataDocument]:
        """
        Parse a markdown file into metadata documents.
        
        Strategy:
        - For business_rules.md and query_patterns.md: Split by ## RULE: or ### Pattern headings
        - For table schema files: Split by major sections (## heading)
        
        Args:
            file_path: Path to markdown file
            
        Returns:
            List of MetadataDocument objects
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_name = file_path.stem  # filename without extension
        
        # Determine parsing strategy based on file type
        if file_name == "business_rules":
            return self._parse_business_rules(file_name, content)
        elif file_name == "query_patterns":
            return self._parse_query_patterns(file_name, content)
        else:
            # Table schema files or other metadata
            return self._parse_table_schema(file_name, content)
    
    def _parse_business_rules(self, file_name: str, content: str) -> List[MetadataDocument]:
        """Parse business_rules.md into individual rule documents."""
        documents = []
        
        # Split by ## RULE: headings
        rule_pattern = r'##\s+RULE:\s+([^\n]+)'
        sections = re.split(rule_pattern, content)
        
        # First section is header/intro
        if sections[0].strip():
            documents.append(MetadataDocument(
                dataset_id=self.dataset_id,
                file_name=file_name,
                section="introduction",
                content=sections[0].strip(),
                metadata={"type": "introduction"}
            ))
        
        # Process rule sections (pattern produces [rule_title, rule_content, ...])
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                rule_title = sections[i].strip()
                rule_content = sections[i + 1].strip()
                
                # Create document for this rule
                documents.append(MetadataDocument(
                    dataset_id=self.dataset_id,
                    file_name=file_name,
                    section=f"rule_{rule_title.lower().replace(' ', '_')}",
                    content=f"# RULE: {rule_title}\n\n{rule_content}",
                    metadata={
                        "type": "business_rule",
                        "rule_title": rule_title
                    }
                ))
        
        logger.debug(f"Parsed {len(documents)} business rules")
        return documents
    
    def _parse_query_patterns(self, file_name: str, content: str) -> List[MetadataDocument]:
        """Parse query_patterns.md into individual pattern documents."""
        documents = []
        
        # Split by ### Pattern headings or ## category headings
        pattern_regex = r'###\s+([^\n]+)'
        sections = re.split(pattern_regex, content)
        
        # First section is header
        if sections[0].strip():
            documents.append(MetadataDocument(
                dataset_id=self.dataset_id,
                file_name=file_name,
                section="introduction",
                content=sections[0].strip(),
                metadata={"type": "introduction"}
            ))
        
        # Process pattern sections
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                pattern_title = sections[i].strip()
                pattern_content = sections[i + 1].strip()
                
                documents.append(MetadataDocument(
                    dataset_id=self.dataset_id,
                    file_name=file_name,
                    section=f"pattern_{pattern_title.lower().replace(' ', '_')}",
                    content=f"### {pattern_title}\n\n{pattern_content}",
                    metadata={
                        "type": "query_pattern",
                        "pattern_title": pattern_title
                    }
                ))
        
        logger.debug(f"Parsed {len(documents)} query patterns")
        return documents
    
    def _parse_table_schema(self, file_name: str, content: str) -> List[MetadataDocument]:
        """Parse table schema or other metadata files by major sections."""
        documents = []
        
        # Split by ## headings (major sections)
        section_pattern = r'##\s+([^\n]+)'
        sections = re.split(section_pattern, content)
        
        # Handle the content before first ## (usually title and description)
        if sections[0].strip():
            # Extract table name from first # heading if present
            title_match = re.match(r'#\s+([^\n]+)', sections[0])
            table_name = title_match.group(1).strip() if title_match else file_name
            
            documents.append(MetadataDocument(
                dataset_id=self.dataset_id,
                file_name=file_name,
                section="overview",
                content=sections[0].strip(),
                metadata={
                    "type": "table_metadata",
                    "table_name": table_name
                }
            ))
        
        # Process remaining sections
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                section_title = sections[i].strip()
                section_content = sections[i + 1].strip()
                
                documents.append(MetadataDocument(
                    dataset_id=self.dataset_id,
                    file_name=file_name,
                    section=section_title.lower().replace(' ', '_'),
                    content=f"## {section_title}\n\n{section_content}",
                    metadata={
                        "type": "table_metadata",
                        "section_title": section_title
                    }
                ))
        
        logger.debug(f"Parsed {len(documents)} sections from {file_name}")
        return documents
    
    def get_documents_by_type(self, doc_type: str) -> List[MetadataDocument]:
        """
        Filter documents by type.
        
        Args:
            doc_type: Document type (business_rule, query_pattern, table_metadata)
            
        Returns:
            Filtered list of documents
        """
        return [doc for doc in self.documents if doc.metadata.get("type") == doc_type]
    
    def get_documents_by_file(self, file_name: str) -> List[MetadataDocument]:
        """
        Get all documents from a specific file.
        
        Args:
            file_name: Name of the file (without extension)
            
        Returns:
            Documents from that file
        """
        return [doc for doc in self.documents if doc.file_name == file_name]
    
    def search_content(self, keyword: str) -> List[MetadataDocument]:
        """
        Simple keyword search across all content.
        
        Args:
            keyword: Search term (case-insensitive)
            
        Returns:
            Documents containing the keyword
        """
        keyword_lower = keyword.lower()
        return [
            doc for doc in self.documents 
            if keyword_lower in doc.content.lower()
        ]
    
    def get_statistics(self) -> Dict:
        """Get statistics about loaded metadata."""
        return {
            "dataset_id": self.dataset_id,
            "total_documents": len(self.documents),
            "by_type": {
                "business_rules": len(self.get_documents_by_type("business_rule")),
                "query_patterns": len(self.get_documents_by_type("query_pattern")),
                "table_metadata": len(self.get_documents_by_type("table_metadata")),
            },
            "unique_files": len(set(doc.file_name for doc in self.documents)),
            "metadata_directory": str(self.dataset_metadata_dir)
        }


def load_dataset_metadata(dataset_id: str) -> MetadataLoader:
    """
    Convenience function to load metadata for a dataset.
    
    Args:
        dataset_id: Dataset identifier
        
    Returns:
        MetadataLoader with loaded documents
    """
    loader = MetadataLoader(dataset_id)
    loader.load_all()
    return loader


# Example usage
if __name__ == "__main__":
    # Test with em_market dataset
    logging.basicConfig(level=logging.INFO)
    
    loader = load_dataset_metadata("em_market")
    stats = loader.get_statistics()
    
    print("\n=== Metadata Statistics ===")
    print(f"Dataset: {stats['dataset_id']}")
    print(f"Total Documents: {stats['total_documents']}")
    print(f"\nBy Type:")
    for doc_type, count in stats['by_type'].items():
        print(f"  {doc_type}: {count}")
    print(f"\nUnique Files: {stats['unique_files']}")
    
    print("\n=== Sample Business Rules ===")
    rules = loader.get_documents_by_type("business_rule")
    for rule in rules[:3]:
        print(f"\n- {rule.metadata.get('rule_title')}")
        print(f"  Section: {rule.section}")
        print(f"  Content length: {len(rule.content)} characters")
    
    print("\n=== Search Test ===")
    results = loader.search_content("market value")
    print(f"Found {len(results)} documents containing 'market value'")

