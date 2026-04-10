from pinecone import Pinecone

pc = Pinecone(api_key="pcsk_4WuhvG_FP9s65sYJUjHcEkbvfTRi3W17YWvA6FxoPPr7kzWUSYKR3ZbHVbZdMmCtCMmQcs")
#index = pc.Index("quickstart")

index = pc.Index(
    host="solartis-rag-12zv9nc.svc.aped-4627-b74a.pinecone.io"
)