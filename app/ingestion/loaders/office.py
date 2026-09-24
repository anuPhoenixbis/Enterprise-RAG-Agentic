import logfire
from unstructured.partition.auto import partition

def parse_office(file_path: str):
    #parses .docx and .pptx files using unstructured lib
    with logfire.span(" 📁 Office Document Parsing", file_path):
        try:
            # automatically detects if its .docx or .pptx
            elements = partition(file_path) #partition the doc into its elems
            full_text = "\n".join([str(elem) for elem in elements])

            if not full_text.strip():#not text to extract
                logfire.warning(f"⚠️ Unstructured returned empty text for {file_path}")
            else:
                logfire.info(f"✅ Successfully parsed {len(full_text)} characters")

            return full_text
        except Exception as e:
            logfire.error(f"❌ Office Parse Failed: {e}")
            raise e