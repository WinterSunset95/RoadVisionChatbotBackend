import re
from typing import List, Dict, Tuple
import os
import traceback
import time
from pathlib import Path

from llama_parse import LlamaParse, ResultType
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import pdfplumber

from app.config import settings
from app.core.global_stores import upload_jobs
from app.modules.askai.models.document import ProcessingStage

class PDFProcessor:
    """Enhanced PDF processing with LlamaParse OCR"""

    job_id = None
    
    def __init__(self, embedding_model, tokenizer):
        self.embedding_model = embedding_model
        self.tokenizer = tokenizer
        
        llama_key = settings.LLAMA_CLOUD_API_KEY
        if llama_key:
            self.llama_parser = LlamaParse(
                api_key=llama_key,
                result_type=ResultType.MD,
                parsing_instruction="Extract all text, tables, and structure.",
                num_workers=2,
                verbose=False,
                max_timeout=600,
            )
            self.has_llamaparse = True
            print("✅ LlamaParse OCR initialized")
        else:
            self.has_llamaparse = False
            print("⚠️  LlamaParse not available")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\'\/\@\#\$\%\&\*\+\=]', ' ', text)
        return text.strip()
    
    def _clean_metadata(self, metadata: Dict) -> Dict:
        """Clean metadata for ChromaDB compatibility"""
        cleaned = {}
        for k, v in metadata.items():
            str_val = str(v)
            str_val = re.sub(r'[^\w\s\-\.\,\/]', '_', str_val)
            str_val = str_val.strip()
            cleaned[k] = str_val if str_val else "unknown"
        return cleaned
    
    def update_progress(self, stage: ProcessingStage, progress: float) -> None:
        print(f"📄 Progress: {stage} {progress}%")
        if not self.job_id:
            return
        upload_jobs[self.job_id].stage = stage
        upload_jobs[self.job_id].progress = progress

    def create_smart_chunks(self, text: str, curr_page_no: int, no_of_pages: int, metadata: Dict) -> List[Dict]:
        """Create overlapping chunks with metadata"""
        words = text.split()
        chunks = []

        no_of_words = len(words)
        
        if len(words) <= settings.CHUNK_SIZE:
            return [{
                "content": text,
                "metadata": self._clean_metadata(metadata),
                "word_count": len(words)
            }]
        
        chunk_index = 0
        start = 0
        
        while start < len(words):
            progress_from_previous_pages = (curr_page_no-1)/no_of_pages
            progress_on_current_page = (start/no_of_words) * (1/no_of_pages)
            self.update_progress(ProcessingStage.CREATING_CHUNKS, (progress_from_previous_pages + progress_on_current_page) * 100)
            end = min(start + settings.CHUNK_SIZE, len(words))
            chunk_words = words[start:end]
            chunk_text = ' '.join(chunk_words)
            
            chunk_meta = metadata.copy()
            chunk_meta["chunk_index"] = chunk_index
            
            chunks.append({
                "content": chunk_text,
                "metadata": self._clean_metadata(chunk_meta),
                "word_count": len(chunk_words)
            })
            
            chunk_index += 1
            start = end - settings.CHUNK_OVERLAP
            
            if start >= len(words) - settings.CHUNK_OVERLAP:
                break
        
        return chunks
    
    def extract_with_llamaparse(self, pdf_path: str) -> Dict[int, str]:
        """Primary extraction using LlamaParse"""
        if not self.has_llamaparse:
            return {}
        
        try:
            print(f"🔍 LlamaParse processing for {Path(pdf_path).name}...")
            self.update_progress(ProcessingStage.LLAMA_LOADING, 0)
            documents = self.llama_parser.load_data(pdf_path)
            
            page_texts = {}
            no_of_pages = len(documents)
            for doc in documents:
                self.update_progress(ProcessingStage.EXTRACTING_CONTENT, (documents.index(doc)/no_of_pages)*100)
                page_num_str = doc.metadata.get('page_label', doc.metadata.get('page', '1'))
                
                try:
                    page_num = int(float(page_num_str))
                except (ValueError, TypeError, AttributeError):
                    page_num = 1
                
                if page_num not in page_texts:
                    page_texts[page_num] = []
                
                page_texts[page_num].append(doc.text)
            
            result = {p: self.clean_text("\n\n".join(texts)) 
                    for p, texts in page_texts.items()}
            
            print(f"✅ LlamaParse extracted {len(result)} pages.")
            return result
            
        except Exception as e:
            print(f"❌ LlamaParse FATAL error on {Path(pdf_path).name}: {e}")
            traceback.print_exc()
            return {}
    
    def extract_with_pymupdf(self, pdf_path: str) -> Dict[int, str]:
        """Fallback extraction using PyMuPDF"""
        page_texts = {}
        try:
            self.update_progress(ProcessingStage.PYMUPDF_LOADING, 0)
            doc = fitz.open(pdf_path)
            no_of_pages = doc.page_count
            for page_num in range(doc.page_count):
                self.update_progress(ProcessingStage.EXTRACTING_CONTENT, (page_num/no_of_pages)*100)
                page = doc[page_num]
                text = page.get_text()
                if text and text.strip():
                    page_texts[page_num + 1] = self.clean_text(text)
            doc.close()
            print(f"✅ PyMuPDF extracted {len(page_texts)} pages")
        except Exception as e:
            print(f"❌ PyMuPDF error: {e}")
        return page_texts
    
    def extract_with_tesseract(self, pdf_path: str) -> Dict[int, str]:
        """Final fallback OCR using Tesseract for purely scanned documents."""
        page_texts = {}
        try:
            print(f"🔎 Tesseract OCR processing...")
            self.update_progress(ProcessingStage.TESSERACT_LOADING, 0)
            doc = fitz.open(pdf_path)
            no_of_pages = doc.page_count
            for i, page in enumerate(doc):
                self.update_progress(ProcessingStage.EXTRACTING_CONTENT, (i/no_of_pages)*100)
                pix = page.get_pixmap(dpi=200) 
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(img)
                if text and text.strip():
                    page_texts[i + 1] = self.clean_text(text)
            print(f"✅ Tesseract OCR extracted {len(page_texts)} pages.")
        except Exception as e:
            print(f"❌ Tesseract OCR error: {e}")
            traceback.print_exc()
        return page_texts
    
    def extract_tables(self, pdf_path: str) -> List[Dict]:
        """Extract tables using pdfplumber"""
        tables = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_tables = page.extract_tables() or []
                    
                    no_of_tables = len(page_tables)
                    for table_idx, table in enumerate(page_tables):
                        progress_from_previous_pages = (page_num-1)/total_pages
                        progress_on_current_page = ((table_idx+1)/no_of_tables) * (1/total_pages)
                        total_progress = progress_from_previous_pages + progress_on_current_page
                        self.update_progress(ProcessingStage.EXTRACTING_TABLES, total_progress*100)
                        if len(table) < 2: continue
                        headers = table[0] if table[0] else []
                        table_text = f"Table {table_idx + 1} on page {page_num}:\n"
                        if headers:
                            table_text += "Headers: " + " | ".join(str(h) for h in headers if h) + "\n"
                        for row in table[1:]:
                            if not any(row): continue
                            row_text = " | ".join(str(cell) if cell else "" for cell in row)
                            table_text += row_text + "\n"
                        tables.append({
                            "content": self.clean_text(table_text),
                            "page": page_num,
                            "type": "table", "table_index": table_idx
                        })
            print(f"✅ Extracted {len(tables)} tables")
        except Exception as e:
            print(f"⚠️  Table extraction error: {e}")
        return tables
    
    def process_pdf(self, job_id: str, pdf_path: str, doc_id: str, filename: str) -> Tuple[List[Dict], Dict]:
        """Main PDF processing pipeline"""
        self.job_id = job_id
        print(f"\n{'='*60}\n📄 Processing PDF: {filename}\n{'='*60}")
        start_time = time.time()
        
        page_texts = self.extract_with_llamaparse(pdf_path)
        if not page_texts:
            print("⚠️  LlamaParse failed, attempting PyMuPDF fallback...")
            page_texts = self.extract_with_pymupdf(pdf_path)
        if not page_texts:
            print("⚠️  PyMuPDF also failed, attempting Tesseract OCR fallback...")
            page_texts = self.extract_with_tesseract(pdf_path)
        if not page_texts:
            raise Exception("Failed to extract any text from PDF")
        
        tables = self.extract_tables(pdf_path)
        
        all_chunks = []
        no_of_pages = len(page_texts)
        for page_num, text in page_texts.items():
            # print(f"📄 Processing page {page_num} of {no_of_pages}")
            if not text.strip(): continue
            base_metadata = {"doc_id": str(doc_id), "source": str(filename), "page": str(page_num), "type": "text", "doc_type": "pdf"}
            chunks = self.create_smart_chunks(text, page_num, no_of_pages, base_metadata)
            all_chunks.extend(chunks)
        
        for table in tables:
            table_meta = {"doc_id": str(doc_id), "source": str(filename), "page": str(table["page"]), "type": "table", "doc_type": "pdf", "table_index": str(table.get("table_index", 0))}
            all_chunks.append({"content": table["content"], "metadata": self._clean_metadata(table_meta), "word_count": len(table["content"].split())})
        
        if len(all_chunks) > settings.MAX_CHUNKS_PER_DOCUMENT:
            print(f"⚠️  Limiting to {settings.MAX_CHUNKS_PER_DOCUMENT} chunks")
            all_chunks = all_chunks[:settings.MAX_CHUNKS_PER_DOCUMENT]
        
        stats = {"total_chunks": len(all_chunks), "pages": len(page_texts), "tables": len(tables), "processing_time": time.time() - start_time}
        print(f"✅ Created {stats['total_chunks']} chunks from {stats['pages']} pages")
        print(f"⏱️  Processing time: {stats['processing_time']:.2f}s\n")
        
        return all_chunks, stats

class ExcelProcessor:
    """Placeholder for Excel processing logic"""
    def __init__(self, embedding_model, tokenizer):
        pass
        
    def process_excel(self, excel_path: str, doc_id: str, filename: str) -> Tuple[List[Dict], Dict]:
        """Returns dummy data for now"""
        print(f"⚠️  Excel processing is not yet fully implemented for {filename}. Returning dummy data.")
        time.sleep(1)
        chunks = [{"content": f"Dummy chunk for Excel file {filename}", "metadata": {"doc_id": doc_id, "source": filename, "doc_type": "excel"}, "word_count": 10}]
        stats = {"total_chunks": 1, "sheets": 1, "processing_time": 1.0}
        return chunks, stats
