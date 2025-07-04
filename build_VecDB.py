import chromadb
from chromadb.utils import embedding_functions
import json


def create_qa_database(qa_data, db_path="./chroma_db", collection_name="qa_collection", overwrite_existing=True):

    embedding_model_name = "shibing624/text2vec-base-chinese"
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=embedding_model_name
    )

    client = chromadb.PersistentClient(path=db_path)

    # --- 关键修改：如果选择覆盖，则先删除旧集合 ---
    if overwrite_existing:
        try:
            client.delete_collection(name=collection_name)
            print(f"已删除旧的集合 '{collection_name}'。")
        except:
            # 如果集合不存在，delete_collection会报错，这里捕获并忽略
            print(f"集合 '{collection_name}' 不存在，无需删除。")
            pass
    # --- 关键修改结束 ---

    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=sentence_transformer_ef,
        metadata={"hnsw:space": "cosine"}
    )

    documents = []
    metadatas = []
    ids = []

    for i in range(0, len(qa_data), 2):
        if i + 1 < len(qa_data) and qa_data[i]["role"] == "user" and qa_data[i + 1]["role"] == "灯":
            user_question = qa_data[i]["content"]
            tomori_answer = qa_data[i + 1]["content"]
            formatted_qa = f"问题：{user_question}\n答：{tomori_answer}"

            documents.append(formatted_qa)
            metadatas.append({"type": "character_setting_qa", "character": "高松灯"})
            ids.append(f"qa_{i // 2}")
        else:
            print(f"警告: 跳过不符合预期的QA对在索引 {i}: {qa_data[i]}")

    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"成功将 {len(documents)} 条QA数据添加到 ChromaDB 集合 '{collection_name}' 中。")
    else:
        print("没有找到有效的QA数据可以添加到数据库。请检查输入格式。")

    print(f"当前集合 '{collection_name}' 中的文档数量: {collection.count()}")



if __name__ == "__main__":
    with open('data/rag_data.json','r',encoding='utf-8') as f:
        my_qa_data = json.load(f)


    create_qa_database(my_qa_data, overwrite_existing=True)


    print("\n--- 进行一个简单的查询 ---")
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(
        name="qa_collection")

    query_text = "你喜欢去天文馆吗"
    results = collection.query(
        query_texts=[query_text],
        n_results=2
    )

    print(f"查询 '{query_text}' 的结果:")
    for doc in results['documents'][0]:
        print(f"- {doc}")

    query_text_2 = "千早爱音负责什么"
    results_2 = collection.query(
        query_texts=[query_text_2],
        n_results=2
    )
    print(f"\n查询 '{query_text_2}' 的结果:")
    for doc in results_2['documents'][0]:
        print(f"- {doc}")