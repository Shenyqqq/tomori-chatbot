import chromadb

client = chromadb.PersistentClient("./chroma_db")
collection = client.get_collection("qa_collection")  # 已有embedding
RAG_SIMILARITY_THRESHOLD = 0.4
def get_rag_context(query: str, top_k: int = 3) -> str:
    if not query:
        return ""
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "distances"]  # 确保返回文档内容和它们与查询的距离
        # 如果返回的是距离，通常值越小越相似，需要转换为相似度
    )
    docs_to_inject = []
    if results and results["documents"] and results["documents"][0]:
        # 遍历检索到的文档及其对应的距离/相似度
        for i in range(len(results["documents"][0])):
            doc_content = results["documents"][0][i]
            distance = results["distances"][0][i]
            print("Distance：",distance)
            if distance <= RAG_SIMILARITY_THRESHOLD:
                docs_to_inject.append(doc_content)

    if docs_to_inject:
        return "\n###\n".join(docs_to_inject)
    else:
        return ""