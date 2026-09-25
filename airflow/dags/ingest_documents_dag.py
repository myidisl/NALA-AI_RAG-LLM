# airflow/dags/ingest_documents_dag.py
# DAG Airflow untuk pipeline ingest knowledge base NALA: memindai folder dokumen,
# memecahnya menjadi chunk, membuat embedding, lalu meng-index-nya ke OpenSearch.
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


def run_ingest():
    """Callable task Airflow: jalankan ingest seluruh dokumen di folder knowledge base."""
    # Import di dalam fungsi (bukan di level modul) agar scheduler Airflow tetap bisa
    # mem-parsing file DAG ini dengan cepat walau dependency modul app/ belum terpasang.
    from app.ingest import ingest_documents

    # Path folder knowledge base di dalam container Airflow (lihat volume di docker-compose.yml).
    count = ingest_documents("/opt/airflow/knowledge-base")
    # Output print tercatat di log task Airflow.
    print(f"Ingest selesai: {count} dokumen ter-index.")


with DAG(
    dag_id="ingest_documents",
    description="Scan Nala/knowledge-base, chunk, embed, dan index ke OpenSearch",
    start_date=datetime(2026, 1, 1),
    schedule=None,  # tidak terjadwal otomatis; DAG hanya dijalankan manual (trigger dari UI/CLI)
    catchup=False,  # jangan jalankan ulang run yang terlewat sejak start_date
    tags=["nala", "rag"],  # label untuk memfilter DAG di UI Airflow
) as dag:
    # Satu-satunya task di DAG: memanggil run_ingest() sebagai fungsi Python.
    ingest_task = PythonOperator(
        task_id="ingest_documents",
        python_callable=run_ingest,
    )
