# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess

from openrelik_worker_common.file_utils import create_output_file
from openrelik_worker_common.task_utils import create_task_result, get_input_files

from .app import celery

# Task name used to register and route the task to the correct queue.
TASK_NAME = "openrelik-worker-unzip.tasks.unzip"

# Task metadata for registration in the core system.
TASK_METADATA = {
    "display_name": "Unzip",
    "description": "Extract files from a Zip Archive",
    # Configuration that will be rendered as a web for in the UI, and any data entered
    # by the user will be available to the task function when executing (task_config).
    "task_config": [
        {
            "name": "Zip Extraction",
            "label": "Zippy",
            "description": "Extract files from Zip Archives",
        },
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
    base_command = ["unzip"]
    base_command_string = " ".join(base_command)

    for input_file in input_files:
        zip_path = input_file.get("path")
        if not zip_path or not zip_path.lower().endswith(".zip"):
            raise RuntimeError(f"Invalid input file: {zip_path}")
        
        # Construct command
        command = base_command + [zip_path, "-d", output_path]
        
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Unzip failed for {zip_path}: {e.stderr.decode().strip()}")

    # Collect all extracted files
    for root, _, files in os.walk(output_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            output_files.append(
                create_output_file(
                    output_path, display_name=file_name, extension=file_name.split(".")[-1], data_type="extracted"
                ).to_dict()
            )
    if not output_files:
        raise RuntimeError("No files were extracted from the archive.")

    return create_task_result(
        output_files=output_files,
        workflow_id=workflow_id,
        command=base_command_string,
        meta={},
    )
