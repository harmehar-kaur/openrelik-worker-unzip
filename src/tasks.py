import os
import subprocess
import time
import shutil

from pathlib import Path
from uuid import uuid4

from openrelik_worker_common.file_utils import create_output_file
from openrelik_worker_common.task_utils import create_task_result, get_input_files

from .app import celery

TASK_NAME = "openrelik-worker-unzip.tasks.unzip"

TASK_METADATA = {
    "display_name": "Unzip",
    "description": "Extract files from a Zip Archive",
    "task_config": [
    ],
}

@celery.task(bind=True, name=TASK_NAME, metadata=TASK_METADATA)
def command(
    self,
    pipe_result: str = None,
    input_files: list = None,
    output_path: str = None,
    workflow_id: str = None,
    task_config: dict = None,
) -> str:
    """Run unzip on input files.

    Args:
        pipe_result: Base64-encoded result from the previous Celery task, if any.
        input_files: List of input file dictionaries (unused if pipe_result exists).
        output_path: Path to the output directory.
        workflow_id: ID of the workflow.
        task_config: User configuration for the task.

    Returns:
        Base64-encoded dictionary containing task results.
    """
    input_files = get_input_files(pipe_result, input_files or [])
    output_files = []

    for input_file in input_files:
        input_file_display_name = input_file.get("display_name")
        log_file = create_output_file(
            output_path,
            display_name=f"{input_file_display_name}-7z.log",
        )

        extract_directory = os.path.join(output_path, uuid4().hex)
        os.mkdir(extract_directory)

        command = [
            "/forensics/7zz", "x",
            input_file.get("path"),
            f"-o{extract_directory}",
            "-y"
        ]
        command_string = " ".join(command[:5])

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while process.poll() is None:
            self.send_event("task-progress")
            time.sleep(1)

    if os.path.isfile(log_file.path) and os.stat(log_file.path).st_size > 0:
        output_files.append(log_file.to_dict())

    extract_directory_path = Path(extract_directory)
    extracted_files = [f for f in extract_directory_path.glob("**/*") if f.is_file()]
    for file in extracted_files:
        relative_path = file.relative_to(extract_directory_path)  # Keep folder structure
        destination_path = os.path.join(output_path, relative_path)

        os.makedirs(os.path.dirname(destination_path), exist_ok=True)  # Ensure parent dirs exist
        shutil.move(file, destination_path)  # Move extracted file to correct structure

    output_file = create_output_file(
        output_path,
        display_name=file.name,
        original_path=str(relative_path),
        data_type="worker:openrelik:extraction:unzip",
        source_file_id=input_file.get("id"),
    )

    output_files.append(output_file.to_dict())
    if not output_files:
        raise RuntimeError("7zip didn't create any output files")

    return create_task_result(
        output_files=output_files,
        workflow_id=workflow_id,
        command=command_string,
    )
