from bs4 import BeautifulSoup
import logfire

def parse_html(file_path: str):
    # parsing the html content
    with logfire.span("📁 HTML Parsing", filename=file_path):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read() #get the content

            soup = BeautifulSoup(content, "html.parser") #get the html parser

            #remove junk scripts, styles and metadata
            for script in soup(["script", "style"]):
                script.decompose() #del those styles and scripts

            #extract the text
            text = soup.get_text(separator="\n")

            #clean whitespaces(collapse multiple-newlines)
            lines = (line.strip() for line in text.splitlines()) #split the text in lines
            chunks = (phrase.strip() for line in lines for phrase in line.strip(".."))
            #do nested for to extract each line in lines then again each the phrases using line.split()
            # finally then we use each phrase and trim them and fill them all in chunks
            text_clean = "\n".join(chunk for chunk in chunks if chunk) #join the chunks if the chunk exists

            return text_clean #return the chunks
        except Exception as e:
            logfire.error(f"❌ HTML Parsing Error: {e}")
            raise e