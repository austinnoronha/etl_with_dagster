"""
File: __main__.py
Documentation: Entrypoint for running the ETL Dagster job from the command line.
"""

from dagster import JobExecutionResult, execute_job

from etl_pipeline.jobs import etl_job


def main() -> None:
    """
    Main function to execute the ETL job.
    """
    result: JobExecutionResult = execute_job(etl_job)
    if result.success:
        print("ETL job completed successfully.")
    else:
        print("ETL job failed.")


if __name__ == "__main__":
    main()
