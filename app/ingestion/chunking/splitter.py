from typing import List
import logfire

def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
    # simple semantic chunker that splits by paras. Ensures chunks don't exceed
    # the specified size
    # Chunking is used to break large documents into smaller pieces before embedding
    # and storing them in your vector database.
    # overlap: Number of characters carried from the previous chunk into the next chunk.

    with logfire.span(
            "Text Chunking",
            text_length=len(text),
            chunk_size=chunk_size,
            overlap=overlap
    ):
        if not text.strip():
            return []

        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        paragraphs = text.split("\n\n") #para separator
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()

            if not para: continue

            if len(current_chunk) + len(para)+2 <= chunk_size:
                # we can then append the current para to the current chunk
                current_chunk += para+"\n\n"
            else:
                # make a new chunk
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())

                #take the overlap from the end of prev chunk
                previous_overlap = current_chunk.strip()[-overlap:]

                current_chunk = previous_overlap + "\n\n" + para + "\n\n" #start a new chunk
        # add the final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        valid_chunks = [chunk for chunk in chunks if chunk.strip()]
        logfire.info(
            f"Generated {len(valid_chunks)} chunks "
            f"with {overlap} character overlap"
        )
        return valid_chunks